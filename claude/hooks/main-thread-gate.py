#!/usr/bin/env python3
"""Block the lead and work tabs (WORKSTATION_ROLE=lead|work) from editing files or mutating via Bash.

Subagent tool calls carry `agent_id` in the hook payload, the lead's own do not. Markdown notes
under the drafts and notes folders stay editable. Bash is a per-role allowlist (redirects only under tmp, drafts, notes); `free` is ungated;
an unset role in herdr gets the lead rules. Putting `main-thread-ok` in a prompt lifts the
gate for that turn: the UserPromptSubmit wiring records it per session, PreToolUse reads it.

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
READS = set("herdr herdr-manager notes-lint md-pdf current-project cd ls cat head tail wc rg grep find date echo printf sleep jq awk sed tee gh glab".split())
GIT = (*"status log diff show fetch branch rev-parse ls-remote remote commit-tree".split(), "worktree list")
GIT_ROLE = {"lead": ("push",), "work": ("worktree", "merge", "rebase", "cherry-pick", "checkout -b")}
CHANGE_READS = {("pr", "checks"), ("pr", "diff"), ("mr", "diff"), ("ci", "status"), ("ci", "trace"), ("ci", "view")}
CHANGE_WRITES = {(k, v) for k, vs in (("pr", "create edit merge comment review"), ("mr", "create update merge note approve")) for v in vs.split()}
API_WRITE_PATHS = ("discussions", "notes", "reactions", "resolve")
API_WRITE_FLAGS = {"-f", "-F", "--field", "--raw-field", "--input"}
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1([^\n]*)\n.*?\n\s*\2[ \t]*(?=\n|$)", re.S)
MARKER_WRITE = re.compile(r">\s*\"?(?:\$\([^)]*\)|[^\s\"]*)/verify-self-pass\"?")


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
    resolved = os.path.realpath(os.path.expandvars(os.path.expanduser(target)))
    roots = (os.environ.get("TMPDIR") or "/tmp", "/tmp", *coordination_dirs())
    return resolved == "/dev/null" or any(resolved.startswith(os.path.realpath(r).rstrip("/") + "/") for r in roots)


def segments(command: str) -> tuple[list[list[str]], list[str]]:
    lex = shlex.shlex(command.replace("\n", ";"), posix=True, punctuation_chars=True)
    lex.whitespace_split, lex.commenters = True, ""
    segs, targets, redirect = [[]], [], ""
    for tok in lex:
        if redirect:
            if ">" in redirect and not (redirect.endswith("&") and re.fullmatch(r"\d+|-", tok)):
                targets.append(tok)
            redirect = ""
        elif tok and set(tok) <= set("();<>|&"):
            redirect = tok if set(tok) & set("<>") else ""
            segs += [] if redirect else [[]]
        else:
            segs[-1].append(tok)
    return [s for s in segs if s], targets


def command_allowed(role: str, words: list[str]) -> bool:
    while words and re.match(r"[A-Za-z_]\w*=", words[0]):
        words = words[1:]
    name, args = (words[:1] or ["true"])[0], words[1:]
    if name == "git":
        rest = " ".join(args[2:] if args[:1] == ["-C"] else args) + " "
        return any(rest.startswith(p + " ") for p in GIT + GIT_ROLE[role])
    if name in ("gh", "glab"):
        if args[:1] == ["api"]:
            method = next((a.upper() for f, a in zip(args, args[1:]) if f in ("-X", "--method")), "")
            if not API_WRITE_FLAGS & set(args) and method in ("", "GET"):
                return True
            return role == "lead" and method != "DELETE" and any(k in a for a in args[1:] for k in API_WRITE_PATHS)
        pair = tuple(args[:2])
        return args[1:2] in (["view"], ["list"]) or pair in CHANGE_READS or role == "lead" and pair in CHANGE_WRITES
    if name == "sed":
        return not any(re.match(r"-[a-zA-Z]*i|--in-place", a) for a in args)
    if name == "tee":
        return all(is_safe_target(a) for a in args if not a.startswith("-"))
    return name in READS or name == "true"


def block_reason(payload: dict, role: str) -> str | None:
    tool_input = payload.get("tool_input") or {}
    if payload.get("tool_name") == "Bash":
        command = HEREDOC.sub(r"\3", tool_input.get("command") or "")
        try:
            segs, targets = segments(MARKER_WRITE.sub("", command) if role == "lead" else command)
        except ValueError:
            return f"The {role} may not run a command that cannot be parsed. Hand it to {HANDOFF[role]}."
        bad = next((" ".join(w[:2]) for w in segs if not command_allowed(role, w)), "")
        label = bad and f"run `{bad}`" or not all(map(is_safe_target, targets)) and "write outside the tmp, drafts and notes folders"
        return label and f"The {role} may not {label} from Bash. Hand it to {HANDOFF[role]}."
    if payload.get("tool_name") in EDIT_TOOLS and not is_coordination_file(tool_input.get("file_path") or tool_input.get("notebook_path") or ""):
        return f"The {role} does not edit files. Hand the change to {HANDOFF[role]}."
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
    role = os.environ.get("WORKSTATION_ROLE") or ("lead" if os.environ.get("HERDR_PANE_ID") else "")
    if role not in HANDOFF or is_subagent(payload) or (role == "lead" and escaped(payload)):
        sys.exit(0)
    reason = block_reason(payload, role)
    if reason:
        if not os.environ.get("WORKSTATION_ROLE"):
            reason += " WORKSTATION_ROLE is unset in herdr, so the lead rules apply; relaunch the tab with WORKSTATION_ROLE=lead, work or free."
        if role == "lead":
            reason += f" `{ESCAPE_PHRASE}` in your prompt lifts this for the turn."
        print(reason, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
