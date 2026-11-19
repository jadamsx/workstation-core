import json
import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_herdr_managers import REPO, ReportsCase, watch  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SESSION = "sess-1"
T0 = 1_000_000
REFUSAL = 'PreToolUse:Bash hook error: [/h/.claude/hooks/rm-guard.py]: blocked'


class StuckTests(ReportsCase):
    def setUp(self) -> None:
        super().setUp()
        self.projects = self.root.parent / "projects"
        (self.projects / "proj").mkdir(parents=True)
        patcher = mock.patch.object(watch, "PROJECTS", self.projects)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.wall = [0.0]
        self.rows: list = []
        self.folder = self.manager()
        (self.folder / "manager.json").write_text(json.dumps({"pane_id": "w1:p4", "tab_id": "w1:t4", "session_id": SESSION, "started": T0}))
        self.pane.write_text("● Looked around\n> \n  ? for shortcuts\n")
        self.status("idle")
        self.watcher = watch.Watcher(self.root, procs=lambda: self.rows, wall=lambda: self.wall[0])

    def status(self, state: str) -> None:
        os.environ["FAKE_PANES"] = f'{{"pane_id":"w1:p1","tab_id":"w1:t1"}},{{"pane_id":"w1:p4","tab_id":"w1:t4","agent":"claude","agent_status":"{state}"}}'

    def at(self, t: float, watcher: watch.Watcher | None = None) -> None:
        self.wall[0] = T0 + t
        (watcher or self.watcher).scan(t)

    def lines(self) -> list[str]:
        return [p for p in self.prompts() if "[watcher]" in p]

    def transcript(self, mtime: float, text: str = "{}", sub: bool = False) -> Path:
        path = self.projects / "proj" / (f"{SESSION}/subagents/agent-1.jsonl" if sub else f"{SESSION}.jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n")
        os.utime(path, (T0 + mtime, T0 + mtime))
        return path

    def refusals(self, at: float, n: int = 3) -> None:
        stamp = datetime.fromtimestamp(T0 + at, timezone.utc).isoformat()
        self.transcript(at, "\n".join(json.dumps({"timestamp": stamp, "content": REFUSAL}, separators=(",", ":")) for _ in range(n)))

    def test_silent_tab_is_stuck_after_stall_seconds_whatever_its_last_message_says(self) -> None:
        for message in ("● Looked around", "● WAITING: the review to finish", None):
            self.log.unlink(missing_ok=True)
            (self.root / ".watch-state.json").unlink(missing_ok=True)
            self.pane.write_text(f"{message}\n> \n" if message else "> \n")
            watcher = watch.Watcher(self.root, wall=lambda: self.wall[0])
            self.at(0, watcher)
            self.at(watch.STALL_SECONDS - 30, watcher)
            self.assertEqual(self.lines(), [], message)
            self.at(watch.STALL_SECONDS, watcher)
            self.assertEqual(self.lines(), ["agent prompt w1:p1 [watcher] alpha looks stuck: no activity for 10 min. Assume the worst and kick it."], message)

    def test_stuck_message_is_one_line_without_pane_text(self) -> None:
        self.pane.write_text("● secret screen text\n> \n  ? for shortcuts\n")
        self.at(0)
        self.at(watch.STALL_SECONDS)
        self.assertEqual(len(self.lines()), 1)
        self.assertNotIn("secret", self.log.read_text())
        self.assertNotIn("shortcuts", self.log.read_text())

    def test_working_status_does_not_hide_a_silent_tab(self) -> None:
        self.status("working")
        self.at(watch.STALL_SECONDS)
        self.assertEqual(len(self.lines()), 1)

    def test_permission_prompt_text_open_for_60_seconds_is_stuck(self) -> None:
        self.pane.write_text((FIXTURES / "pane-permission-prompt.txt").read_text())
        self.transcript(0)
        self.at(30)
        self.assertEqual(self.lines(), [])
        self.at(60)
        self.assertEqual(self.lines(), [])
        self.at(90)
        self.assertIn("permission prompt open for 60 s", self.lines()[0])

    def test_blocked_status_open_for_60_seconds_is_stuck(self) -> None:
        self.status("blocked")
        self.at(30)
        self.at(90)
        self.assertEqual(len(self.lines()), 1)

    def test_a_prompt_that_clears_restarts_the_clock(self) -> None:
        self.status("blocked")
        self.at(30)
        self.status("working")
        self.at(60)
        self.status("blocked")
        self.at(90)
        self.at(120)
        self.assertEqual(self.lines(), [])

    def test_same_guard_refusing_three_times_in_the_window_is_stuck(self) -> None:
        self.refusals(100)
        self.at(120)
        self.assertEqual(len(self.lines()), 1)
        self.assertIn("rm-guard.py refused it 3 times", self.lines()[0])

    def test_two_refusals_or_old_refusals_stay_quiet(self) -> None:
        self.refusals(100, 2)
        self.at(120)
        self.refusals(100)
        self.at(100 + watch.STALL_SECONDS + 60)
        self.assertEqual([x for x in self.lines() if "refused" in x], [])

    def test_running_shell_keeps_a_silent_tab_quiet(self) -> None:
        os.environ["FAKE_TABS"] = '{"tab_id":"w1:t4","label":"▸ alpha"}'
        os.environ["FAKE_SHELL_PID"] = "5"
        mcp = self.folder / "mcp.json"
        shell = "/bin/zsh -c source /h/.claude/shell-snapshots/s.sh && eval 'make test' < /dev/null"
        for t in range(0, 1200, 30):
            self.rows = [watch.Proc(10, 5, 5000, 50.0, f"claude --mcp-config {mcp}"), watch.Proc(20, 10, 100, t / 10, shell)]
            self.at(t)
        self.assertEqual(self.lines(), [])

    def test_subagent_transcript_activity_keeps_a_silent_tab_quiet(self) -> None:
        self.transcript(0)
        for t in range(0, 1200, 30):
            self.transcript(t, sub=True)
            self.at(t)
        self.assertEqual(self.lines(), [])

    def test_a_stall_is_reported_once_and_rearms_after_activity(self) -> None:
        self.at(watch.STALL_SECONDS)
        self.at(watch.STALL_SECONDS + 60)
        self.at(5000)
        self.assertEqual(len(self.lines()), 1)
        self.transcript(5000)
        self.at(5030)
        self.at(5000 + watch.STALL_SECONDS + 30)
        self.assertEqual(len(self.lines()), 2)

    def test_a_restart_does_not_repeat_a_reported_stall(self) -> None:
        self.at(watch.STALL_SECONDS)
        again = watch.Watcher(self.root, wall=lambda: self.wall[0])
        self.at(watch.STALL_SECONDS + 30, again)
        self.assertEqual(len(self.lines()), 1)
        state = json.loads((self.root / ".watch-state.json").read_text())["stuck"]
        self.assertEqual(list(state), ["w1:p4"])

    def test_the_idle_report_is_gone(self) -> None:
        self.assertFalse(hasattr(watch, "IDLE_SECONDS") or hasattr(watch.Watcher, "report_idle"))

    def test_lead_brief_says_to_kick_a_looks_stuck_line_and_read_status_and_bluf_first(self) -> None:
        text = (REPO / "claude/engines/agent-core.md").read_text()
        self.assertIn("`[watcher] looks stuck` line means kick the tab at once", text)
        self.assertIn("`Status` and `BLUF` lines first", text)


if __name__ == "__main__":
    unittest.main()
