import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / "claude/hooks/notes-lint-guard.py"


class NotesLintGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.vault = Path(tmp.name).resolve() / "notes"
        (self.vault / "projects").mkdir(parents=True)
        self.note = self.vault / "projects/a.md"
        self.note.write_text("# a\n")

    def run_hook(self, path: Path, tool: str = "Write") -> subprocess.CompletedProcess:
        env = {**os.environ, "NOTES_DIR": str(self.vault), "PATH": "/nonexistent"}
        payload = {"tool_name": tool, "tool_input": {"file_path": str(path)}}
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
        )

    def test_missing_linter_fails_open(self) -> None:
        self.assertEqual(self.run_hook(self.note).returncode, 0)

    def test_note_outside_vault_ignored(self) -> None:
        self.assertEqual(
            self.run_hook(Path(tempfile.gettempdir()) / "x.md").returncode, 0
        )

    def test_non_edit_tool_ignored(self) -> None:
        self.assertEqual(self.run_hook(self.note, "Read").returncode, 0)


if __name__ == "__main__":
    unittest.main()
