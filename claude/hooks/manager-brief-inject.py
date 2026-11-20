#!/usr/bin/env python3
"""SessionStart hook for lead and work sessions: hand back the role's brief.

A lead (WORKSTATION_ROLE=lead) gets `claude/templates/lead-brief.md` on every source, since nothing else carries it.
A work session (WORKSTATION_ROLE=work) gets `claude/templates/manager-brief.md` on source `compact` or `clear`, when the
system prompt addition may no longer be in context. Prints nothing otherwise. Always exits 0.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
BRIEF = TEMPLATES / "manager-brief.md"
LEAD_BRIEF = TEMPLATES / "lead-brief.md"
SOURCES = {"compact", "clear"}


def brief_for(source: object) -> Path | None:
    role = os.environ.get("WORKSTATION_ROLE")
    if role == "lead":
        return LEAD_BRIEF
    if role == "work" and source in SOURCES:
        return BRIEF
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict):
        return 0
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
