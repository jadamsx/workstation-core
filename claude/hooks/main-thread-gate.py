#!/usr/bin/env python3
"""Block the main thread from editing files or running tests, builds, linters and formatters.

The main thread coordinates; subagents do the work. Subagent tool calls carry `agent_id` in
the hook payload, the main thread's do not. Putting `main-thread-ok` in a prompt lifts the
block for that turn: the UserPromptSubmit wiring records it per session, PreToolUse reads it.

Exit 0 = allow, exit 2 = block (stderr goes back to Claude).
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

ESCAPE_PHRASE = "main-thread-ok"
EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
EDIT_EXEMPT_DIRS = ("/.claude/plans/", "/.claude/projects/")


def coordination_dirs() -> tuple[str, ...]:
    notes = os.path.expanduser(os.environ.get("NOTES_DIR") or "~/notes")
    drafts = os.path.expanduser(os.environ.get("DRAFTS_DIR") or "~/drafts")
    return (drafts.rstrip("/") + "/", notes.rstrip("/") + "/")


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


def is_subagent(payload: dict) -> bool:
    return bool(payload.get("agent_id"))


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
    if ESCAPE_PHRASE in (payload.get("prompt") or ""):
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


def is_coordination_file(path: str) -> bool:
    if any(part in path for part in EDIT_EXEMPT_DIRS):
        return True
    return any(path.startswith(root) for root in coordination_dirs()) and path.endswith(
        ".md"
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
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    if not isinstance(payload, dict):
        sys.exit(0)
    if payload.get("hook_event_name") == "UserPromptSubmit":
        record_prompt(payload)
        sys.exit(0)
    if is_subagent(payload) or escaped(payload):
        sys.exit(0)
    reason = block_reason(payload)
    if reason:
        print(
            f"{reason} Add `{ESCAPE_PHRASE}` to your prompt to allow it this turn.",
            file=sys.stderr,
        )
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
