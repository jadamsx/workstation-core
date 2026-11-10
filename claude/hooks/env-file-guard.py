#!/usr/bin/env python3
"""Block edits to real `.env.*` files while leaving `.env.example` style templates editable.

permissions.deny cannot express an exception, so `Edit(**/.env)` stays a deny rule and every
`.env.<suffix>` is handled here: only names ending in `.example`, `.sample` or `.template` pass.

Exit 0 = allow, exit 2 = block (stderr goes back to Claude).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}
TEMPLATE_SUFFIXES = (".example", ".sample", ".template")


def is_real_env_file(file_path: str) -> bool:
    name = Path(file_path).name
    return name.startswith(".env.") and not name.endswith(TEMPLATE_SUFFIXES)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    if not isinstance(payload, dict) or payload.get("tool_name") not in EDIT_TOOLS:
        sys.exit(0)
    file_path = (payload.get("tool_input") or {}).get("file_path", "")
    if file_path and is_real_env_file(file_path):
        print(
            f"{Path(file_path).name} is a real env file and holds secrets. Edit the matching "
            ".env.example (or .sample, .template) instead.",
            file=sys.stderr,
        )
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
