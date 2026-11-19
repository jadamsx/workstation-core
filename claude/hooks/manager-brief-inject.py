#!/usr/bin/env python3
"""SessionStart hook for manager sessions (WORKSTATION_REPORTS set): hand back the manager brief.

Runs on source `compact` or `clear`, when the system prompt addition may no longer be in context, and returns
`claude/templates/manager-brief.md` as additionalContext. Prints nothing otherwise. On every source it also records
the payload's `session_id` as `session_id` in the manager's manager.json, so a restart can resume the conversation.
Always exits 0.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

BRIEF = Path(__file__).resolve().parent.parent / "templates/manager-brief.md"
SOURCES = {"compact", "clear"}


def record_session(reports: Path, session_id: object) -> None:
    info_file = reports / "manager.json"
    if not isinstance(session_id, str) or not session_id:
        return
    try:
        info = json.loads(info_file.read_text())
        if not isinstance(info, dict):
            return
        with tempfile.NamedTemporaryFile("w", dir=reports, prefix=".manager.", delete=False) as tmp:
            tmp.write(json.dumps({**info, "session_id": session_id}))
        os.replace(tmp.name, info_file)
    except (OSError, ValueError):
        return


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if not os.environ.get("WORKSTATION_REPORTS") or not isinstance(payload, dict):
        return 0
    record_session(Path(os.environ["WORKSTATION_REPORTS"]), payload.get("session_id"))
    if payload.get("source") not in SOURCES or not BRIEF.is_file():
        return 0
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": BRIEF.read_text(),
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
