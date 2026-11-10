#!/usr/bin/env python3
"""Keep the drafts dir (DRAFTS_DIR, default ~/drafts) and the notes vault (NOTES_DIR, default ~/notes)
from growing ad hoc top-level folders.

Agent artifacts go to drafts/projects/<slug>/<ticket-or-topic>/, durable notes to
notes/projects/<slug>/. A write is blocked when its first path component under either root is not in
the allowlist, and every write under a retired path is blocked. Layers add folders and retired
paths through hooks.d.

Exit 0 = allow, exit 2 = block (stderr goes back to Claude).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from hook_config import load

EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
DRAFTS = Path(os.path.expanduser(os.environ.get("DRAFTS_DIR") or "~/drafts"))
NOTES = Path(os.path.expanduser(os.environ.get("NOTES_DIR") or "~/notes"))
CONFIG = load()
DRAFTS_ALLOWED = {
    "archive",
    "backups",
    "handoffs",
    "inbox",
    "projects",
    "research",
    "reviews",
    "tmp",
    "README.md",
    ".claude",
    ".DS_Store",
    *CONFIG.get("drafts_allowed", []),
}
NOTES_ALLOWED = {
    "areas",
    "decisions",
    "designs",
    "howto",
    "projects",
    "reference",
    "research",
    "runbooks",
    "templates",
    ".obsidian",
    ".DS_Store",
    *CONFIG.get("notes_allowed", []),
}
RETIRED = [
    Path(os.path.normpath(os.path.expanduser(p)))
    for p in CONFIG.get("retired_paths", [])
]


def slug() -> str:
    try:
        out = subprocess.run(
            ["current-project"], capture_output=True, text=True, timeout=10
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.strip() or "<slug>"


def relative(path: Path, root: Path) -> tuple[str, ...] | None:
    try:
        return path.relative_to(root).parts
    except ValueError:
        return None


def verdict(file_path: str) -> str | None:
    path = Path(os.path.normpath(os.path.expanduser(file_path)))
    for retired in RETIRED:
        if relative(path, retired) is not None:
            return f"{retired} is retired. Write to {DRAFTS}/projects/{slug()}/<ticket-or-topic>/ instead."
    parts = relative(path, DRAFTS)
    if parts:
        loose_file_exists = len(parts) == 1 and path.is_file()
        if parts[0] not in DRAFTS_ALLOWED and not loose_file_exists:
            return (
                f"{parts[0]} is not a known top-level folder in drafts. Write to "
                f"{DRAFTS}/projects/{slug()}/<ticket-or-topic>/ instead."
            )
    parts = relative(path, NOTES)
    if parts:
        top_level_note = len(parts) == 1 and parts[0].endswith(".md")
        if parts[0] not in NOTES_ALLOWED and not top_level_note:
            return (
                f"{parts[0]} is not a known top-level area in notes. Write to "
                f"{NOTES}/projects/{slug()}/ instead."
            )
    return None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    if not isinstance(payload, dict) or payload.get("tool_name") not in EDIT_TOOLS:
        sys.exit(0)
    file_path = (payload.get("tool_input") or {}).get("file_path", "")
    message = verdict(file_path) if file_path else None
    if message:
        print(message, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
