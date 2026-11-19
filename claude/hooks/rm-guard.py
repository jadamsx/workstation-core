#!/usr/bin/env python3
"""Block recursive `rm` outside throwaway locations and `rm -rf` in any form.

`rm -rf` in any form in the command text is denied. A Bash call with `dangerouslyDisableSandbox` is
allowed through this hook once the rm checks pass; settings deny rules still apply.

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
RM_FLAGS = re.compile(r"\brm((?:[ \t]+-{1,2}[\w-]+)+)")
RM_RF_MESSAGE = "Never write rm -rf, even quoted; move it to ~/.Trash instead."
FAILED_MESSAGE = "rm-guard failed unexpectedly ({}); the call is denied until the hook is fixed."


def tokens(segment: str) -> list[str]:
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def split_command(command: str) -> list[str]:
    command = command.replace("\\\n", "")
    parts, buf, quote, i = [], "", "", 0
    while i < len(command):
        ch = command[i]
        if quote == "'":
            quote = "" if ch == "'" else quote
        elif ch == "\\":
            buf += command[i : i + 2]
            i += 2
            continue
        elif quote:
            quote = "" if ch == quote else quote
        elif ch in "'\"":
            quote = ch
        elif ch in ";&|()\n<>":
            parts.append(buf)
            buf = ""
            i += 1
            continue
        buf += ch
        i += 1
    return [*parts, buf]


def rm_flags_forbidden(flags: list[str]) -> bool:
    short = set("".join(f[1:] for f in flags if not f.startswith("--")))
    recursive = "--recursive" in flags or short & {"r", "R"}
    force = "--force" in flags or "f" in short
    return bool(recursive and force)


def has_rm_rf(command: str) -> bool:
    if any(
        rm_flags_forbidden(m.group(1).split())
        for m in RM_FLAGS.finditer(command.replace("\\\n", ""))
    ):
        return True
    for part in split_command(command):
        words = tokens(part)
        for i, word in enumerate(words):
            if os.path.basename(word) != "rm":
                continue
            args = words[i + 1 :]
            args = args[: args.index("--")] if "--" in args else args
            if rm_flags_forbidden([a for a in args if a.startswith("-") and a != "-"]):
                return True
    return False


def escape_requested(value: object) -> bool:
    return value is True or (isinstance(value, str) and value.strip().lower() == "true")


def deny(message: str) -> None:
    print(message, file=sys.stderr)
    sys.exit(2)


# A denied or prompted escape strands an unattended agent; settings deny rules still apply.
def allow_escape() -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "permissionDecisionReason": "sandbox escape allowed after the rm check",
                }
            }
        )
    )
    sys.exit(0)


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
    try:
        rm_rf = has_rm_rf(command)
        escape = escape_requested(tool_input.get("dangerouslyDisableSandbox"))
    except Exception as exc:
        deny(FAILED_MESSAGE.format(type(exc).__name__))
    if rm_rf:
        deny(RM_RF_MESSAGE)
    check_rm(command, payload.get("cwd") or "")
    if escape:
        allow_escape()
    sys.exit(0)


if __name__ == "__main__":
    main()
