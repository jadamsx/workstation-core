#!/usr/bin/env python3
"""PreToolUse guard on `git commit`, `gh pr create|edit` and `glab mr create|update`.

Blocks AI-style comments in the staged diff, a missing pre-commit git hook, and change titles or
descriptions that break the rules in the ``change`` object of hooks.d (see hook_config.py):
require_gitmoji, title_requires_ticket, commit_forbids_ticket, ticket_key, commit_ticket_key,
ticket_exempt_projects and description_cut_markers. Every rule is off until a layer turns it on.
Non-Bash tools that carry a title, description and project_id (a source control MCP create or update) are
checked as changes too; the settings matcher says which tools reach this hook.

Exit 0 = allow, exit 2 = block (stderr is fed back to Claude to fix and retry).
"""

import json
import os
import pathlib
import re
import shlex
import subprocess
import sys

from hook_config import load, ticket_exempt

RULES = load().get("change", {})
TICKET_KEY = RULES.get("ticket_key", r"[A-Z][A-Z0-9]+-\d+")
REQUIRE_GITMOJI = RULES.get("require_gitmoji", False)
TITLE_REQUIRES_TICKET = RULES.get("title_requires_ticket", False)
COMMIT_FORBIDS_TICKET = RULES.get("commit_forbids_ticket", False)
TICKET_EXEMPT = RULES.get("ticket_exempt_projects", [])
CUT_MARKERS = RULES.get("description_cut_markers", [])
MAX_TITLE = 80
MAX_DESCRIPTION = 3000

TICKET_RE = re.compile(rf"\b{TICKET_KEY}\b")
COMMIT_TICKET_RE = re.compile(rf"\b{RULES.get('commit_ticket_key', TICKET_KEY)}\b")
GITMOJI_RE = re.compile(r"^(:\w+:|[\U0001F000-\U0001FAFF☀-➿⬀-⯿])")
TEMPLATE_FILES = (
    ".github/pull_request_template.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "docs/pull_request_template.md",
    ".gitlab/merge_request_templates/default.md",
)
COMMIT = re.compile(r"\bgit\b[^|;&]*\bcommit\b")
CD_DIR = re.compile(r"^\s*cd\s+(\"[^\"]*\"|'[^']*'|\S+)")
GIT_DIR = re.compile(r"\bgit\s+-C\s+(\"[^\"]*\"|'[^']*'|\S+)")
REPO_FLAG = re.compile(r"(?<!\S)(?:--repo|-R)[=\s]+([^\s\"']+)")
TEMPLATE_DIRS = (".github/PULL_REQUEST_TEMPLATE", ".gitlab/merge_request_templates")
CHANGE_CREATE = re.compile(r"\b(gh\s+pr\s+(create|edit)|glab\s+mr\s+(create|update))\b")
SMELL_PATTERNS = re.compile(
    r"^\+\s*(#|//|--|/\*)\s*("
    r"This (function|method|class|file|code|line)\b"
    r"|Now (we|let's|call|check)\b"
    r"|First,|Then,|Next,|Finally,"
    r"|Here we\b|Let's\b|Note that\b|As mentioned\b"
    r"|Initialize the\b|Create a new\b|Loop (through|over)\b"
    r"|Check if the\b|Return the\b|Call the\b|Import(ing)? the\b"
    r"|Added? (to|for|by)\b|Updated? (to|for)\b|Fix(ed)? (the|a)\b"
    r"|TODO: implement|Step \d"
    r")",
    re.IGNORECASE,
)


