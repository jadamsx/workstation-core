#!/usr/bin/env python3
"""Block browser writes while the Playwright page sits on a shared environment.

The last navigated host is remembered in a state file, because write tools carry no URL.
Hosts come from shared-envs.txt beside this hook (copy shared-envs.example.txt; SHARED_ENVS_FILE
overrides the path); no file means nothing is shared. Entries match the exact host, or any
subdomain when they start with a dot.

Exit 0 = allow, exit 2 = block (stderr goes back to Claude).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

HOSTS_FILE = Path(
    os.environ.get("SHARED_ENVS_FILE")
    or Path(__file__).resolve().parent / "shared-envs.txt"
)
STATE_FILE = Path(tempfile.gettempdir()) / "claude-shared-env-host"
WRITE_TOOLS = {
    "mcp__playwright__browser_type",
    "mcp__playwright__browser_fill_form",
    "mcp__playwright__browser_evaluate",
    "mcp__playwright__browser_file_upload",
}
NAVIGATE = "mcp__playwright__browser_navigate"


def is_shared(host: str) -> bool:
    if not HOSTS_FILE.is_file():
        return False
    entries = (line.strip() for line in HOSTS_FILE.read_text().splitlines())
    return any(
        host.endswith(e) if e.startswith(".") else host == e for e in entries if e
    )


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    if not isinstance(payload, dict):
        sys.exit(0)
    tool = payload.get("tool_name")
    if tool == NAVIGATE:
        STATE_FILE.write_text(
            urlparse((payload.get("tool_input") or {}).get("url", "")).hostname or ""
        )
    elif (
        tool in WRITE_TOOLS
        and STATE_FILE.is_file()
        and is_shared(STATE_FILE.read_text())
    ):
        print(
            f"{STATE_FILE.read_text()} is a shared environment: browser writes are blocked. "
            "Use a smoke-test agent, or run against a local stack.",
            file=sys.stderr,
        )
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
