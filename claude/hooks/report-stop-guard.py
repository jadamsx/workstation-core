#!/usr/bin/env python3
"""Stop hook for manager sessions (WORKSTATION_REPORTS set): no silent stop.

A turn must end with a report file written this turn or a last message that starts with `WAITING:`. Otherwise
the stop is blocked once (`stop_hook_active` stops the loop) with what to do. The turn starts at the newest user
prompt in the transcript; when the transcript cannot be read the stop is allowed.

Exit 0 = allow, exit 2 = block (stderr goes back to Claude).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

MESSAGE = "Write your report (Status: decision or done) or reply WAITING: <what will wake you>."


def transcript_entries(path: str) -> list[dict]:
    entries = []
    for line in Path(path).read_text().splitlines():
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def text_of(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def is_prompt(entry: dict) -> bool:
    if entry.get("type") != "user":
        return False
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return True
    return isinstance(content, list) and any(isinstance(b, dict) and b.get("type") != "tool_result" for b in content)


def turn_start(entries: list[dict]) -> float | None:
    for entry in reversed(entries):
        if is_prompt(entry) and entry.get("timestamp"):
            return datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00")).timestamp()
    return None


def last_assistant_text(entries: list[dict]) -> str:
    for entry in reversed(entries):
        text = text_of((entry.get("message") or {}).get("content")) if entry.get("type") == "assistant" else ""
        if text.strip():
            return text
    return ""


def wrote_report_since(folder: str, since: float) -> bool:
    return any(p.stat().st_mtime >= since for p in Path(folder).glob("result-*.md"))


def main() -> None:
    folder = os.environ.get("WORKSTATION_REPORTS", "")
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    if not folder or not isinstance(payload, dict) or payload.get("stop_hook_active"):
        sys.exit(0)
    try:
        entries = transcript_entries(payload.get("transcript_path", ""))
        since = turn_start(entries)
    except (OSError, ValueError):
        sys.exit(0)
    if since is None:
        sys.exit(0)
    message = payload.get("last_assistant_message") or last_assistant_text(entries)
    if message.lstrip().startswith("WAITING:") or wrote_report_since(folder, since):
        sys.exit(0)
    print(MESSAGE, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
