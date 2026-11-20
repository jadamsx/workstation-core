#!/usr/bin/env python3
"""Block the Opus lead (WORKSTATION_ROLE=lead) from editing files.

Subagent tool calls carry `agent_id` in the hook payload, the lead's own do not. Markdown notes
under the drafts and notes folders stay editable. Putting `main-thread-ok` in a prompt lifts the
gate for that turn: the UserPromptSubmit wiring records it per session, PreToolUse reads it.

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


def block_reason(payload: dict) -> str | None:
    if payload.get("tool_name") not in EDIT_TOOLS:
        return None
    tool_input = payload.get("tool_input") or {}
    if is_coordination_file(tool_input.get("file_path") or tool_input.get("notebook_path") or ""):
        return None
    return "The lead does not edit files. Hand the change to the work tab."


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
    if os.environ.get("WORKSTATION_ROLE") != "lead" or is_subagent(payload) or escaped(payload):
        sys.exit(0)
    reason = block_reason(payload)
    if reason:
        print(f"{reason} `{ESCAPE_PHRASE}` in your prompt lifts this for the turn.", file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
