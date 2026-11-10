#!/usr/bin/env python3
"""After an edit to a note in the vault, run notes-lint on it and hand failures back to Claude.

PostToolUse on Edit, Write and MultiEdit. Exit 2 puts stderr in front of Claude. Any internal
problem (linter missing, timeout, crash) exits 0, because a broken guard must not stall writes.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from hook_config import load

EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
SKIPPED = {
    "templates",
    ".obsidian",
    ".git",
    ".githooks",
    *load().get("lint_skipped", []),
}


def vault_root() -> Path:
    return Path(os.path.expanduser(os.environ.get("NOTES_DIR") or "~/notes")).resolve()


def vault_note(file_path: str) -> Path | None:
    path = Path(file_path).resolve()
    try:
        rel = path.relative_to(vault_root())
    except ValueError:
        return None
    if path.suffix != ".md" or rel.parts[0] in SKIPPED or not path.is_file():
        return None
    return path


def linter() -> str | None:
    beside = Path(__file__).resolve().parent.parent.parent / "bin/notes-lint"
    return str(beside) if beside.is_file() else shutil.which("notes-lint")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict) or payload.get("tool_name") not in EDIT_TOOLS:
            sys.exit(0)
        note = vault_note((payload.get("tool_input") or {}).get("file_path", ""))
        lint = linter()
        if note is None or lint is None:
            sys.exit(0)
        result = subprocess.run(
            [sys.executable, lint, "--root", str(vault_root()), str(note)],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, ValueError, subprocess.SubprocessError):
        sys.exit(0)
    if result.returncode == 1 and result.stdout.strip():
        print(
            "notes-lint failed on the note you just wrote. Fix every line below, in place, before "
            "continuing (rules: templates/ and README.md in the vault):\n"
            + result.stdout.strip(),
            file=sys.stderr,
        )
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
