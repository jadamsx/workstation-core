#!/usr/bin/env python3
"""SessionStart hook: hand Claude the project note of the workspace it runs in.

Runs `current-project` for the slug, reads <vault>/projects/<slug>/index.md (vault is NOTES_DIR,
default ~/notes) and returns it as additionalContext, capped at LIMIT characters. Prints nothing
when there is no project or the note still holds only the template. Always exits 0.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

LIMIT = 4000


def vault() -> Path:
    return Path(os.path.expanduser(os.environ.get("NOTES_DIR") or "~/notes"))


def body(text: str) -> list[str]:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        end = next(
            (i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), 0
        )
        lines = lines[end + 1 :]
    return [line.strip() for line in lines]


def written(note: str, template: str) -> bool:
    boilerplate = set(body(template))
    return any(
        line and not line.startswith("#") and line not in boilerplate
        for line in body(note)
    )


def slug() -> str:
    out = subprocess.run(
        ["current-project"], capture_output=True, text=True, timeout=10
    ).stdout
    return out.strip()


def main() -> int:
    try:
        name = slug()
        note = vault() / "projects" / name / "index.md" if name else None
        if note is None or not note.is_file():
            return 0
        text = note.read_text()
        template = vault() / "templates/project.md"
        if not written(text, template.read_text() if template.is_file() else ""):
            return 0
        context = f"Project note for {name} ({note}):\n\n{text}"
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SessionStart",
                        "additionalContext": context[:LIMIT],
                    }
                }
            )
        )
    except (OSError, subprocess.SubprocessError) as error:
        print(f"project-context: {error}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
