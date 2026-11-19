#!/usr/bin/env python3
"""Deny new top-level Agent spawns while the usage gate is parked.

Exempt: a spawn made from inside a subagent (its node already started) and one from a session whose working
directory sits in a worktree with a `.owns` file, so running work keeps its sub-spawns.
"""

from __future__ import annotations

import json
import sys
import time
from importlib.machinery import SourceFileLoader
from pathlib import Path

gate = SourceFileLoader("usage_gate", str(Path(__file__).resolve().parents[2] / "bin" / "usage-gate")).load_module()


def in_owned_worktree(cwd: str) -> bool:
    path = Path(cwd or ".").resolve()
    return any((p / ".owns").is_file() for p in [path, *path.parents])


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    if payload.get("tool_name") != "Agent" or payload.get("agent_id") or in_owned_worktree(payload.get("cwd", "")):
        sys.exit(0)
    until = gate.parked_until()
    if until is not None:
        stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(until))
        print(f"Usage gate: new work is parked until {stamp}. Running work and its sub-spawns continue.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
