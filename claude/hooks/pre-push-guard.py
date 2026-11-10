#!/usr/bin/env python3
"""Block `git push` until the checks that would fail CI have passed locally.

Runs pre-commit on the diff, then inspects the branch's open PR or MR (`gh` for GitHub, `glab` for
GitLab): a missing ticket key when the hooks.d ``change`` rules ask for one, leftover template placeholder text,
and a change that is already approved, because pushing resets approval and re-runs review and CI.
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


def block(reason: str, fix: str) -> None:
    print(f"{reason}\n\n{fix}", file=sys.stderr)
    sys.exit(2)


def is_git_push(command: str) -> bool:
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    return "git" in parts and "push" in parts


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
    if not is_git_push(command):
        sys.exit(0)
    if any(marker in command for marker in REOPEN_MARKERS):
        sys.exit(0)

    cwd = push_dir(command, payload.get("cwd") or os.getcwd())

    check_pre_commit(cwd)
    change = change_for_branch(cwd)
    if change:
        check_change(change, cwd)

    sys.exit(0)


if __name__ == "__main__":
    main()
