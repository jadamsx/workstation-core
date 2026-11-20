#!/usr/bin/env python3
"""Block the lead and work tabs (WORKSTATION_ROLE=lead|work) from editing files or doing builder work in Bash.

Subagent tool calls carry `agent_id` in the hook payload, the main thread's own do not. Markdown notes
under the drafts and notes folders stay editable. Putting `main-thread-ok` in a prompt lifts the
gate for the lead for that turn: the UserPromptSubmit wiring records it per session, PreToolUse reads it.

Exit 0 = allow, exit 2 = block (stderr goes back to Claude).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ESCAPE_PHRASE = "main-thread-ok"
EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
EDIT_EXEMPT_DIRS = ("/.claude/plans/", "/.claude/projects/")
HANDOFF = {"lead": "the work tab", "work": "a builder agent"}
CMD = r"(?:^|[;&|(]\s*)"
BASH_RULES = (
    ("commit or push", CMD + r"git\s+(?:-C\s+\S+\s+)?(?:commit|push)\b"),
    (
        "run tests or linters",
        CMD
        + r"(?:(?:uv\s+run|python3?\s+-m|npx)\s+)*(?:pytest|ruff|eslint|mypy|unittest)\b"
        + r"|"
        + CMD
        + r"(?:(?:npm|pnpm|yarn)\s+(?:run\s+)?(?:test|lint)|make\s+(?:test|lint|check))\b",
    ),
    ("edit files in place", r"\bsed\b[^|;&]*\s-\w*i|REOPEN_REVIEW\s*=|(?:touch|tee|>>?)\s*\S*verify-self-pass"),
)
WRITE_TARGET = re.compile(r"(?<![<>])>>?\s*([^\s&|;<>()]+)|\btee\s+(?:-\w+\s+)*([^\s&|;<>()]+)")
SAFE_PREFIXES = ("/dev/", "/tmp/", "/private/tmp/", "$TMPDIR", "${TMPDIR")


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
    target = os.path.expanduser(target.strip("'\""))
    tmp = os.environ.get("TMPDIR", "").rstrip("/")
    if target.startswith(SAFE_PREFIXES) or "scratchpad" in target or (tmp and target.startswith(tmp + "/")):
        return True
    resolved = os.path.realpath(target)
    return any(resolved.startswith(os.path.realpath(root) + "/") for root in coordination_dirs())


def bash_violation(command: str) -> str | None:
    for label, pattern in BASH_RULES:
        if re.search(pattern, command):
            return label
    if any(not is_safe_target(a or b) for a, b in WRITE_TARGET.findall(command)):
        return "write repo files"
    return None


def block_reason(payload: dict, role: str) -> str | None:
    tool_input = payload.get("tool_input") or {}
    if payload.get("tool_name") == "Bash":
        label = bash_violation(tool_input.get("command") or "")
        return label and f"The {role} does not {label} from Bash. Hand it to {HANDOFF[role]}."
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
    if role not in HANDOFF or is_subagent(payload) or (role == "lead" and escaped(payload)):
        sys.exit(0)
    reason = block_reason(payload, role)
    if reason:
        lift = f" `{ESCAPE_PHRASE}` in your prompt lifts this for the turn." if role == "lead" else ""
        print(reason + lift, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
