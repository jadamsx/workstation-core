#!/usr/bin/env python3
"""Block recursive `rm` outside throwaway locations.

Allowed roots: $TMPDIR, the drafts dir (DRAFTS_DIR, default ~/drafts), ~/.cache, a repo's
.claude/worktrees/*, and any path through node_modules, .venv, dist, build or __pycache__.

Exit 0 = allow, exit 2 = block (stderr goes back to Claude).
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys

SAFE_DIR_NAMES = {"node_modules", ".venv", "dist", "build", "__pycache__"}
RM_PREFIXES = {"sudo", "command", "xargs", "exec", "env"}
UNSAFE_EXPANSION = re.compile(r"\$\(|`|\$(?!\{?(TMPDIR|HOME)\}?(/|$))")
SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|\n]")


def tokens(segment: str) -> list[str]:
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def drafts_dir() -> str:
    return os.path.expanduser(os.environ.get("DRAFTS_DIR") or "~/drafts")


def rm_target_is_safe(target: str, cwd: str) -> bool:
    if UNSAFE_EXPANSION.search(target):
        return False
    home = os.path.expanduser("~")
    tmpdir = os.environ.get("TMPDIR", "")
    path = re.sub(
        r"^\$\{?TMPDIR\}?", tmpdir if tmpdir else "/nonexistent-tmpdir", target
    )
    path = re.sub(r"^\$\{?HOME\}?", home, path)
    path = os.path.normpath(
        os.path.join(cwd, os.path.expanduser(path)) if cwd else os.path.expanduser(path)
    )
    roots = [os.path.normpath(drafts_dir()), os.path.join(home, ".cache")]
    if tmpdir:
        roots.append(os.path.normpath(tmpdir))
    if any(path.startswith(root.rstrip("/") + "/") for root in roots):
        return True
    parts = path.split("/")
    for i, part in enumerate(parts[:-2]):
        if part == ".claude" and parts[i + 1] == "worktrees":
            return True
    return any(part in SAFE_DIR_NAMES for part in parts)


def check_rm(command: str, cwd: str) -> None:
    for segment in SEGMENT_SPLIT.split(command):
        parts = tokens(segment)
        while parts and (re.match(r"\w+=", parts[0]) or parts[0] in RM_PREFIXES):
            parts = parts[1:]
        if not parts or os.path.basename(parts[0]) != "rm":
            continue
        args = parts[1:]
        end_of_flags = args.index("--") if "--" in args else len(args)
        flags = [a for a in args[:end_of_flags] if a.startswith("-")]
        recursive = any(
            f == "--recursive" or (not f.startswith("--") and set(f) & {"r", "R"})
            for f in flags
        )
        if not recursive:
            continue
        targets = [a for a in args[:end_of_flags] if not a.startswith("-")] + args[
            end_of_flags + 1 :
        ]
        bad = [t for t in targets if not rm_target_is_safe(t, cwd)]
        if bad:
            print(
                f"Recursive rm of {', '.join(bad)} is blocked: rm -r only runs under $TMPDIR, "
                f"{drafts_dir()}, ~/.cache, a repo's .claude/worktrees/*, or on node_modules, .venv, "
                "dist, build and __pycache__. Delete anything else by hand.",
                file=sys.stderr,
            )
            sys.exit(2)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    if not isinstance(payload, dict) or payload.get("tool_name") != "Bash":
        sys.exit(0)
    check_rm(
        (payload.get("tool_input") or {}).get("command", ""), payload.get("cwd") or ""
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
