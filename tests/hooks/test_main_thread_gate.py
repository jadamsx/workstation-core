import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / "claude/hooks/main-thread-gate.py"


EDIT = ("Edit", {"file_path": "/repo/a.py"})
COMMIT = ("Bash", {"command": "git commit -m x"})
MARKER = 'echo "$sha $branch" > $(git rev-parse --git-dir)/verify-self-pass'
BLOCKED = (
    "git commit -m x",
    "cd r && git commit -m x",
    "uv run pytest -q",
    "python3 -m unittest discover",
    "pnpm test",
    "ruff check .",
    "/usr/bin/pytest",
    "bash -c 'git commit -m x'",
    "sh -c 'echo hi > a.py'",
    "env git commit -m x",
    "FOO=1 git commit -m x",
    "git -c x.y=z commit -m x",
    "git apply p.diff",
    'python3 -c \'open("a","w")\'',
    "perl -pi -e s/a/b/ f.py",
    "cp a b",
    "mv a b",
    "echo hi > src/a.py",
    "echo hi >> /repo/a.txt",
    "echo hi >| src/a.py",
    "echo hi > /tmp/../repo/a.py",
    "cat > a.py <<EOF\nx\nEOF",
    "sed -i s/a/b/ f.py",
    "sed -ni p f.py",
    "echo x | tee out.txt",
    "ls; touch x",
    "ls\ntouch x",
    "gh api -X DELETE /x/notes/1",
    "touch verify-self-pass",
    "echo x > $(git rev-parse --git-dir)/verify-self-pass; touch x",
)
ALLOWED = (
    "git status && git diff | head",
    "git -C /r log --oneline",
    "git worktree list",
    "git commit-tree -h",
    "rg pytest tests",
    "herdr pane list 2>&1",
    'herdr agent prompt "a > b"',
    "gh pr view 1 --json n --jq '.n>1'",
    "gh api /x",
    "gh api -X GET /x",
    "glab api --method GET /x --paginate",
    "gh pr checks 1",
    "gh pr diff 1",
    "gh run view 1 --log-failed",
    "glab ci trace",
    "glab mr diff 1",
    "FOO=1 ls",
    "sed -n 5p f",
    "ls > /dev/null",
    "echo x > $TMPDIR/a",
    "echo x > /tmp/a",
    "echo x > /private/tmp/claude-1/scratchpad/a",
    "echo x > /home/u/drafts/p/a.md",
    "cat <<EOF >> /home/u/notes/n.md\nx\nEOF",
    "echo x | tee /tmp/o",
)
ROWS = [
    (r, c, ok)
    for ok, cmds in ((False, BLOCKED), (True, ALLOWED))
    for c in cmds
    for r in ("lead", "work")
] + [
    ("lead", "git push origin x", True),
    ("lead", MARKER, True),
    ("lead", "git merge x", False),
    *(
        (r, c, r == "lead")
        for r in ("lead", "work")
        for c in (
            "gh pr merge 1",
            "glab mr merge 1",
            "gh pr comment 1 -b x",
            "gh pr review 1 -a",
            "glab mr note 1 -m x",
            "glab mr approve 1",
            "gh api -X POST /r/pulls/1/comments/notes",
            "glab api -f body=x projects/1/merge_requests/1/discussions/2/notes",
            "gh api -X PUT /repos/x/discussions/1/resolve",
        )
    ),
    ("lead", "gh api -X POST /repos/x/issues", False),
    ("work", "gh api -X POST /x", False),
    ("work", "git push origin x", False),
    ("work", MARKER, False),
    ("work", 'git merge -m "a > b" x', True),
]


class LeadGateTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.env = {
            **os.environ,
            "MAIN_THREAD_GATE_STATE": tmp.name,
            "NOTES_DIR": "/home/u/notes",
            "DRAFTS_DIR": "/home/u/drafts",
            "WORKSTATION_ROLE": "lead",
        }
        self.env.pop("HERDR_PANE_ID", None)

    def run_hook(self, payload: dict, **env: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env={**self.env, **env},
        )

    def pre(self, tool: str, tool_input: dict, **extra: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "session_id": "s1",
            "tool_name": tool,
            "tool_input": tool_input,
            **extra,
        }

    def prompt(self, text: str) -> dict:
        return {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "s1",
            "prompt": text,
        }

    def test_lead_edit_tools_blocked(self) -> None:
        for tool in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
            with self.subTest(tool=tool):
                self.assertEqual(
                    self.run_hook(
                        self.pre(tool, {"file_path": "/repo/a.py"})
                    ).returncode,
                    2,
                )

    def test_agents_allowed(self) -> None:
        self.assertEqual(
            self.run_hook(self.pre("Agent", {"subagent_type": "builder"})).returncode, 0
        )

    def test_subagent_edit_allowed(self) -> None:
        payload = self.pre("Edit", {"file_path": "/repo/a.py"}, agent_id="a1")
        self.assertEqual(self.run_hook(payload).returncode, 0)

    def test_other_roles_ungated(self) -> None:
        for role in ("builder", "free", ""):
            for tool, tin in (EDIT, COMMIT):
                with self.subTest(role=role, tool=tool):
                    self.assertEqual(
                        self.run_hook(
                            self.pre(tool, tin), WORKSTATION_ROLE=role
                        ).returncode,
                        0,
                    )

    def test_role_matrix(self) -> None:
        for role in ("lead", "work"):
            for tool, tin in (EDIT, COMMIT):
                with self.subTest(role=role, tool=tool):
                    blocked = self.run_hook(self.pre(tool, tin), WORKSTATION_ROLE=role)
                    self.assertEqual(blocked.returncode, 2)
                    self.assertIn(f"The {role} ", blocked.stderr)
                    self.assertIn(
                        "typed agent" if role == "lead" else "builder agent",
                        blocked.stderr,
                    )
                    self.assertEqual(
                        self.run_hook(
                            self.pre(tool, tin, agent_id="a1"), WORKSTATION_ROLE=role
                        ).returncode,
                        0,
                    )
                    self.run_hook(self.prompt("main-thread-ok"), WORKSTATION_ROLE=role)
                    self.assertEqual(
                        self.run_hook(
                            self.pre(tool, tin), WORKSTATION_ROLE=role
                        ).returncode,
                        0 if role == "lead" else 2,
                    )
                    self.run_hook(self.prompt("next"), WORKSTATION_ROLE=role)

    def test_bash_rules(self) -> None:
        for role, cmd, allowed in ROWS:
            with self.subTest(role=role, cmd=cmd):
                result = self.run_hook(
                    self.pre("Bash", {"command": cmd}), WORKSTATION_ROLE=role
                )
                self.assertEqual(result.returncode, 0 if allowed else 2)

    def test_unset_role_in_herdr_fails_closed(self) -> None:
        blocked = self.run_hook(
            self.pre(*COMMIT), WORKSTATION_ROLE="", HERDR_PANE_ID="1"
        )
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("WORKSTATION_ROLE=lead, work or free", blocked.stderr)
        self.assertEqual(
            self.run_hook(
                self.pre(*COMMIT), WORKSTATION_ROLE="free", HERDR_PANE_ID="1"
            ).returncode,
            0,
        )

    def test_notes_and_drafts_markdown_allowed(self) -> None:
        for path in ("/home/u/notes/a.md", "/home/u/drafts/p/plan.md"):
            with self.subTest(path=path):
                self.assertEqual(
                    self.run_hook(self.pre("Write", {"file_path": path})).returncode, 0
                )
        self.assertEqual(
            self.run_hook(
                self.pre("Write", {"file_path": "/home/u/notes/a.py"})
            ).returncode,
            2,
        )

    def test_escape_phrase_lifts_the_gate_for_one_turn(self) -> None:
        edit = self.pre("Edit", {"file_path": "/repo/a.py"})
        self.run_hook(self.prompt("main-thread-ok please"))
        self.assertEqual(self.run_hook(edit).returncode, 0)
        self.run_hook(self.prompt("next turn"))
        self.assertEqual(self.run_hook(edit).returncode, 2)


if __name__ == "__main__":
    unittest.main()
