import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

FAKE_HERDR = """#!/bin/sh
echo "$@" >> "$FAKE_LOG"
echo '{"result":{"workspace":{"label":"ABC-7 x","tokens":{"project":"abc-7"}}}}'
"""


class CurrentProjectTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        bindir = Path(tmp.name)
        fake = bindir / "herdr"
        fake.write_text(FAKE_HERDR)
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
        self.log = bindir / "log"
        self.env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("HERDR_WORKSPACE_ID", "WORKSTATION_PROJECT")
        }
        self.env.update(PATH=f"{bindir}:{os.environ['PATH']}", FAKE_LOG=str(self.log))

    def run_bin(self, **env: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [str(REPO / "bin/current-project")],
            env={**self.env, **env},
            capture_output=True,
            text=True,
        )

    def test_env_wins_without_asking_herdr(self) -> None:
        result = self.run_bin(WORKSTATION_PROJECT="x", HERDR_WORKSPACE_ID="w3")
        self.assertEqual(result.stdout, "x\n")
        self.assertFalse(self.log.exists())

    def test_falls_back_to_workspace_token(self) -> None:
        self.assertEqual(self.run_bin(HERDR_WORKSPACE_ID="w3").stdout, "abc-7\n")

    def test_prints_nothing_outside_herdr(self) -> None:
        result = self.run_bin()
        self.assertEqual((result.stdout, result.returncode), ("", 0))
