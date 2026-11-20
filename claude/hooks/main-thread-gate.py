"""Guard rail (not a sandbox) for the lead and work tabs (WORKSTATION_ROLE=lead|work).

Edit/Write is blocked except markdown under the drafts and notes folders. Bash is an allowlist per role:
each command segment must start with a listed command, and redirects and `tee` may only write under the
temp, drafts and notes folders. `free` is ungated; an unset role inside herdr (HERDR_PANE_ID) gets the lead
rules, outside herdr it is ungated. Subagent tool calls carry `agent_id` and are never gated. Putting
`main-thread-ok` in a prompt lifts the gate for the lead for that turn.

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
HANDOFF = {"lead": "the work tab", "work": "a builder agent"}
READS = {
    "herdr": None, "herdr-manager": None, "notes-lint": None, "md-pdf": None, "current-project": None,
    "cd": None, "ls": None, "cat": None, "head": None, "tail": None, "wc": None, "rg": None, "grep": None,
    "find": None, "date": None, "echo": None, "printf": None, "sleep": None, "jq": None, "awk": None,
    "sed": None, "tee": None, "gh": None, "glab": None,
}
GIT_READS = ("status", "log", "diff", "show", "fetch", "branch", "rev-parse", "ls-remote", "remote", "commit-tree", "worktree list")
ALLOW = {
    "lead": {**READS, "git": GIT_READS + ("push",)},
    "work": {**READS, "git": GIT_READS + ("worktree", "merge", "rebase", "cherry-pick", "checkout -b")},
}
CHANGE_READS = {"view", "list"}
CHANGE_WRITES = {("pr", "create"), ("pr", "edit"), ("mr", "create"), ("mr", "update")}
API_WRITE_FLAGS = {"-f", "-F", "--field", "--raw-field", "--input"}
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1([^\n]*)\n.*?\n\s*\2[ \t]*(?=\n|$)", re.S)
MARKER_WRITE = re.compile(r">\s*\"?(?:\$\([^)]*\)|[^\s\"]*)/verify-self-pass\"?")
ASSIGNMENT = re.compile(r"[A-Za-z_]\w*=")
SED_INPLACE = re.compile(r"-[a-zA-Z]*i|--in-place")


def coordination_dirs() -> tuple[str, ...]:
    notes = os.path.expanduser(os.environ.get("NOTES_DIR") or "~/notes")
    drafts = os.path.expanduser(os.environ.get("DRAFTS_DIR") or "~/drafts")
    extra = tuple(os.path.expanduser(d) for d in os.environ.get("WORKSTATION_EDIT_EXEMPT_DIRS", "").split(":") if d)
    return (drafts, notes, *extra)


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


def is_coordination_file(path: str) -> bool:
    resolved = Path(os.path.realpath(path))
    if resolved.suffix != ".md":
        return False
    return any(part in f"{resolved}/" for part in EDIT_EXEMPT_DIRS) or any(
        resolved.is_relative_to(os.path.realpath(root)) for root in coordination_dirs()
    )


def is_safe_target(target: str) -> bool:
    target = os.path.expandvars(os.path.expanduser(target))
    resolved = os.path.realpath(target)
    roots = (os.environ.get("TMPDIR") or "/tmp", "/tmp", *coordination_dirs())
    return resolved == "/dev/null" or any(resolved.startswith(os.path.realpath(r).rstrip("/") + "/") for r in roots)


def segments(command: str) -> tuple[list[list[str]], list[str]]:
    """Split into command segments plus redirect targets; quoted text stays inside one token."""
    lex = shlex.shlex(command.replace("\n", ";"), posix=True, punctuation_chars=True)
    lex.whitespace_split, lex.commenters = True, ""
    segs: list[list[str]] = [[]]
    targets: list[str] = []
    tokens = list(lex)
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        punct = bool(tok) and all(c in "();<>|&" for c in tok)
        if punct and ">" in tok:
            i += 1
            if i < len(tokens) and not (tok.endswith("&") and re.fullmatch(r"\d+|-", tokens[i])):
                targets.append(tokens[i])
        elif punct and "<" in tok:
            i += 1
        elif punct:
            segs.append([])
        else:
            segs[-1].append(tok)
        i += 1
    return [s for s in segs if s], targets


def command_allowed(role: str, words: list[str]) -> bool:
    while words and ASSIGNMENT.match(words[0]):
        words = words[1:]
    if not words:
        return True
    name, args = words[0], words[1:]
    allow = ALLOW[role]
    if name not in allow:
        return False
    if name == "git":
        if args[:1] == ["-C"]:
            args = args[2:]
        return any(" ".join(args[: len(p.split())]) == p for p in allow["git"])
    if name in ("gh", "glab"):
        if args[:1] == ["api"]:
            method = next((args[i + 1] for i, a in enumerate(args[:-1]) if a in ("-X", "--method")), "GET")
            return method.upper() == "GET" and not API_WRITE_FLAGS & set(args)
        return args[1:2] and args[1] in CHANGE_READS or tuple(args[:2]) in CHANGE_WRITES
    if name == "sed":
        return not any(SED_INPLACE.fullmatch(a) for a in args)
    if name == "tee":
        return all(is_safe_target(a) for a in args if not a.startswith("-"))
    return True


def bash_violation(command: str, role: str) -> str | None:
    command = HEREDOC.sub(r"\3", command)
    if role == "lead":
        command = MARKER_WRITE.sub("", command)
    try:
        segs, targets = segments(command)
    except ValueError:
        return "run a command that cannot be parsed"
    for words in segs:
        if not command_allowed(role, words):
            return "run `" + " ".join(words[:2]) + "`"
    if not all(is_safe_target(t) for t in targets):
        return "write outside the tmp, drafts and notes folders"
    return None


def block_reason(payload: dict, role: str) -> str | None:
    tool_input = payload.get("tool_input") or {}
    if payload.get("tool_name") == "Bash":
        label = bash_violation(tool_input.get("command") or "", role)
        return label and f"The {role} may not {label} from Bash. Hand it to {HANDOFF[role]}."
    if payload.get("tool_name") not in EDIT_TOOLS:
        return None
    if is_coordination_file(tool_input.get("file_path") or tool_input.get("notebook_path") or ""):
        return None
    return f"The {role} does not edit files. Hand the change to {HANDOFF[role]}."


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
    role = os.environ.get("WORKSTATION_ROLE", "")
    unset_in_herdr = not role and bool(os.environ.get("HERDR_PANE_ID"))
    if unset_in_herdr:
        role = "lead"
    if role not in HANDOFF or is_subagent(payload) or (role == "lead" and escaped(payload)):
        sys.exit(0)
    reason = block_reason(payload, role)
    if reason:
        if unset_in_herdr:
            reason += " WORKSTATION_ROLE is unset in herdr, so the lead rules apply; relaunch the tab with WORKSTATION_ROLE=lead, work or free."
        lift = f" `{ESCAPE_PHRASE}` in your prompt lifts this for the turn." if role == "lead" else ""
        print(reason + lift, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
