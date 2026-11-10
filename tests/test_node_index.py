import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "lib/task_graph.py"


class NodeIndexTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.env = {
            **os.environ,
            "AGENT_NODE_INDEX": str(Path(tmp.name) / "index.json"),
        }

    def run_index(self, *args: str, stdin: str = "") -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(INDEX), *args],
            input=stdin,
            text=True,
            capture_output=True,
            env=self.env,
        )

    def test_spike_is_an_allowed_kind(self) -> None:
        self.assertIn("spike", self.run_index("kinds").stdout.split())

    def test_spike_node_records(self) -> None:
        nodes = json.dumps(
            [
                {
                    "kind": "spike",
                    "title": "try the cheap experiment",
                    "actor": "researcher",
                }
            ]
        )
        result = self.run_index("record", "--task", "task-x", stdin=nodes)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
