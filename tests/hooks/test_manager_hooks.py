import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[2] / "claude/hooks"
BRIEF = Path(__file__).resolve().parents[2] / "claude/templates/manager-brief.md"
LEAD_BRIEF = Path(__file__).resolve().parents[2] / "claude/templates/lead-brief.md"


def run_hook(name: str, payload: dict, role: str | None = None) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "WORKSTATION_ROLE"}
    if role is not None:
        env["WORKSTATION_ROLE"] = role
    return subprocess.run(
        [sys.executable, str(HOOKS / name)], input=json.dumps(payload), text=True, capture_output=True, env=env
    )


class ManagerBriefInjectTest(unittest.TestCase):
    def start(self, source: str, role: str | None) -> subprocess.CompletedProcess:
        return run_hook("manager-brief-inject.py", {"source": source}, role)

    def test_compact_and_clear_return_the_brief_as_context(self) -> None:
        for source in ("compact", "clear"):
            out = json.loads(self.start(source, "work").stdout)["hookSpecificOutput"]
            self.assertEqual(out["hookEventName"], "SessionStart")
            self.assertEqual(out["additionalContext"], BRIEF.read_text())

    def test_other_sources_and_non_manager_sessions_print_nothing(self) -> None:
        self.assertEqual(self.start("startup", "work").stdout, "")
        self.assertEqual(self.start("resume", "work").stdout, "")
        self.assertEqual(self.start("compact", None).stdout, "")

    def test_lead_gets_the_lead_brief_on_every_source(self) -> None:
        for source in ("startup", "resume", "clear", "compact"):
            result = run_hook("manager-brief-inject.py", {"source": source}, role="lead")
            out = json.loads(result.stdout)["hookSpecificOutput"]
            self.assertEqual(out["additionalContext"], LEAD_BRIEF.read_text(), source)


if __name__ == "__main__":
    unittest.main()
