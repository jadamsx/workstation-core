#!/usr/bin/env python3
"""Block the main thread from editing files or running tests, builds, linters and formatters.

The coordinator (lead or plain main thread) coordinates; subagents do the work. Subagent tool calls
carry `agent_id` in the hook payload, the main thread's do not. A manager tab, recognised by a
non-empty WORKSTATION_REPORTS, may edit and run tests directly. Putting `main-thread-ok` in a prompt lifts the
edit gate for the main thread this turn: the UserPromptSubmit wiring records it per session,
PreToolUse reads it. It is not a way to brief agents. Long or open-ended jobs go to a typed
agent with one bounded task, never a general-purpose agent carrying a whole job.

Every role: a Bash polling loop (`until`/`while` with `sleep`) or a `sleep` over 10 seconds is denied in favour
of run_in_background, and a run_in_background command is rewritten to run under a 20-minute timeout.

With WORKSTATION_ROLE=ask the gate is an allowlist: no file edits, only read-only agent types, and Bash
runs only listed read-only commands, tokenised and normalised before matching. It applies to subagents too and whatever the prompt says.

Exit 0 = allow, exit 2 = block (stderr goes back to Claude).
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import sys
from pathlib import Path

ESCAPE_PHRASE = "main-thread-ok"
WORKER_REPORT = re.compile(r"^\s*\[worker-report\]", re.MULTILINE)
EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
MAX_SLEEP_SECONDS = 10
BACKGROUND_TIMEOUT_SECONDS = 1200
SLEEP_ARG = re.compile(r"\bsleep\s+(\d+(?:\.\d+)?)([smhd]?)\b")
LOOP_WORD = re.compile(r"\b(until|while)\b")
SLEEP_WORD = re.compile(r"\bsleep\b")
SLEEP_UNITS = {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}
WRAPPED = re.compile(rf"^\s*(gtimeout|timeout)\s+{BACKGROUND_TIMEOUT_SECONDS}\b|^\s*perl -e 'alarm {BACKGROUND_TIMEOUT_SECONDS};")
POLLING_DENIED = "Do not poll or sleep for more than 10 seconds. Use run_in_background, which notifies when the command finishes."
EDIT_EXEMPT_DIRS = ("/.claude/plans/", "/.claude/projects/")


def coordination_dirs() -> tuple[str, str]:
    notes = os.path.expanduser(os.environ.get("NOTES_DIR") or "~/notes")
    drafts = os.path.expanduser(os.environ.get("DRAFTS_DIR") or "~/drafts")
    return (drafts, notes)


TOOL_HEADS = {
    "pytest",
    "py.test",
    "tox",
    "nox",
    "tsc",
    "mypy",
    "pyright",
    "ruff",
    "black",
    "isort",
    "flake8",
    "pylint",
    "eslint",
    "prettier",
    "biome",
    "vitest",
    "jest",
    "playwright",
}
PYTHON_MODULES = {
    "pytest",
    "unittest",
    "mypy",
    "ruff",
    "black",
    "isort",
    "flake8",
    "pylint",
}
PACKAGE_MANAGERS = {"npm", "pnpm", "yarn", "bun"}
SCRIPT_NAMES = re.compile(
    r"^(test|build|lint|format|fmt|typecheck|type-check|check|tsc)(:\S+)?$"
)
MAKE_TARGETS = re.compile(r"^(test|tests|build|lint|check|fmt|format|typecheck)\S*$")
SUBCOMMANDS = {
    "go": {"test", "build", "vet"},
    "cargo": {"test", "build", "check", "clippy", "fmt"},
    "pre-commit": {"run"},
}
WRAPPERS = {"time", "env", "nice", "exec", "command", "npx", "bunx", "pnpx"}
WRAPPER_ARG_FLAGS = {
    "--with",
    "--project",
    "--directory",
    "-p",
    "--python",
    "--package",
    "-w",
    "--prefix",
}

EDIT_AGENTS = "builder (scope node for several files, one-file for 1-2 files)"
TEST_AGENTS = "run-digest (run and digest) or claim-prover (prove a claim)"

QUOTED = re.compile(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"")
HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?.*?\n\1\b", re.DOTALL)
SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|\n]")
ENV_ASSIGN = re.compile(r"^[A-Za-z_]\w*=")
ASK_REDIRECT = re.compile(r">{1,2}(?:&\d+(?![\w/.~-])|\s*/dev/null(?![\w/.]))")
ASK_READ_HEADS = {
    "ls", "cat", "head", "tail", "wc", "rg", "grep", "find", "cut", "tr", "basename",
    "dirname", "pwd", "echo", "printf", "date", "stat", "du", "jq", "diff", "cd",
}
ASK_FIND_WRITES = {"-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprint0", "-fprintf", "-fls"}
ASK_GIT_READS = {"status", "log", "diff", "show", "branch", "blame", "ls-files", "rev-parse", "describe"}
ASK_GIT_BRANCH_FLAGS = {"-a", "-r", "-v", "-vv", "--list", "--show-current", "--all", "--remotes"}
ASK_HOST_READS = {"view", "list", "status", "diff", "checks"}
ASK_API_WRITES = ("--method", "--request", "--field", "--raw-field", "--input")
ASK_API_SHORT_WRITES = re.compile(r"-[A-Za-z]*[XfF]")
ASK_HERDR_READS = {
    ("pane", "read"), ("pane", "list"), ("tab", "list"),
    ("workspace", "list"), ("workspace", "get"), ("agent", "list"),
}
ASK_AGENTS = {
    "code-locator",
    "researcher",
    "change-reader",
    "release-state-reader",
    "run-digest",
    "web-fetch",
    "Explore",
}
ASK_ALLOWED = (
    "Allowed in the ask tab: read-only agents (" + ", ".join(sorted(ASK_AGENTS)) + "), "
    "and Bash that runs only listed read-only commands (" + ", ".join(sorted(ASK_READ_HEADS)) + "; "
    "git " + ", ".join(sorted(ASK_GIT_READS)) + "; gh and glab reads; "
    "herdr " + ", ".join(" ".join(pair) for pair in sorted(ASK_HERDR_READS)) + "), joined by && || ; |, with no command substitution or `$` and no redirect except to /dev/null. "
    "No file edits, no SendMessage. Point the human to the lead tab."
)


def is_subagent(payload: dict) -> bool:
    return bool(payload.get("agent_id"))


def is_manager() -> bool:
    return bool(os.environ.get("WORKSTATION_REPORTS"))


def state_dir() -> Path:
    override = os.environ.get("MAIN_THREAD_GATE_STATE")
    return (
        Path(override)
        if override
        else Path.home() / ".claude" / "state" / "main-thread-ok"
    )


def flag_path(session_id: str) -> Path:
    return state_dir() / re.sub(r"[^\w.-]", "_", session_id or "unknown")


def record_prompt(payload: dict) -> None:
    flag = flag_path(payload.get("session_id", ""))
    prompt = payload.get("prompt") or ""
    if ESCAPE_PHRASE in prompt and not WORKER_REPORT.search(prompt):
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.touch()
    else:
        flag.unlink(missing_ok=True)


def escaped(payload: dict) -> bool:
    return flag_path(payload.get("session_id", "")).exists()


def command_head(segment: str) -> list[str]:
    try:
        tokens = shlex.split(segment)
    except ValueError:
        tokens = segment.split()
    while tokens:
        head = tokens[0]
        if ENV_ASSIGN.match(head) or head in WRAPPERS:
            tokens = tokens[1:]
        elif head == "uv" and len(tokens) > 1 and tokens[1] in {"run", "tool"}:
            tokens = tokens[2:]
            while tokens and tokens[0].startswith("-"):
                tokens = tokens[2:] if tokens[0] in WRAPPER_ARG_FLAGS else tokens[1:]
        elif (
            head in {"pnpm", "yarn", "bun", "npm"}
            and len(tokens) > 1
            and tokens[1] == "exec"
        ):
            tokens = tokens[2:]
        else:
            break
    return tokens


def runs_tooling(tokens: list[str]) -> bool:
    if not tokens:
        return False
    head, rest = Path(tokens[0]).name, tokens[1:]
    if head in TOOL_HEADS:
        return True
    if (
        head.startswith("python")
        and rest[:1] == ["-m"]
        and rest[1:2]
        and rest[1] in PYTHON_MODULES
    ):
        return True
    if head in PACKAGE_MANAGERS:
        script = rest[1:2] if rest[:1] == ["run"] else rest[:1]
        return bool(script) and bool(SCRIPT_NAMES.match(script[0]))
    if head == "make":
        return any(MAKE_TARGETS.match(arg) for arg in rest if not arg.startswith("-"))
    return bool(rest) and rest[0] in SUBCOMMANDS.get(head, ())


def blocked_command(command: str) -> bool:
    bare = QUOTED.sub('""', HEREDOC.sub("", command))
    return any(
        runs_tooling(command_head(seg.strip())) for seg in SEGMENT_SPLIT.split(bare)
    )


def ask_segments(command: str) -> list[list[str]] | None:
    """Split into commands of unquoted-word lists, or None for syntax the allowlist cannot judge."""
    if "$" in command or "`" in command or "\\\n" in command:
        return None
    segments: list[list[str]] = [[]]
    word, quote, live, i = "", "", False, 0
    while i < len(command):
        ch = command[i]
        if quote:
            if ch == quote:
                quote = ""
            elif quote == '"' and ch == "\\":
                i += 1
                word += command[i : i + 1]
            else:
                word += ch
        elif ch in "'\"":
            quote, live = ch, True
        elif ch == "\\":
            i += 1
            word += command[i : i + 1]
            live = True
        elif ch in "<(":
            return None
        elif ch == ">":
            if live and word.isdigit():
                word, live = "", False
            m = ASK_REDIRECT.match(command, i)
            if not m:
                return None
            i = m.end() - 1
        elif ch in ";|&\n" or ch.isspace():
            if live:
                segments[-1].append(word)
                word, live = "", False
            if not ch.isspace() or ch == "\n":
                segments.append([])
        else:
            word += ch
            live = True
        i += 1
    if quote:
        return None
    if live:
        segments[-1].append(word)
    return [seg for seg in segments if seg]


def ask_allows(tokens: list[str]) -> bool:
    head, rest = tokens[0], tokens[1:]
    if head in ASK_READ_HEADS:
        if head == "find":
            return not ASK_FIND_WRITES & set(rest)
        if head == "rg":
            return not any(t.startswith(("--pre", "--hostname-bin")) for t in rest)
        return True
    if head == "git":
        while rest[:1] == ["-C"]:
            rest = rest[2:]
        sub, args = (rest[:1] or [""])[0], rest[1:]
        if any(a.startswith(("--output", "--textconv", "--ext-diff", "--no-index")) for a in args):
            return False
        if sub in ("diff", "log", "show") and any(a.startswith(("/", "~")) or "../" in a for a in args):
            return False
        if sub == "branch":
            return set(args) <= ASK_GIT_BRANCH_FLAGS
        return sub in ASK_GIT_READS
    if head in ("gh", "glab"):
        if rest[:1] in (["auth"], ["config"]):
            return False
        if rest[:1] == ["api"]:
            return not any(t.startswith(ASK_API_WRITES) or ASK_API_SHORT_WRITES.match(t) for t in rest)
        return len(rest) > 1 and rest[1] in ASK_HOST_READS and not rest[0].startswith("-")
    if head == "herdr":
        return tuple(rest[:2]) in ASK_HERDR_READS
    return False


def ask_allows_command(command: str) -> bool:
    segments = ask_segments(command)
    return segments is not None and all(ask_allows(seg) for seg in segments)


def ask_block_reason(payload: dict) -> str | None:
    tool, tool_input = payload.get("tool_name", ""), payload.get("tool_input") or {}
    if tool in EDIT_TOOLS:
        return f"The ask tab never edits files. {ASK_ALLOWED}"
    if tool == "SendMessage":
        return f"The ask tab never messages other sessions. {ASK_ALLOWED}"
    if tool == "Agent" and (tool_input.get("subagent_type") or "") not in ASK_AGENTS:
        return f"The ask tab only spawns read-only agents. {ASK_ALLOWED}"
    if tool == "Bash" and not ask_allows_command(tool_input.get("command") or ""):
        return f"The ask tab runs only allowlisted read-only commands. {ASK_ALLOWED}"
    return None


def polling_reason(payload: dict) -> str | None:
    if payload.get("tool_name") != "Bash":
        return None
    command = (payload.get("tool_input") or {}).get("command") or ""
    bare = QUOTED.sub('""', HEREDOC.sub("", command))
    long_sleep = any(float(n) * SLEEP_UNITS[u] > MAX_SLEEP_SECONDS for n, u in SLEEP_ARG.findall(bare))
    loop = LOOP_WORD.search(bare) and SLEEP_WORD.search(bare)
    return POLLING_DENIED if long_sleep or loop else None


def with_timeout(payload: dict) -> dict | None:
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") or ""
    if payload.get("tool_name") != "Bash" or not tool_input.get("run_in_background") or WRAPPED.match(command):
        return None
    limit = BACKGROUND_TIMEOUT_SECONDS
    runner = f"gtimeout {limit}" if shutil.which("gtimeout") else f"perl -e 'alarm {limit}; exec @ARGV' --"
    return {**tool_input, "command": f"{runner} bash -c {shlex.quote(command)}"}


def is_coordination_file(path: str) -> bool:
    resolved = Path(os.path.realpath(path))
    if resolved.suffix != ".md":
        return False
    return any(part in f"{resolved}/" for part in EDIT_EXEMPT_DIRS) or any(
        resolved.is_relative_to(os.path.realpath(root)) for root in coordination_dirs()
    )


def block_reason(payload: dict) -> str | None:
    tool, tool_input = payload.get("tool_name", ""), payload.get("tool_input") or {}
    if tool in EDIT_TOOLS:
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        if is_coordination_file(path):
            return None
        return f"The main thread coordinates and does not edit files. Dispatch {EDIT_AGENTS}."
    if tool == "Bash" and blocked_command(tool_input.get("command", "")):
        return f"The main thread does not run tests, builds, linters or formatters. Dispatch {TEST_AGENTS}."
    return None


def main() -> None:
    fail = 2 if os.environ.get("WORKSTATION_ROLE") == "ask" else 0
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(fail)
    if not isinstance(payload, dict):
        sys.exit(fail)
    if payload.get("hook_event_name") == "UserPromptSubmit":
        record_prompt(payload)
        sys.exit(0)
    if os.environ.get("WORKSTATION_ROLE") == "ask":
        reason = ask_block_reason(payload)
        if reason:
            print(reason, file=sys.stderr)
            sys.exit(2)
    reason = polling_reason(payload)
    if reason:
        print(reason, file=sys.stderr)
        sys.exit(2)
    reason = None if is_subagent(payload) or is_manager() or escaped(payload) else block_reason(payload)
    if reason:
        print(
            f"{reason} `{ESCAPE_PHRASE}` in your prompt lifts the edit gate for the main thread this turn; "
            "it is not a way to brief agents. Long or open-ended jobs go to a typed agent "
            "with one bounded task, never a general-purpose agent carrying a whole job.",
            file=sys.stderr,
        )
        sys.exit(2)
    updated = with_timeout(payload)
    if updated:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "updatedInput": updated}}))
    sys.exit(0)


if __name__ == "__main__":
    main()
