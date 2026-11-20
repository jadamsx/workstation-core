import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / "claude/hooks/main-thread-gate.py"


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

    def run_hook(self, payload: dict, **env: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env={**self.env, **env},
        )

    def pre(self, tool: str, tool_input: dict, **extra: str) -> dict:
        return {"hook_event_name": "PreToolUse", "session_id": "s1", "tool_name": tool, "tool_input": tool_input, **extra}

    def prompt(self, text: str) -> dict:
        return {"hook_event_name": "UserPromptSubmit", "session_id": "s1", "prompt": text}

    def test_lead_edit_tools_blocked(self) -> None:
        for tool in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
            with self.subTest(tool=tool):
                self.assertEqual(self.run_hook(self.pre(tool, {"file_path": "/repo/a.py"})).returncode, 2)

    def test_agents_allowed(self) -> None:
        self.assertEqual(self.run_hook(self.pre("Agent", {"subagent_type": "builder"})).returncode, 0)

    def test_subagent_edit_allowed(self) -> None:
        payload = self.pre("Edit", {"file_path": "/repo/a.py"}, agent_id="a1")
        self.assertEqual(self.run_hook(payload).returncode, 0)

    def test_other_roles_ungated(self) -> None:
        for role in ("builder", ""):
            for tool, tin in (("Edit", {"file_path": "/repo/a.py"}), ("Bash", {"command": "git commit -m x"})):
                with self.subTest(role=role, tool=tool):
                    self.assertEqual(self.run_hook(self.pre(tool, tin), WORKSTATION_ROLE=role).returncode, 0)

    def test_role_matrix(self) -> None:
        calls = {"edit": ("Edit", {"file_path": "/repo/a.py"}), "bash": ("Bash", {"command": "git push"})}
        for role in ("lead", "work"):
            for kind, (tool, tin) in calls.items():
                with self.subTest(role=role, kind=kind):
                    blocked = self.run_hook(self.pre(tool, tin), WORKSTATION_ROLE=role)
                    self.assertEqual(blocked.returncode, 2)
                    self.assertIn(f"The {role} ", blocked.stderr)
                    self.assertIn("work tab" if role == "lead" else "builder agent", blocked.stderr)
                    self.assertEqual(self.run_hook(self.pre(tool, tin, agent_id="a1"), WORKSTATION_ROLE=role).returncode, 0)
                    self.run_hook(self.prompt("main-thread-ok"), WORKSTATION_ROLE=role)
                    lifted = self.run_hook(self.pre(tool, tin), WORKSTATION_ROLE=role).returncode
                    self.assertEqual(lifted, 0 if role == "lead" else 2)
                    self.run_hook(self.prompt("next"), WORKSTATION_ROLE=role)

    def test_bash_blocked(self) -> None:
        for cmd in (
            "git commit -m x",
            "cd r && git push origin main",
            "uv run pytest -q",
            "python3 -m unittest discover",
            "pnpm test",
            "npm run lint",
            "ruff check .",
            "make check",
            "echo hi > src/a.py",
            "echo hi >> /repo/a.txt",
            "cat > a.py <<EOF\nx\nEOF",
            "sed -i s/a/b/ f.py",
            "echo x | tee out.txt",
            "touch verify-self-pass",
            "REOPEN_REVIEW=1 foo",
        ):
            for role in ("lead", "work"):
                with self.subTest(cmd=cmd, role=role):
                    self.assertEqual(self.run_hook(self.pre("Bash", {"command": cmd}), WORKSTATION_ROLE=role).returncode, 2)

    def test_bash_allowed(self) -> None:
        for cmd in (
            "git status && git diff | head",
            "git log --oneline",
            "git worktree list",
            "rg pytest tests",
            "herdr pane list 2>&1",
            "ls > /dev/null",
            "echo x > $TMPDIR/a",
            "echo x > /tmp/a",
            "echo x > /private/tmp/claude-1/scratchpad/a",
            "echo x > /home/u/drafts/p/a.md",
            "cat <<EOF >> /home/u/notes/n.md\nx\nEOF",
            "echo x | tee /tmp/o",
        ):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.run_hook(self.pre("Bash", {"command": cmd})).returncode, 0)

    def test_notes_and_drafts_markdown_allowed(self) -> None:
        for path in ("/home/u/notes/a.md", "/home/u/drafts/p/plan.md"):
            with self.subTest(path=path):
                self.assertEqual(self.run_hook(self.pre("Write", {"file_path": path})).returncode, 0)
        self.assertEqual(self.run_hook(self.pre("Write", {"file_path": "/home/u/notes/a.py"})).returncode, 2)

    def test_escape_phrase_lifts_the_gate_for_one_turn(self) -> None:
        edit = self.pre("Edit", {"file_path": "/repo/a.py"})
        self.run_hook(self.prompt("main-thread-ok please"))
        self.assertEqual(self.run_hook(edit).returncode, 0)
        self.run_hook(self.prompt("next turn"))
        self.assertEqual(self.run_hook(edit).returncode, 2)


if __name__ == "__main__":
    unittest.main()
