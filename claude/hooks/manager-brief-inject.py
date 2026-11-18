#!/usr/bin/env python3
"""SessionStart hook for manager sessions (WORKSTATION_REPORTS set): hand back the manager brief.

Runs on source `compact` or `clear`, when the system prompt addition may no longer be in context, and returns
`claude/templates/manager-brief.md` as additionalContext. Prints nothing otherwise. Always exits 0.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BRIEF = Path(__file__).resolve().parent.parent / "templates/manager-brief.md"
SOURCES = {"compact", "clear"}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if not os.environ.get("WORKSTATION_REPORTS") or not isinstance(payload, dict):
        return 0
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
