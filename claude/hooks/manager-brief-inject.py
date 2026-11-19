#!/usr/bin/env python3
"""SessionStart hook for lead and manager sessions: hand back the role's brief.

A lead (WORKSTATION_ROLE=lead) gets `claude/templates/lead-brief.md` on every source, since nothing else carries it.
A manager (WORKSTATION_REPORTS set) gets `claude/templates/manager-brief.md` on source `compact` or `clear`, when the
system prompt addition may no longer be in context. Prints nothing otherwise. A manager's every source also records
the payload's `session_id` as `session_id` in its manager.json, so a restart can resume the conversation.
Always exits 0.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
BRIEF = TEMPLATES / "manager-brief.md"
LEAD_BRIEF = TEMPLATES / "lead-brief.md"
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


def brief_for(source: object) -> Path | None:
    if os.environ.get("WORKSTATION_ROLE") == "lead":
        return LEAD_BRIEF
    if os.environ.get("WORKSTATION_REPORTS") and source in SOURCES:
        return BRIEF
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict):
        return 0
    if os.environ.get("WORKSTATION_REPORTS"):
        record_session(Path(os.environ["WORKSTATION_REPORTS"]), payload.get("session_id"))
    brief = brief_for(payload.get("source"))
    if brief is None or not brief.is_file():
        return 0
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": brief.read_text(),
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
