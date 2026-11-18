#!/usr/bin/env python3
"""Block malformed manager reports. Active only when WORKSTATION_REPORTS is set (a manager session).

A file written into that folder must be named `result-*.md`, or be the `.draft` that is moved to such a name,
and its first line must be `Status: decision` or `Status: done`. Checked on Write, and on Bash commands that
redirect, tee, move or copy into the folder. Content is read from the Write input, a here-document, an
`echo` or `printf` argument, or the draft file a `mv` or `cp` moves. Content that cannot be seen up front passes.

Exit 0 = allow, exit 2 = block (stderr goes back to Claude).
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import sys
from pathlib import Path

STATUS_LINES = {"Status: decision", "Status: done"}
PATH_CHARS = r"(?:\$\([^)]*\)|[^\s\"';|&<>)])*"
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n(.*)", re.S)
INLINE = re.compile(r"\b(?:echo|printf)\s+(?:-\w+\s+)*([\"'])(.*?)\1", re.S)


def reports_dir() -> str:
    return os.environ.get("WORKSTATION_REPORTS", "").rstrip("/")


def usage() -> str:
    return (
        "A manager report is a file in $WORKSTATION_REPORTS named result-<timestamp>.md whose first line is "
        "`Status: decision` or `Status: done`. Write the body to the draft, then move it:\n"
        '  cat > "$WORKSTATION_REPORTS/.draft"\n'
        '  mv "$WORKSTATION_REPORTS/.draft" "$WORKSTATION_REPORTS/result-$(date +%Y%m%d-%H%M%S).md"'
    )


def name_problem(name: str) -> str:
    if name == ".draft" or fnmatch.fnmatch(name, "result-*.md"):
        return ""
    return f"`{name or '(the folder)'}` is not a report name."


def first_line_problem(text: str) -> str:
    first = text.lstrip("\n").split("\n", 1)[0].strip()
    return "" if first in STATUS_LINES else f"The first line is `{first}`, not a Status line."


def write_targets(command: str, folder: str) -> list[str]:
    path = re.escape(folder) + PATH_CHARS
    patterns = [
        rf">>?\s*[\"']?({path})",
        rf"\btee\b(?:\s+-\w+)*\s+[\"']?({path})",
        rf"\b(?:mv|cp|install|ln)\b[^;|&\n]*?\s[\"']?({path})[\"']?\s*(?:[;|&\n]|$)",
        rf"\btouch\b[^;|&\n]*?\s[\"']?({path})",
    ]
    return [m.group(1) for p in patterns for m in re.finditer(p, command)]


def moved_source(command: str, folder: str) -> str:
    found = re.search(rf"\b(?:mv|cp)\b(?:\s+-\w+)*\s+[\"']?({re.escape(folder)}{PATH_CHARS})[\"']?\s", command)
    return found.group(1) if found else ""


def visible_content(command: str, folder: str) -> str | None:
    heredoc = HEREDOC.search(command)
    if heredoc:
        return heredoc.group(3)
    inline = INLINE.search(command)
    if inline:
        return inline.group(2).replace("\\n", "\n")
    source = moved_source(command, folder)
    if source and Path(source).is_file():
        return Path(source).read_text()
    return None


def bash_problem(command: str, folder: str) -> str:
    command = command.replace("${WORKSTATION_REPORTS}", folder).replace("$WORKSTATION_REPORTS", folder)
    if folder not in command:
        return ""
    targets = write_targets(command, folder)
    for target in targets:
        problem = name_problem(os.path.basename(target))
        if problem:
            return problem
    if targets:
        content = visible_content(command, folder)
        if content is not None:
            return first_line_problem(content)
    return ""


def write_problem(file_path: str, content: str, folder: str) -> str:
    target = Path(os.path.expanduser(file_path)).resolve()
    if Path(folder).resolve() not in target.parents:
        return ""
    return name_problem(target.name) or first_line_problem(content)


def main() -> None:
    folder = reports_dir()
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    if not folder or not isinstance(payload, dict):
        sys.exit(0)
    tool_input = payload.get("tool_input") or {}
    tool = payload.get("tool_name")
    if tool == "Write":
        problem = write_problem(tool_input.get("file_path", ""), tool_input.get("content", ""), folder)
    elif tool == "Bash":
        problem = bash_problem(tool_input.get("command", ""), folder)
    else:
        problem = ""
    if problem:
        print(f"{problem} {usage()}", file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