def staged_comment_smells(cwd: str) -> list[str]:
    try:
        diff = subprocess.run(
            ["git", "diff", "--cached", "--unified=0"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10,
        ).stdout
    except Exception:
        return []
    return [
        line[1:].strip()[:120]
        for line in diff.splitlines()
        if SMELL_PATTERNS.match(line)
    ][:10]


def precommit_installed(cwd: str) -> bool:
    if not (pathlib.Path(cwd) / ".pre-commit-config.yaml").is_file():
        return True
    try:
        hook = subprocess.run(
            ["git", "rev-parse", "--git-path", "hooks/pre-commit"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10,
        ).stdout.strip()
    except Exception:
        return True
    return not hook or (pathlib.Path(cwd) / hook).is_file()


def template_path(root: pathlib.Path) -> pathlib.Path | None:
    for name in TEMPLATE_FILES:
        if (root / name).is_file():
            return root / name
    for name in TEMPLATE_DIRS:
        found = sorted((root / name).glob("*.md")) if (root / name).is_dir() else []
        if found:
            return found[0]
    return None


def user_written(description: str) -> str:
    cuts = [i for i in (description.find(m) for m in CUT_MARKERS) if i != -1]
    return description[: min(cuts)] if cuts else description


def template_headings(cwd: str, project_id: str = "") -> list[str]:
    start = pathlib.Path(cwd)
    for parent in [start, *start.parents]:
        template = template_path(parent)
        if template:
            return re.findall(r"^#{1,3}\s+(.+)$", template.read_text(), re.MULTILINE)
        if (parent / ".git").exists():
            break
    slug = project_id.rstrip("/").split("/")[-1]
    template = template_path(start / slug) if slug else None
    if template:
        return re.findall(r"^#{1,3}\s+(.+)$", template.read_text(), re.MULTILINE)
    return []


def check_change(
    title: str, description: str, cwd: str, project_id: str = ""
) -> list[str]:
    errors = []
    if REQUIRE_GITMOJI and title and not GITMOJI_RE.match(title):
        errors.append(f"Change title must start with a gitmoji. Got: {title[:80]!r}.")
    if (
        TITLE_REQUIRES_TICKET
        and title
        and not TICKET_RE.search(title)
        and not ticket_exempt(TICKET_EXEMPT, cwd, project_id)
    ):
        errors.append(
            f"Change title must carry its ticket key, e.g. 'ABC-123 Sum token usage across calls'. "
            f"Got: {title[:80]!r}. The tracker links back through the title; the branch name alone "
            "is not enough."
        )
    if title and len(title) > MAX_TITLE:
        errors.append(
            f"Change title too long ({len(title)} chars, max {MAX_TITLE}). Shorten it."
        )
    written = user_written(description)
    if len(written) > MAX_DESCRIPTION:
        errors.append(
            f"Change description too long ({len(written)} chars, max {MAX_DESCRIPTION}). "
            "Keep it concise: user-visible impact and reasoning only, no essay, no rebase/meta "
            "narration (that belongs in a comment)."
        )
    headings = template_headings(cwd, project_id)
    if description and headings:
        missing = [h for h in headings if h.lower() not in description.lower()]
        if missing:
            errors.append(
                "Change description must follow the repo's PR/MR template. Missing sections: "
                + ", ".join(missing)
            )
    return errors


def quoted_flag(command: str, flags: str) -> str:
    match = re.search(
        rf"(?:{flags})[= ]+(?:\"([^\"]*)\"|'([^']*)')", command, re.DOTALL
    )
    return (match.group(1) or match.group(2)) if match else ""


def resolve_dir(raw: str, base: str) -> str:
    expanded = os.path.expandvars(os.path.expanduser(shlex.split(raw)[0]))
    target = pathlib.Path(base) / expanded
    return str(target) if target.is_dir() else base


def command_cwd(command: str, cwd: str, checked: re.Pattern[str]) -> str:
    for segment in re.split(r"&&|;|\|\||\n", command):
        if checked.search(segment):
            git_dir = GIT_DIR.search(segment)
            return resolve_dir(git_dir.group(1), cwd) if git_dir else cwd
        change_dir = CD_DIR.match(segment)
        if change_dir:
            cwd = resolve_dir(change_dir.group(1), cwd)
    return cwd


def check_commit(command: str, cwd: str) -> list[str]:
    errors = []
    msg_match = re.search(r"-m\s+(?:\"([^\"]+)\"|'([^']+)')", command)
    if msg_match:
        msg = msg_match.group(1) or msg_match.group(2)
        if REQUIRE_GITMOJI and not GITMOJI_RE.match(msg):
            errors.append(
                f"Commit message must start with a gitmoji (emoji or :shortcode:). Got: {msg[:80]!r}. "
                "Pick the right gitmoji for the change type and retry."
            )
        if COMMIT_FORBIDS_TICKET and COMMIT_TICKET_RE.search(msg):
            errors.append(f"Commit messages carry no ticket key. Got: {msg[:80]!r}.")
    if not precommit_installed(cwd):
        errors.append(
            "This repo has .pre-commit-config.yaml but the pre-commit git hook is not installed, so "
            "the commit would skip its checks. Run `pre-commit install`, then retry."
        )
    smells = staged_comment_smells(cwd)
    if smells:
        errors.append(
            "Staged diff contains AI-style/redundant comments. Remove or rewrite them "
            "(comments explain WHY, never WHAT), re-stage, then retry the commit:\n  - "
            + "\n  - ".join(smells)
        )
    return errors


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    tool_input = data.get("tool_input") or {}
    cwd = data.get("cwd", ".")
    command = tool_input.get("command", "")

    if data.get("tool_name") != "Bash":
        if "title" not in tool_input and "description" not in tool_input:
            sys.exit(0)
        errors = check_change(
            tool_input.get("title", ""),
            tool_input.get("description", ""),
            cwd,
            str(tool_input.get("project_id", "")),
        )
    elif CHANGE_CREATE.search(command):
        body_flags = (
            "--body|-b" if re.search(r"\bgh\s+pr\b", command) else "--description|-d"
        )
        repo = REPO_FLAG.search(command)
        errors = check_change(
            quoted_flag(command, "--title|-t"),
            quoted_flag(command, body_flags),
            command_cwd(command, cwd, CHANGE_CREATE),
            repo.group(1) if repo else "",
        )
    elif COMMIT.search(command) and not ("--amend" in command and "-m" not in command):
        errors = check_commit(command, command_cwd(command, cwd, COMMIT))
    else:
        sys.exit(0)

    if errors:
        print("\n\n".join(errors), file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
