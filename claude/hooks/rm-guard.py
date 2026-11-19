#!/usr/bin/env python3
"""Block calls Claude Code would prompt on, and recursive `rm` outside throwaway locations.

Denied everywhere: `rm -rf` in any form in the command text, and `dangerouslyDisableSandbox` for a
command that is not on sandbox.excludedCommands (every `&&`/`;`/`|` part must match a pattern).

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
from pathlib import Path

SAFE_DIR_NAMES = {"node_modules", ".venv", "dist", "build", "__pycache__"}
RM_PREFIXES = {"sudo", "command", "xargs", "exec", "env"}
UNSAFE_EXPANSION = re.compile(r"\$\(|`|\$(?!\{?(TMPDIR|HOME)\}?(/|$))")
SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|\n]")
RM_FLAGS = re.compile(r"\brm((?:[ \t]+-{1,2}[\w-]+)+)")
BASE_SETTINGS = Path(__file__).resolve().parent.parent / "settings.base.json"
RM_RF_MESSAGE = "Never write rm -rf, even quoted; move it to ~/.Trash instead."
SANDBOX_MESSAGE = (
    "That command is not on the sandbox excluded list; do not escape the sandbox. "
    "Write a decision report to the coordinator instead."
)


def tokens(segment: str) -> list[str]:
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def has_rm_rf(command: str) -> bool:
    for match in RM_FLAGS.finditer(command):
        flags = match.group(1).split()
        short = set("".join(f[1:] for f in flags if not f.startswith("--")))
        recursive = "--recursive" in flags or short & {"r", "R"}
        force = "--force" in flags or "f" in short
        if recursive and force:
            return True
    return False


def excluded_patterns() -> list[str]:
    for path in (Path.home() / ".claude/settings.json", BASE_SETTINGS):
        try:
            return json.loads(path.read_text())["sandbox"]["excludedCommands"]
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return []


def is_excluded(command: str) -> bool:
    patterns = [
        re.compile(".*".join(map(re.escape, p.split("*"))) + r"\Z", re.S)
        for p in excluded_patterns()
    ]
    parts = [p.strip() for p in SEGMENT_SPLIT.split(command) if p.strip()]
    return bool(parts) and all(any(rx.match(part) for rx in patterns) for part in parts)


def deny(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(2)


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
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command", "")
    if has_rm_rf(command):
        deny(RM_RF_MESSAGE)
    if tool_input.get("dangerouslyDisableSandbox") is True and not is_excluded(command):
        deny(SANDBOX_MESSAGE)
    check_rm(command, payload.get("cwd") or "")
    sys.exit(0)


if __name__ == "__main__":
    main()
