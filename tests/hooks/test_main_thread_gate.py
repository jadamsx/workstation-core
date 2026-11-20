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

    def test_lead_bash_and_agents_allowed(self) -> None:
        self.assertEqual(self.run_hook(self.pre("Bash", {"command": "uv run pytest"})).returncode, 0)
        self.assertEqual(self.run_hook(self.pre("Agent", {"subagent_type": "builder"})).returncode, 0)

    def test_subagent_edit_allowed(self) -> None:
        payload = self.pre("Edit", {"file_path": "/repo/a.py"}, agent_id="a1")
        self.assertEqual(self.run_hook(payload).returncode, 0)

    def test_other_roles_may_edit(self) -> None:
        payload = self.pre("Edit", {"file_path": "/repo/a.py"})
        self.assertEqual(self.run_hook(payload, WORKSTATION_ROLE="work").returncode, 0)

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
