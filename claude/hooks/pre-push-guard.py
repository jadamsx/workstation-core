#!/usr/bin/env python3
"""Block `git push` until the checks that would fail CI have passed locally.

Deletes and tag-only pushes are exempt. Otherwise runs pre-commit on the diff, then inspects the
branch's open change (`gh` or `glab`): a missing ticket key when the hooks.d ``change`` rules
ask for one, leftover template placeholder text, and a change that is already approved,
because pushing resets approval and re-runs review and CI.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys

from hook_config import load, ticket_exempt

RULES = load().get("change", {})
TIMEOUT_S = 25
TICKET_KEY = RULES.get("ticket_key", r"[A-Z][A-Z0-9]+-\d+")
TITLE_REQUIRES_TICKET = RULES.get("title_requires_ticket", False)
TICKET_EXEMPT = RULES.get("ticket_exempt_projects", [])
PLACEHOLDERS = (
    "Briefly summarise",
    "Provide a concise overview",
    "Describe your changes here",
    *RULES.get("placeholders", []),
)
REOPEN_MARKERS = ("--reopen-review", "REOPEN_REVIEW")
HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?.*?\n\1\b", re.DOTALL)
ENV_ASSIGN = re.compile(r"^[A-Za-z_]\w*=")
PREFIXES = {"sudo", "command", "xargs", "exec", "env"}
GIT_OPTIONS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}


def block(reason: str, fix: str) -> None:
    print(f"{reason}\n\n{fix}", file=sys.stderr)
    sys.exit(2)


def command_parts(command: str) -> list[list[str]]:
    """Token lists of each command in the text, heredoc bodies dropped and quoted text kept whole."""
    parts, buf, quote, i = [], "", "", 0
    text = HEREDOC.sub("", command)
    while i < len(text):
        ch = text[i]
        if ch == "\\" and quote != "'":
            buf += text[i : i + 2]
            i += 2
            continue
        if quote:
            quote = "" if ch == quote else quote
        elif ch in "'\"":
            quote = ch
        elif ch in ";&|()\n":
            parts.append(buf)
            buf = ""
            i += 1
            continue
        buf += ch
        i += 1
    parts.append(buf)
    result = []
    for part in parts:
        try:
            tokens = shlex.split(part)
        except ValueError:
            tokens = part.split()
        while tokens and (ENV_ASSIGN.match(tokens[0]) or tokens[0] in PREFIXES):
            tokens = tokens[1:]
        if tokens and os.path.basename(tokens[0]) in ("bash", "sh") and "-c" in tokens[:-1]:
            result.extend(command_parts(tokens[tokens.index("-c") + 1]))
        elif tokens:
            result.append(tokens)
    return result


def git_subcommand(tokens: list[str]) -> tuple[str, list[str]]:
    if os.path.basename(tokens[0]) != "git":
        return "", []
    i = 1
    while i < len(tokens):
        if tokens[i] in GIT_OPTIONS_WITH_VALUE:
            i += 2
        elif tokens[i].startswith("-"):
            i += 1
        else:
            return tokens[i], tokens[i + 1 :]
    return "", []


def push_args(command: str) -> list[str] | None:
    for tokens in command_parts(command):
        sub, args = git_subcommand(tokens)
        if sub == "push":
            return args
    return None


def is_exempt_push(args: list[str]) -> bool:
    return any(
        a in ("--delete", "-d", "--tags", "tag") or a.startswith("refs/tags/")
        for a in args
    )


def push_dir(command: str, cwd: str) -> str:
    """The repo the push runs in: a leading `cd <dir>` or `git -C <dir>` wins over the session cwd."""
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    target = cwd
    for i, part in enumerate(parts[:-1]):
        nxt = os.path.expanduser(parts[i + 1])
        if part == "cd":
            target = os.path.join(target, nxt)
        elif part == "-C" and i > 0 and parts[i - 1] == "git":
            target = os.path.join(target, nxt)
        elif part == "push":
            break
    return os.path.normpath(target)


def run(args: list[str], cwd: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args, cwd=cwd, capture_output=True, text=True, timeout=TIMEOUT_S
    )


def load_json(args: list[str], cwd: str) -> dict | None:
    try:
        proc = run(args, cwd)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if proc.returncode != 0:
        return None
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def change_for_branch(cwd: str) -> dict | None:
    """The current branch's open change as {title, body, approved}, or None when there is none yet."""
    pr = load_json(["gh", "pr", "view", "--json", "title,body,reviewDecision"], cwd)
    if pr:
        return {
            "title": pr.get("title", ""),
            "body": pr.get("body") or "",
            "approved": pr.get("reviewDecision") == "APPROVED",
        }
    mr = load_json(["glab", "mr", "view", "--output", "json"], cwd)
    if mr:
        return {
            "title": mr.get("title", ""),
            "body": mr.get("description") or "",
            "approved": mr_approved(mr.get("iid"), cwd),
        }
    return None


def check_pre_commit(cwd: str) -> None:
    if not os.path.exists(os.path.join(cwd, ".pre-commit-config.yaml")):
        return
    try:
        proc = run(
            ["pre-commit", "run", "--from-ref", "origin/HEAD", "--to-ref", "HEAD"], cwd
        )
    except subprocess.TimeoutExpired:
        return  # fail open: a slow hook must not become a reason to bypass this one
    except FileNotFoundError:
        return
    if proc.returncode != 0:
        failed = [
            line.split("...")[0].strip()
            for line in proc.stdout.splitlines()
            if "Failed" in line
        ]
        block(
            "pre-commit fails on this diff: " + (", ".join(failed) or "see output"),
            "Fix it here rather than in CI. `pre-commit run --from-ref origin/HEAD --to-ref HEAD`",
        )


def mr_approved(iid: int | None, cwd: str) -> bool:
    """`glab mr view` carries no approval state; the approvals endpoint does."""
    if not iid:
        return False
    data = load_json(
        ["glab", "api", f"projects/:id/merge_requests/{iid}/approvals"], cwd
    )
    return bool(data) and (bool(data.get("approved")) or bool(data.get("approved_by")))


def check_change(change: dict, cwd: str) -> None:
    title = change["title"]
    if (
        TITLE_REQUIRES_TICKET
        and not re.search(rf"\b{TICKET_KEY}\b", title)
        and not ticket_exempt(TICKET_EXEMPT, cwd)
    ):
        block(
            f"Change title has no ticket key: {title!r}",
            "Titles carry the key, e.g. `ABC-123 summary`. Without it the tracker loses the link.",
        )

    hit = next((p for p in PLACEHOLDERS if p in change["body"]), None)
    if hit:
        block(
            f"Change description still has template placeholder text: {hit!r}",
            "Fill the section or mark it `N/A - <reason>`.",
        )

    if change["approved"]:
        block(
            "This change is already approved. Pushing resets the approval and re-runs review and CI.",
            "Batch the change, or push with --reopen-review in the command if it genuinely must go now.",
        )


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    if payload.get("tool_name") != "Bash":
        sys.exit(0)

    command = payload.get("tool_input", {}).get("command", "")
    args = push_args(command)
    if (
        args is None
        or is_exempt_push(args)
        or any(marker in command for marker in REOPEN_MARKERS)
    ):
        sys.exit(0)
    cwd = push_dir(command, payload.get("cwd") or os.getcwd())

    check_pre_commit(cwd)
    change = change_for_branch(cwd)
    if change:
        check_change(change, cwd)

    sys.exit(0)


if __name__ == "__main__":
    main()
