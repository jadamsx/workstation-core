import json
import os
import stat
import sys
import subprocess
import tempfile
import threading
import time
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
POLICY = json.loads((REPO / "claude/resource-policy.json").read_text())
sys.path.insert(0, str(REPO / "lib"))
import herdr_reports  # noqa: E402

watch = SourceFileLoader("herdr_report_watch_under_test", str(REPO / "bin/herdr-report-watch")).load_module()

FAKE_HERDR = """#!/bin/sh
echo "$@" >> "$FAKE_LOG"
case "$1 $2" in
  "workspace get") echo "{\\"result\\":{\\"workspace\\":{\\"label\\":\\"${FAKE_LABEL:-Space One}\\"}}}" ;;
  "tab create") echo '{"result":{"tab":{"tab_id":"w1:t4"},"root_pane":{"pane_id":"w1:p4"}}}' ;;
  "agent wait") if [ -e "$FAKE_WAIT_FAIL" ]; then echo "timeout" >&2; exit 1; fi; echo '{"result":{}}' ;;
  "agent start")
    n=$(cat "$FAKE_STARTS" 2>/dev/null || echo 0); echo $((n + 1)) > "$FAKE_STARTS"
    if [ "$n" -lt "${FAKE_START_BUSY:-0}" ]; then echo '{"error":{"code":"agent_pane_busy"}}' >&2; exit 1; fi
    if [ -e "$FAKE_NOT_READY" ]; then echo '{"error":{"code":"agent_not_ready","message":"agent is blocked during startup and is not ready for prompts"}}' >&2; exit 1; fi
    echo '{"result":{}}' ;;
  "tab rename"|"tab close") echo '{"result":{}}' ;;
  "agent send-keys")
    if [ -e "$FAKE_NEXT" ]; then cp "$FAKE_NEXT" "$FAKE_PANE"; rm "$FAKE_NEXT"; else cp "$FAKE_READY" "$FAKE_PANE"; fi
    echo '{"result":{}}' ;;
  "pane read")
    n=$(cat "$FAKE_READS" 2>/dev/null || echo 0); echo $((n + 1)) > "$FAKE_READS"
    if [ "$n" -ge "${FAKE_EMPTY_READS:-0}" ]; then cat "$FAKE_PANE"; fi ;;
  "workspace list") echo '{"result":{"workspaces":[{"workspace_id":"w1","label":"Space One"}]}}' ;;
  "tab list") echo "{\\"result\\":{\\"tabs\\":[$FAKE_TABS]}}" ;;
  "pane process-info")
    n=$(cat "$FAKE_PROCS" 2>/dev/null || echo 0); echo $((n + 1)) > "$FAKE_PROCS"
    if [ "$n" -lt "${FAKE_BUSY_POLLS:-0}" ]; then fg='[{"argv0":"zsh"},{"argv0":"tail"}]'; else fg='[{"argv0":"zsh"}]'; fi
    echo "{\\"result\\":{\\"process_info\\":{\\"cmdline\\":\\"$FAKE_CMDLINE\\",\\"foreground_processes\\":$fg}}}" ;;
  "pane list") panes="$FAKE_PANES"; [ -e "$FAKE_PANES_NOW" ] && panes=$(cat "$FAKE_PANES_NOW"); echo "{\\"result\\":{\\"panes\\":[$panes]}}" ;;
  "agent prompt") if [ -e "$FAKE_BLOCKED" ]; then echo "agent_blocked" >&2; exit 1; fi ;;
esac
"""


class ReportsCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        fake = base / "bin/herdr"
        fake.parent.mkdir()
        fake.write_text(FAKE_HERDR)
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
        self.log = base / "log"
        self.blocked = base / "blocked"
        self.root = base / "reports"
        self.pane = base / "pane"
        self.ready = base / "ready"
        self.ready.write_text("welcome\n> \n  ? for shortcuts\n")
        self.pane.write_text(self.ready.read_text())
        self.env = {
            **os.environ,
            "PATH": f"{fake.parent}:{os.environ['PATH']}",
            "FAKE_LOG": str(self.log),
            "FAKE_BLOCKED": str(self.blocked),
            "FAKE_PANE": str(self.pane),
            "FAKE_READY": str(self.ready),
            "FAKE_READS": str(base / "reads"),
            "FAKE_STARTS": str(base / "starts"),
            "FAKE_PROCS": str(base / "procs"),
            "FAKE_NEXT": str(base / "next-pane"),
            "SHELL": "/bin/zsh",
            "AGENT_START_RETRY_SECONDS": "0.05",
            "FAKE_WAIT_FAIL": str(base / "wait-fail"),
            "FAKE_NOT_READY": str(base / "not-ready"),
            "FAKE_PANES_NOW": str(base / "panes-now"),
            "FAKE_PANES": '{"pane_id":"w1:p1","tab_id":"w1:t1"},{"pane_id":"w1:p4","tab_id":"w1:t4","agent":"claude"}',
            "FAKE_TABS": "",
            "FAKE_CMDLINE": "claude --model sonnet --append-system-prompt-file brief.md",
            "WORKSTATION_REPORTS_ROOT": str(self.root),
            "USAGE_FILE": str(base / "usage.json"),
            "USAGE_OVERRIDE_FILE": str(base / "usage-override"),
            "HERDR_WORKSPACE_ID": "w1",
            "HERDR_PANE_ID": "w1:p1",
        }
        patcher = mock.patch.dict(os.environ, self.env)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.space = self.root / "space-one"

    def calls(self) -> list[str]:
        return self.log.read_text().splitlines() if self.log.exists() else []

    def prompts(self) -> list[str]:
        return [c for c in self.calls() if c.startswith("agent prompt")]

    def manager(self, name: str = "alpha", pane: str = "w1:p4") -> Path:
        folder = self.space / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "manager.json").write_text(json.dumps({"pane_id": pane, "tab_id": "w1:t4"}))
        (self.space / "coordinator").write_text("w1:p1\n")
        return folder

    def bin(self, script: str, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([str(REPO / "bin" / script), *args], capture_output=True, text=True)

class WatcherTests(ReportsCase):
    def test_new_result_is_sent_once_across_passes_and_restarts(self) -> None:
        result = self.manager() / "result-1.md"
        result.write_text("Done")
        watch.Watcher(self.root).scan(0)
        watch.Watcher(self.root).scan(100)
        self.assertEqual(self.prompts(), [f"agent prompt w1:p1 [worker-report] {result}"])

    def test_oddly_named_report_is_delivered_once_and_leaves_the_tab_open(self) -> None:
        result = self.manager() / "2026-11-18-1.md"
        result.write_text("no status line")
        watch.Watcher(self.root).scan(0)
        watch.Watcher(self.root).scan(100)
        self.assertEqual(self.prompts(), [f"agent prompt w1:p1 [worker-report] {result}"])
        self.assertNotIn("tab close w1:t4", self.calls())

    def test_blocked_coordinator_is_retried_after_15_seconds_then_sent_once(self) -> None:
        self.manager().joinpath("result-1.md").write_text("Done")
        self.blocked.touch()
        watcher = watch.Watcher(self.root)
        watcher.scan(0)
        watcher.scan(5)
        self.assertEqual(len(self.prompts()), 1)
        watcher.scan(15)
        self.assertEqual(len(self.prompts()), 2)
        self.blocked.unlink()
        watcher.scan(30)
        watcher.scan(60)
        self.assertEqual(len(self.prompts()), 3)

    def test_vanished_manager_without_results_gets_one_exited_line(self) -> None:
        self.manager()
        os.environ["FAKE_PANES"] = '{"pane_id":"w1:p1"}'
        watcher = watch.Watcher(self.root)
        watcher.scan(0)
        watcher.scan(100)
        self.assertEqual(self.prompts(), ["agent prompt w1:p1 [worker-report] alpha exited without a report"])

    def test_live_manager_and_unreachable_herdr_send_no_exited_line(self) -> None:
        self.manager()
        watch.Watcher(self.root).scan(0)
        os.environ["PATH"] = "/usr/bin:/bin"
        watch.Watcher(self.root).scan(100)
        self.assertEqual(self.prompts(), [])

    def test_unsent_result_is_delivered_before_any_exited_line(self) -> None:
        self.manager().joinpath("result-1.md").write_text("Done")
        os.environ["FAKE_PANES"] = ""
        self.blocked.touch()
        watcher = watch.Watcher(self.root)
        watcher.scan(0)
        self.assertNotIn("exited", " ".join(self.prompts()))

    def test_missing_coordinator_sends_nothing_and_keeps_the_result_pending(self) -> None:
        folder = self.manager()
        (self.space / "coordinator").unlink()
        (folder / "result-1.md").write_text("Done")
        watcher = watch.Watcher(self.root)
        watcher.scan(0)
        self.assertEqual(self.prompts(), [])
        (self.space / "coordinator").write_text("w1:p9\n")
        watcher.scan(20)
        self.assertEqual(self.prompts(), [f"agent prompt w1:p9 [worker-report] {folder / 'result-1.md'}"])


class ParkedResumeTests(ReportsCase):
    def park(self, *jobs: tuple[str, str, float]) -> None:
        panes = ['{"pane_id":"w1:p1"}']
        (self.root / ".parked").mkdir(parents=True, exist_ok=True)
        for i, (name, text, until) in enumerate(jobs):
            if name != "ghost":
                self.manager(name, f"w1:p{4 + len(name)}")
                panes.append(f'{{"pane_id":"w1:p{4 + len(name)}"}}')
            (self.root / ".parked" / f"{i:03}.json").write_text(json.dumps({"folder": str(self.space / name), "text": text, "until": until}))
        os.environ["FAKE_PANES"] = ",".join(panes)

    def left(self) -> list[str]:
        return [Path(json.loads(f.read_text())["folder"]).name for f in sorted((self.root / ".parked").glob("*.json"))]

    def usage(self, five: float, reset: float) -> None:
        Path(os.environ["USAGE_FILE"]).write_text(json.dumps({"five_hour": {"used_percentage": five, "resets_at": reset}}))

    def test_resumes_jobs_in_order_with_one_line_per_lead_once_usage_is_under(self) -> None:
        now = time.time()
        self.park(("alpha", "/plan-task a", now + 3600), ("beta", "/plan-task b", now + 3600))
        self.usage(95, now + 3600)
        watcher = watch.Watcher(self.root)
        watcher.scan(0)
        self.assertEqual(self.prompts(), [])
        self.usage(5, now + 9000)
        watcher.scan(1)
        watcher.scan(2)
        self.assertEqual(
            self.prompts(),
            [
                "agent prompt w1:p9 [coordinator] /plan-task a",
                "agent prompt w1:p8 [coordinator] /plan-task b",
                "agent prompt w1:p1 [worker-report] resumed parked jobs: alpha, beta",
            ],
        )
        self.assertEqual(self.left(), [])

    def test_an_override_releases_parked_jobs(self) -> None:
        now = time.time()
        self.park(("alpha", "/plan-task a", now + 3600))
        self.usage(95, now + 3600)
        watcher = watch.Watcher(self.root)
        watcher.scan(0)
        self.assertEqual(self.left(), ["alpha"])
        Path(os.environ["USAGE_OVERRIDE_FILE"]).write_text(str(now + 600))
        watcher.scan(1)
        self.assertEqual(self.left(), [])

    def test_a_poison_job_is_dropped_and_the_rest_still_resume(self) -> None:
        self.park(("ghost", "/plan-task g", 0), ("alpha", "/plan-task a", 0))
        watch.Watcher(self.root).scan(0)
        self.assertEqual(self.left(), [])
        self.assertIn("agent prompt w1:p9 [coordinator] /plan-task a", self.prompts())

    def test_a_malformed_parked_file_is_dropped(self) -> None:
        (self.root / ".parked").mkdir(parents=True)
        (self.root / ".parked" / "000.json").write_text("[1]")
        watch.Watcher(self.root).scan(0)
        self.assertEqual(list((self.root / ".parked").glob("*.json")), [])

    def test_a_busy_standing_manager_keeps_its_job_parked(self) -> None:
        folder = self.manager()
        (folder / "manager.json").write_text(json.dumps({"pane_id": "w1:p4", "tab_id": "w1:t4", "standing": True}))
        os.environ["FAKE_PANES"] = '{"pane_id":"w1:p1"},{"pane_id":"w1:p4","agent_status":"working"}'
        (self.root / ".parked").mkdir()
        (self.root / ".parked" / "000.json").write_text(json.dumps({"folder": str(folder), "text": "/plan-task a", "until": 0}))
        watch.Watcher(self.root).scan(0)
        self.assertEqual((self.left(), self.prompts()), (["alpha"], []))

    def test_a_busy_manager_does_not_block_the_jobs_after_it(self) -> None:
        self.park(("alpha", "/plan-task a", 0), ("beta", "/plan-task b", 0))
        folder = self.space / "alpha"
        (folder / "manager.json").write_text(json.dumps({"pane_id": "w1:p9", "tab_id": "w1:t9", "standing": True}))
        os.environ["FAKE_PANES"] = '{"pane_id":"w1:p1"},{"pane_id":"w1:p9","agent_status":"working"},{"pane_id":"w1:p8"}'
        watch.Watcher(self.root).scan(0)
        self.assertEqual(self.left(), ["alpha"])
        self.assertIn("agent prompt w1:p8 [coordinator] /plan-task b", self.prompts())


class DoneReportTests(ReportsCase):
    def test_done_report_is_delivered_then_closes_the_tab_and_silences_the_exited_line(self) -> None:
        folder = self.manager()
        (folder / "result-1.md").write_text("Status: done\nchanged x\n")
        watcher = watch.Watcher(self.root)
        watcher.scan(0)
        self.assertEqual(len(self.prompts()), 1)
        self.assertIn("tab close w1:t4", self.calls())
        self.assertTrue(json.loads((folder / "manager.json").read_text())["closed"])
        os.environ["FAKE_PANES"] = '{"pane_id":"w1:p1","tab_id":"w1:t1"}'
        watcher.scan(100)
        self.assertEqual(len(self.prompts()), 1)

    def standing(self, name: str = "alpha") -> Path:
        folder = self.manager(name)
        (folder / "manager.json").write_text(json.dumps({"pane_id": "w1:p4", "tab_id": "w1:t4", "standing": True}))
        return folder

    def test_standing_done_report_clears_the_tab_once_and_never_closes_it(self) -> None:
        folder = self.standing()
        (folder / "result-1.md").write_text("Status: done\nchanged x\n")
        os.environ["FAKE_PANES"] = '{"pane_id":"w1:p4","tab_id":"w1:t4","agent_status":"idle"}'
        watcher = watch.Watcher(self.root)
        watcher.scan(0)
        watch.Watcher(self.root).scan(100)
        self.assertEqual(self.prompts(), [f"agent prompt w1:p1 [worker-report] {folder / 'result-1.md'}", "agent prompt w1:p4 /clear"])
        self.assertNotIn("tab close w1:t4", self.calls())
        self.assertNotIn("closed", json.loads((folder / "manager.json").read_text()))

    def test_standing_tab_is_cleared_only_once_it_is_idle_and_again_after_the_next_done_report(self) -> None:
        folder = self.standing()
        (folder / "result-1.md").write_text("Status: done\nx\n")
        os.environ["FAKE_PANES"] = '{"pane_id":"w1:p4","tab_id":"w1:t4","agent_status":"working"}'
        watcher = watch.Watcher(self.root)
        watcher.scan(0)
        self.assertNotIn("agent prompt w1:p4 /clear", self.prompts())
        os.environ["FAKE_PANES"] = '{"pane_id":"w1:p4","tab_id":"w1:t4","agent_status":"idle"}'
        watcher.scan(5)
        (folder / "result-2.md").write_text("Status: done\ny\n")
        watcher.scan(10)
        self.assertEqual(self.prompts().count("agent prompt w1:p4 /clear"), 2)

    def test_standing_decision_report_is_not_cleared(self) -> None:
        folder = self.standing()
        (folder / "result-1.md").write_text("Status: decision\nwhich?\n")
        watch.Watcher(self.root).scan(0)
        self.assertNotIn("agent prompt w1:p4 /clear", self.prompts())

    def test_non_standing_done_report_still_closes_and_is_not_cleared(self) -> None:
        folder = self.manager()
        (folder / "result-1.md").write_text("Status: done\nx\n")
        watch.Watcher(self.root).scan(0)
        self.assertIn("tab close w1:t4", self.calls())
        self.assertNotIn("agent prompt w1:p4 /clear", self.prompts())

    def test_manager_close_refuses_a_standing_manager_unless_forced(self) -> None:
        folder = self.standing()
        self.assertEqual(self.bin("manager-close", "alpha").returncode, 2)
        self.assertNotIn("tab close w1:t4", self.calls())
        self.assertEqual(self.bin("manager-close", "alpha", "--force").returncode, 0)
        self.assertIn("tab close w1:t4", self.calls())
        self.assertTrue(json.loads((folder / "manager.json").read_text())["closed"])

    def kept(self, name: str = "alpha") -> Path:
        folder = self.manager(name)
        (folder / "manager.json").write_text(json.dumps({"pane_id": "w1:p4", "tab_id": "w1:t4", "keep": True}))
        return folder

    def test_kept_done_report_is_delivered_but_never_closes_or_clears(self) -> None:
        folder = self.kept()
        (folder / "result-1.md").write_text("Status: done\nx\n")
        os.environ["FAKE_PANES"] = '{"pane_id":"w1:p4","tab_id":"w1:t4","agent_status":"idle"}'
        watcher = watch.Watcher(self.root)
        watcher.scan(0)
        watcher.scan(100)
        self.assertEqual(self.prompts(), [f"agent prompt w1:p1 [worker-report] {folder / 'result-1.md'}"])
        self.assertNotIn("tab close w1:t4", self.calls())
        self.assertNotIn("closed", json.loads((folder / "manager.json").read_text()))

    def test_manager_close_refuses_a_kept_manager_unless_forced(self) -> None:
        self.kept()
        self.assertEqual(self.bin("manager-close", "alpha").returncode, 2)
        self.assertNotIn("tab close w1:t4", self.calls())
        self.assertEqual(self.bin("manager-close", "alpha", "--force").returncode, 0)
        self.assertIn("tab close w1:t4", self.calls())

    def test_restarted_manager_is_not_closed_by_a_done_report_from_before_its_start(self) -> None:
        folder = self.manager()
        old = folder / "result-1.md"
        old.write_text("Status: done\nx\n")
        os.utime(old, (100, 100))
        (folder / "manager.json").write_text(json.dumps({"pane_id": "w1:p4", "tab_id": "w1:t4", "started": 200}))
        watch.Watcher(self.root).scan(0)
        self.assertNotIn("tab close w1:t4", self.calls())
        (folder / "result-2.md").write_text("Status: done\ny\n")
        watch.Watcher(self.root).scan(1)
        self.assertIn("tab close w1:t4", self.calls())

    def test_decision_report_keeps_the_tab_open(self) -> None:
        folder = self.manager()
        (folder / "result-1.md").write_text("Status: decision\nwhich one?\n")
        watch.Watcher(self.root).scan(0)
        self.assertEqual(len(self.prompts()), 1)
        self.assertNotIn("tab close w1:t4", self.calls())
        self.assertNotIn("closed", json.loads((folder / "manager.json").read_text()))


class ManagerTests(ReportsCase):
    def test_register_saves_this_pane_and_rerun_replaces_it(self) -> None:
        self.assertEqual(self.bin("herdr-manager", "register").returncode, 0)
        os.environ["HERDR_PANE_ID"] = "w1:p8"
        self.bin("herdr-manager", "register")
        self.assertEqual((self.space / "coordinator").read_text().strip(), "w1:p8")

    def test_register_renames_the_coordinator_tab_to_lead(self) -> None:
        self.bin("herdr-manager", "register")
        self.assertIn("tab rename w1:t1 ◆ lead", self.calls())

    def test_check_is_true_for_the_coordinator_pane_only(self) -> None:
        self.bin("herdr-manager", "register")
        mine = self.bin("manager-start", "--check")
        self.assertEqual((mine.returncode, mine.stdout.strip()), (0, "coordinator"))
        os.environ["HERDR_PANE_ID"] = "w1:p4"
        self.assertEqual(self.bin("manager-start", "--check").returncode, 1)
        del os.environ["HERDR_PANE_ID"]
        self.assertEqual(self.bin("manager-start", "--check").returncode, 1)

    def test_manager_start_submits_the_prompt_only_after_the_agent_is_ready(self) -> None:
        r = self.bin("manager-start", "beta", "--prompt", "do the thing", "--dir", "/tmp")
        self.assertEqual(r.returncode, 0, r.stderr)
        calls = self.calls()
        wait = calls.index("agent wait w1:p4 --until idle --timeout 120000")
        self.assertGreater(calls.index("agent prompt w1:p4 do the thing"), wait)
        self.assertGreater(wait, next(i for i, c in enumerate(calls) if c.startswith("agent start")))

    def test_manager_send_prefixes_the_text_and_retries_while_blocked(self) -> None:
        self.manager()
        self.blocked.touch()
        os.environ["MANAGER_SEND_RETRY_SECONDS"] = "0.1"
        threading.Timer(0.5, self.blocked.unlink).start()
        r = self.bin("manager-send", "alpha", "OK to push")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertGreater(len(self.prompts()), 1)
        self.assertEqual(self.prompts()[-1], "agent prompt w1:p4 [coordinator] OK to push")

    def usage(self, five: float, reset: float) -> None:
        Path(os.environ["USAGE_FILE"]).write_text(json.dumps({"five_hour": {"used_percentage": five, "resets_at": reset}}))

    def test_a_slash_job_over_the_usage_limit_is_parked_with_one_line_and_not_sent(self) -> None:
        folder = self.manager()
        self.usage(90, time.time() + 3600)
        r = self.bin("manager-send", "alpha", "/build plan.md node N1 worktree /tmp")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.usage(90, time.time() + 3600)
        r = self.bin("manager-send", "alpha", "/plan-task x")
        self.assertEqual((r.returncode, r.stdout.count("\n"), r.stdout.startswith("parked until ")), (0, 1, True))
        self.assertEqual(self.prompts(), [])
        parked = [json.loads(f.read_text()) for f in sorted((self.root / ".parked").glob("*.json"))]
        self.assertEqual([(p["folder"], p["text"]) for p in parked], [(str(folder), "/plan-task x")])
        self.assertEqual(self.bin("manager-send", "alpha", "OK to push").returncode, 0)
        self.assertEqual(self.prompts(), ["agent prompt w1:p4 [coordinator] OK to push"])

    def test_concurrent_parks_keep_every_job(self) -> None:
        self.manager()
        self.usage(90, time.time() + 3600)
        procs = [
            subprocess.Popen([str(REPO / "bin/manager-send"), "alpha", f"/plan-task {n}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for n in range(12)
        ]
        results = [(p.wait(), p.stderr.read()) for p in procs]
        self.assertEqual(results, [(0, "")] * 12)
        texts = {json.loads(f.read_text())["text"] for f in (self.root / ".parked").glob("*.json")}
        self.assertEqual(texts, {f"/plan-task {n}" for n in range(12)})

    def test_the_override_lifts_the_park(self) -> None:
        self.manager()
        self.usage(90, time.time() + 3600)
        os.environ["USAGE_GATE"] = "off"
        self.addCleanup(os.environ.pop, "USAGE_GATE", None)
        self.assertEqual(self.bin("manager-send", "alpha", "/plan-task x").returncode, 0)
        self.assertEqual(self.prompts(), ["agent prompt w1:p4 [coordinator] /plan-task x"])

    def standing_send(self, status: str, keep: bool = False, standing: bool = True) -> Path:
        folder = self.manager()
        (folder / "manager.json").write_text(json.dumps({"pane_id": "w1:p4", "tab_id": "w1:t4", "standing": standing, **({"keep": True} if keep else {})}))
        os.environ["FAKE_PANES"] = f'{{"pane_id":"w1:p4","tab_id":"w1:t4","agent_status":"{status}"}}'
        os.environ["MANAGER_SEND_RETRY_SECONDS"] = "0.1"
        return folder

    def test_send_to_a_working_standing_manager_waits_until_idle(self) -> None:
        self.standing_send("working")
        idle = '{"pane_id":"w1:p4","tab_id":"w1:t4","agent_status":"idle"}'
        threading.Timer(0.5, Path(os.environ["FAKE_PANES_NOW"]).write_text, [idle]).start()
        r = self.bin("manager-send", "alpha", "go")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.prompts(), ["agent prompt w1:p4 [coordinator] go"])
        self.assertGreater(len([c for c in self.calls() if c == "pane list"]), 1)

    def test_send_to_a_done_uncleared_standing_manager_clears_first_and_records_it(self) -> None:
        folder = self.standing_send("idle")
        (folder / "result-1.md").write_text("\nStatus: done\nx\n")
        r = self.bin("manager-send", "alpha", "go")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.prompts(), ["agent prompt w1:p4 /clear", "agent prompt w1:p4 [coordinator] go"])
        self.assertEqual(json.loads((self.root / ".watch-state.json").read_text())["cleared"], [str(folder / "result-1.md")])
        watch.Watcher(self.root).scan(0)
        self.assertEqual(self.prompts().count("agent prompt w1:p4 /clear"), 1)

    def test_send_to_a_kept_or_non_standing_manager_does_not_wait_or_clear(self) -> None:
        for keep, standing in ((True, True), (False, False)):
            folder = self.standing_send("working", keep=keep, standing=standing)
            (folder / "result-1.md").write_text("Status: done\nx\n")
            self.log.unlink(missing_ok=True)
            self.assertEqual(self.bin("manager-send", "alpha", "go").returncode, 0)
            self.assertEqual(self.prompts(), ["agent prompt w1:p4 [coordinator] go"])

    def test_send_to_a_standing_manager_with_a_dead_pane_fails(self) -> None:
        self.standing_send("idle")
        os.environ["FAKE_PANES"] = '{"pane_id":"w1:p9","tab_id":"w1:t9"}'
        r = self.bin("manager-send", "alpha", "go")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.prompts(), [])

    def test_start_refuses_a_live_unclosed_manager(self) -> None:
        self.manager()
        r = self.bin("herdr-manager", "start", "alpha", "--dir", "/tmp")
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn("tab create", " ".join(self.calls()))

    def test_done_report_close_is_retried_after_a_failed_close(self) -> None:
        folder = self.manager()
        (folder / "result-1.md").write_text("\n\nStatus: done\nx\n")
        with mock.patch.object(watch, "close_manager", side_effect=watch.ReportsError("down")):
            watch.Watcher(self.root).scan(0)
        watch.Watcher(self.root).scan(1)
        self.assertTrue(json.loads((folder / "manager.json").read_text())["closed"])

    def test_close_manager_with_herdr_unreachable_does_not_mark_closed(self) -> None:
        folder = self.manager()
        with mock.patch.object(herdr_reports, "herdr", side_effect=subprocess.CalledProcessError(1, "herdr")), \
                mock.patch.object(herdr_reports, "live_panes", return_value=None):
            with self.assertRaises(herdr_reports.ReportsError):
                herdr_reports.close_manager(folder)
        self.assertNotIn("closed", json.loads((folder / "manager.json").read_text()))

    def test_manager_close_closes_the_tab_and_marks_it_closed(self) -> None:
        folder = self.manager()
        self.assertEqual(self.bin("manager-close", "alpha").returncode, 0)
        self.assertIn("tab close w1:t4", self.calls())
        self.assertTrue(json.loads((folder / "manager.json").read_text())["closed"])

    def test_restart_preserves_keep_and_standing_from_the_old_manager_json(self) -> None:
        folder = self.manager()
        (folder / "manager.json").write_text(json.dumps({"pane_id": "w1:p9", "tab_id": "w1:t9", "closed": True, "keep": True, "standing": True}))
        r = self.bin("manager-start", "alpha", "--prompt", "go", "--dir", "/tmp")
        self.assertEqual(r.returncode, 0, r.stderr)
        info = json.loads((folder / "manager.json").read_text())
        self.assertTrue(info["keep"] and info["standing"])
        self.assertNotIn("closed", info)

    def test_keep_sets_and_off_clears_the_flag(self) -> None:
        folder = self.manager()
        self.assertEqual(self.bin("herdr-manager", "keep", "alpha").returncode, 0)
        self.assertTrue(json.loads((folder / "manager.json").read_text())["keep"])
        self.assertEqual(self.bin("herdr-manager", "keep", "alpha", "--off").returncode, 0)
        self.assertNotIn("keep", json.loads((folder / "manager.json").read_text()))
        self.assertEqual(self.bin("herdr-manager", "keep", "nope").returncode, 2)

    def bin_setup(self, *flags: str) -> subprocess.CompletedProcess:
        return subprocess.run([str(REPO / "bin/herdr-manager"), "setup", *flags], capture_output=True, text=True, cwd=self.root.parent)

    def setup_run(self, cwd: Path | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([str(REPO / "bin/herdr-manager"), "setup"], capture_output=True, text=True, cwd=cwd or self.root.parent)

    def creates(self) -> list[str]:
        return [c for c in self.calls() if c.startswith("tab create")]

    def test_setup_registers_the_lead_and_creates_a_standing_work_tab_and_an_ask_tab(self) -> None:
        r = self.setup_run()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((self.space / "coordinator").read_text().strip(), "w1:p1")
        self.assertIn("tab rename w1:t1 ◆ lead", self.calls())
        work, ask = self.creates()
        self.assertIn(f"--cwd {self.root.parent.resolve()} --label ▸ work --env WORKSTATION_REPORTS={self.space / 'work'}", work)
        self.assertIn("--label ? ask --env WORKSTATION_ROLE=ask --env DISABLE_AUTO_UPDATE=true --env DISABLE_UPDATE_PROMPT=true", ask)
        starts = [c for c in self.calls() if c.startswith("agent start")]
        self.assertIn("-- --model sonnet --strict-mcp-config --mcp-config", starts[0])
        self.assertIn("-- --model haiku --strict-mcp-config --mcp-config", starts[1])
        self.assertIn("--append-system-prompt-file", starts[1])
        self.assertEqual(self.started_servers(starts[1]), set(POLICY["roles"]["ask"]))
        self.assertTrue(starts[1].endswith("ask-brief.md"))
        self.assertTrue(json.loads((self.space / "work/manager.json").read_text())["standing"])

    def test_ask_role_refuses_any_mcp_server(self) -> None:
        manager = SourceFileLoader("herdr_manager_under_test", str(REPO / "bin/herdr-manager")).load_module()
        self.root.mkdir(parents=True, exist_ok=True)
        policy, catalog = self.root / "policy.json", self.root / "mcp.json"
        policy.write_text(json.dumps({"roles": {"ask": ["x"]}}))
        catalog.write_text(json.dumps({"mcpServers": {"x": {}}}))
        with mock.patch.object(manager, "POLICY", policy), mock.patch.object(manager, "MCP_SERVERS", catalog):
            with self.assertRaises(herdr_reports.ReportsError):
                manager.mcp_args("ask", self.root / "ask")

    def test_setup_in_two_spaces_passes_distinct_agent_names(self) -> None:
        self.setup_run()
        os.environ["FAKE_LABEL"] = "Space Two"
        os.environ["FAKE_PANES"] = '{"pane_id":"w1:p1","tab_id":"w1:t1"}'
        self.setup_run()
        names = [c.split()[2] for c in self.calls() if c.startswith("agent start")]
        self.assertEqual(names, ["work-space-one", "ask-space-one", "work-space-two", "ask-space-two"])

    def test_setup_twice_changes_nothing(self) -> None:
        self.setup_run()
        os.environ["FAKE_TABS"] = '{"tab_id":"w1:t4","label":"? ask"}'
        before = len(self.creates())
        r = self.setup_run()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(self.creates()), before)

    def test_setup_brings_back_only_the_missing_tab(self) -> None:
        self.setup_run()
        os.environ["FAKE_TABS"] = '{"tab_id":"w1:t4","label":"? ask"}'
        os.environ["FAKE_PANES"] = '{"pane_id":"w1:p1","tab_id":"w1:t1"}'
        self.setup_run()
        self.assertEqual(len(self.creates()), 3)
        self.assertIn("--label ▸ work", self.creates()[-1])
        os.environ["FAKE_TABS"] = ""
        os.environ["FAKE_PANES"] = '{"pane_id":"w1:p1","tab_id":"w1:t1"},{"pane_id":"w1:p4","tab_id":"w1:t4"}'
        self.setup_run()
        self.assertEqual(len(self.creates()), 4)
        self.assertIn("--label ? ask", self.creates()[-1])

    def test_setup_no_work_skips_work_keeps_ask_and_is_remembered_until_work_flag(self) -> None:
        r = self.bin_setup("--no-work")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads((self.space / "setup.json").read_text()), {"work": False})
        self.assertEqual(len(self.creates()), 1)
        self.assertIn("--label ? ask", self.creates()[0])
        self.assertFalse((self.space / "work").exists())
        os.environ["FAKE_TABS"] = '{"tab_id":"w1:t4","label":"? ask"}'
        self.setup_run()
        self.assertEqual(len(self.creates()), 1)
        r = self.bin_setup("--work")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads((self.space / "setup.json").read_text()), {"work": True})
        self.assertEqual(len(self.creates()), 2)
        self.assertIn("--label ▸ work", self.creates()[-1])

    def test_setup_with_corrupt_setup_json_fails(self) -> None:
        self.space.mkdir(parents=True, exist_ok=True)
        (self.space / "setup.json").write_text("{")
        self.assertEqual(self.setup_run().returncode, 2)

    def started_servers(self, start: str) -> set[str]:
        return set(json.loads(Path(start.split("--mcp-config ")[1].split()[0]).read_text())["mcpServers"])

    def test_work_and_named_managers_start_only_their_policy_servers(self) -> None:
        self.setup_run()
        self.bin("herdr-manager", "start", "alpha", "--dir", "/tmp")
        work, _, alpha = [c for c in self.calls() if c.startswith("agent start")]
        self.assertEqual(self.started_servers(work), set(POLICY["roles"]["work"]))
        self.assertEqual(self.started_servers(alpha), set(POLICY["roles"]["manager"]))

    def start_with_policy(self, text: str | None) -> subprocess.CompletedProcess:
        loader = SourceFileLoader("herdr_manager_policy", str(REPO / "bin/herdr-manager"))
        module = loader.load_module()
        policy = self.root / "policy.json"
        if text is not None:
            policy.write_text(text)
        with mock.patch.object(module, "POLICY", policy):
            return module.main(["start", "alpha", "--dir", "/tmp"])

    def test_start_fails_naming_file_and_role_for_a_bad_policy(self) -> None:
        for text in (None, "{", '{"roles": {}}'):
            with self.subTest(text=text), mock.patch("sys.stderr") as err:
                self.assertEqual(self.start_with_policy(text), 2)
                shown = "".join(c.args[0] for c in err.write.call_args_list)
                self.assertIn("policy.json", shown)
                self.assertIn("'manager'", shown)

    def test_start_opens_a_sonnet_tab_with_the_brief_and_records_it(self) -> None:
        r = self.bin("herdr-manager", "start", "alpha", "--resume", "0a1b2c3d-0000-4000-8000-000000000001", "--dir", "/tmp")
        self.assertEqual(r.returncode, 0, r.stderr)
        tab = next(c for c in self.calls() if c.startswith("tab create"))
        self.assertIn(f"--label ▸ alpha --env WORKSTATION_REPORTS={self.space / 'alpha'}", tab)
        self.assertIn("--env DISABLE_AUTO_UPDATE=true", tab)
        start = next(c for c in self.calls() if c.startswith("agent start"))
        self.assertIn("agent start alpha-space-one --kind claude --pane w1:p4 -- --model sonnet --resume 0a1b2c3d", start)
        self.assertIn("--append-system-prompt-file", start)
        self.assertTrue((REPO / "claude/templates/manager-brief.md").exists())
        self.assertEqual(json.loads((self.space / "alpha/manager.json").read_text())["pane_id"], "w1:p4")

    def trust_dialog(self) -> None:
        self.pane.write_text(f"Quick safety check\n{herdr_reports.TRUST_DIALOG}\n❯ 1. Yes, I trust this folder\n  2. No, exit\n")

    def real_trust_dialog(self) -> None:
        self.pane.write_text(
            f"Quick safety check: {herdr_reports.TRUST_DIALOG}\n ❯ No, exit\n   Yes, I trust this folder\n Enter to confirm · Esc to cancel\n"
        )

    def start_in(self, directory: Path, cwd: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [str(REPO / "bin/herdr-manager"), "start", "beta", "--dir", str(directory)], capture_output=True, text=True, cwd=cwd,
        )

    def process_polls(self) -> list[str]:
        return [c for c in self.calls() if c.startswith("pane process-info")]

    def test_start_waits_until_the_shell_is_the_only_foreground_process(self) -> None:
        os.environ["FAKE_BUSY_POLLS"] = "3"
        self.assertEqual(self.bin("herdr-manager", "start", "beta", "--dir", "/tmp").returncode, 0)
        calls = self.calls()
        first_start = next(i for i, c in enumerate(calls) if c.startswith("agent start"))
        self.assertEqual(len([c for c in calls[:first_start] if c.startswith("pane process-info")]), 4)

    def test_wait_for_shell_gives_up_while_the_pane_stays_busy(self) -> None:
        os.environ["FAKE_BUSY_POLLS"] = "999"
        self.assertFalse(herdr_reports.wait_for_shell("w1:p4", 0.3, 0.1))
        self.assertTrue(len(self.process_polls()) >= 2)

    def test_agent_start_is_retried_while_the_pane_is_busy(self) -> None:
        os.environ["FAKE_START_BUSY"] = "3"
        r = self.bin("herdr-manager", "start", "beta", "--dir", "/tmp")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len([c for c in self.calls() if c.startswith("agent start")]), 4)
        self.assertTrue((self.space / "beta/manager.json").exists())

    def test_agent_start_gives_up_after_three_retries_and_closes_the_tab(self) -> None:
        os.environ["FAKE_START_BUSY"] = "9"
        r = self.bin("herdr-manager", "start", "beta", "--dir", "/tmp")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(len([c for c in self.calls() if c.startswith("agent start")]), 4)
        self.assertIn("tab close w1:t4", self.calls())

    def test_trust_dialog_inside_the_callers_directory_is_accepted(self) -> None:
        self.trust_dialog()
        inside = Path(tempfile.mkdtemp(dir=self.root.parent))
        self.addCleanup(inside.rmdir)
        r = self.start_in(inside, self.root.parent)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("agent send-keys w1:p4 Enter", self.calls())

    def test_trust_dialog_outside_the_callers_directory_is_refused_and_closes_the_tab(self) -> None:
        self.trust_dialog()
        elsewhere = Path(tempfile.mkdtemp(dir=self.root.parent))
        self.addCleanup(elsewhere.rmdir)
        r = self.start_in(elsewhere, REPO)
        self.assertEqual(r.returncode, 2)
        self.assertIn(str(elsewhere.resolve()), r.stderr)
        self.assertNotIn("agent send-keys", " ".join(self.calls()))
        self.assertIn("tab close w1:t4", self.calls())
        self.assertFalse((self.space / "beta/manager.json").exists())

    def test_blocked_start_with_the_trust_dialog_visible_sends_down_enter_and_records_the_manager(self) -> None:
        (self.root.parent / "not-ready").write_text("")
        self.real_trust_dialog()
        inside = Path(tempfile.mkdtemp(dir=self.root.parent))
        self.addCleanup(inside.rmdir)
        r = self.start_in(inside, self.root.parent)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len([c for c in self.calls() if c.startswith("agent start")]), 1)
        self.assertIn("agent send-keys w1:p4 Down Enter", self.calls())
        self.assertTrue((self.space / "beta/manager.json").exists())

    def test_trust_then_imports_dialog_are_both_answered_and_records_the_manager(self) -> None:
        self.trust_dialog()
        (self.root.parent / "next-pane").write_text(
            "Allow external CLAUDE.md file imports?\n ❯ No, disable external imports\n   Yes, allow external imports\n Enter to confirm · Esc to cancel\n"
        )
        inside = Path(tempfile.mkdtemp(dir=self.root.parent))
        self.addCleanup(inside.rmdir)
        r = self.start_in(inside, self.root.parent)
        self.assertEqual(r.returncode, 0, r.stderr)
        sent = [c for c in self.calls() if c.startswith("agent send-keys")]
        self.assertEqual(sent, ["agent send-keys w1:p4 Enter", "agent send-keys w1:p4 Down Enter"])
        self.assertTrue((self.space / "beta/manager.json").exists())

    def test_blocked_start_without_a_trust_dialog_fails_with_the_pane_tail_and_closes_the_tab(self) -> None:
        (self.root.parent / "not-ready").write_text("")
        self.pane.write_text("something else\n")
        r = self.bin("herdr-manager", "start", "beta", "--dir", "/tmp")
        self.assertEqual(r.returncode, 2)
        self.assertIn("something else", r.stderr)
        self.assertNotIn("agent send-keys", " ".join(self.calls()))
        self.assertIn("tab close w1:t4", self.calls())
        self.assertFalse((self.space / "beta/manager.json").exists())

    def test_input_box_matches_both_prompt_glyphs(self) -> None:
        for text in ("> \n", "│ > \n", "❯ \n", "❯\xa0Try \"x\"\n", "  ? for shortcuts"):
            self.assertTrue(herdr_reports.INPUT_BOX.search(text), text)
        for text in ("loading\n", "❯Try\n", "echo > file\n"):
            self.assertFalse(herdr_reports.INPUT_BOX.search(text), text)

    def test_trust_accepted_but_no_input_box_raises(self) -> None:
        self.trust_dialog()
        self.ready.write_text("still loading\n")
        manager = SourceFileLoader("herdr_manager_under_test", str(REPO / "bin/herdr-manager")).load_module()
        with mock.patch.object(manager, "STARTUP_TIMEOUT", 0.3), self.assertRaises(herdr_reports.ReportsError):
            manager.accept_trust_dialog("w1:p4", Path.cwd().resolve())

    def test_wait_timeout_with_the_input_box_visible_still_submits_the_prompt(self) -> None:
        (self.root.parent / "wait-fail").write_text("")
        r = self.bin("manager-start", "beta", "--prompt", "go", "--dir", "/tmp")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.prompts(), ["agent prompt w1:p4 go"])

    def test_wait_timeout_without_the_input_box_fails_and_closes_the_tab(self) -> None:
        (self.root.parent / "wait-fail").write_text("")
        self.pane.write_text("loading\n")
        r = self.bin("manager-start", "beta", "--prompt", "go", "--dir", "/tmp")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(self.prompts(), [])
        self.assertIn("tab close w1:t4", self.calls())

    def test_start_rejects_a_bad_name_and_a_bad_session_before_any_tab(self) -> None:
        self.assertEqual(self.bin("herdr-manager", "start", "Bad Name").returncode, 2)
        self.assertEqual(self.bin("herdr-manager", "start", "ok", "--resume", "nope").returncode, 2)
        self.assertEqual([c for c in self.calls() if c.startswith("tab create")], [])

    def test_list_shows_liveness_and_newest_result(self) -> None:
        folder = self.manager()
        (folder / "result-1.md").write_text("x")
        (folder / "result-2.md").write_text("x")
        self.manager("gone", "w1:p9")
        out = self.bin("herdr-manager", "list").stdout.splitlines()
        self.assertEqual(out, ["alpha\tlive\tresult-2.md", "gone\tgone\t-"])


class IdleTests(ReportsCase):
    def setUp(self) -> None:
        super().setUp()
        self.pane.write_text("● Looked around\n  nothing more to do\n> \n  ? for shortcuts\n")
        self.status("idle")

    def status(self, state: str) -> None:
        os.environ["FAKE_PANES"] = (
            '{"pane_id":"w1:p1","tab_id":"w1:t1"},'
            f'{{"pane_id":"w1:p4","tab_id":"w1:t4","agent":"claude","agent_status":"{state}"}}'
        )

    def idle_lines(self) -> list[str]:
        return [p for p in self.prompts() if "idle, no report" in p]

    def test_idle_over_15_minutes_without_a_report_sends_one_line_with_the_pane_tail(self) -> None:
        self.manager()
        w = watch.Watcher(self.root)
        w.scan(0)
        w.scan(899)
        self.assertEqual(self.idle_lines(), [])
        w.scan(901)
        w.scan(5000)
        self.assertEqual(self.idle_lines(), ["agent prompt w1:p1 [worker-report] alpha idle, no report"])
        self.assertIn("nothing more to do", self.log.read_text())

    def test_a_new_idle_spell_is_reported_again(self) -> None:
        self.manager()
        w = watch.Watcher(self.root)
        w.scan(0)
        w.scan(901)
        self.status("working")
        w.scan(1000)
        self.status("idle")
        w.scan(1100)
        w.scan(2100)
        self.assertEqual(len(self.idle_lines()), 2)

    def test_idle_spell_is_reported_once_across_watcher_restarts(self) -> None:
        self.manager()
        watch.Watcher(self.root).scan(0)
        watch.Watcher(self.root).scan(0)
        w = watch.Watcher(self.root)
        w.scan(0)
        w.scan(901)
        self.assertEqual(len(self.idle_lines()), 1)
        again = watch.Watcher(self.root)
        again.scan(0)
        again.scan(901)
        self.assertEqual(len(self.idle_lines()), 1)

    def test_waiting_message_is_not_reported(self) -> None:
        self.manager()
        self.pane.write_text("● WAITING: the review to finish\n> \n")
        w = watch.Watcher(self.root)
        w.scan(0)
        w.scan(901)
        self.assertEqual(self.idle_lines(), [])

    def test_report_written_in_the_turn_is_not_reported_as_missing(self) -> None:
        folder = self.manager()
        w = watch.Watcher(self.root)
        self.status("working")
        w.scan(0)
        (folder / "result-1.md").write_text("Status: decision\nQ")
        self.status("idle")
        w.scan(10)
        w.scan(1000)
        self.assertEqual(self.idle_lines(), [])

    def test_standing_tab_idle_after_a_done_report_or_before_its_first_job_is_not_reported(self) -> None:
        folder = self.manager()
        (folder / "manager.json").write_text(json.dumps({"pane_id": "w1:p4", "tab_id": "w1:t4", "standing": True}))
        w = watch.Watcher(self.root)
        w.scan(0)
        w.scan(5000)
        (folder / "result-1.md").write_text("Status: done\nx\n")
        w.scan(6000)
        w.scan(20000)
        self.assertEqual(self.idle_lines(), [])

    def standing(self) -> Path:
        folder = self.manager()
        (folder / "manager.json").write_text(json.dumps({"pane_id": "w1:p4", "tab_id": "w1:t4", "standing": True}))
        return folder

    def test_standing_tab_that_works_after_a_done_report_then_idles_is_reported_once(self) -> None:
        folder = self.standing()
        (folder / "result-1.md").write_text("Status: done\nx\n")
        w = watch.Watcher(self.root)
        w.scan(0)
        w.scan(10)
        self.status("working")
        w.scan(100)
        self.status("idle")
        w.scan(200)
        w.scan(1100)
        w.scan(5000)
        self.assertEqual(len(self.idle_lines()), 1)

    def test_standing_tab_cleared_and_never_working_is_not_reported(self) -> None:
        folder = self.standing()
        (folder / "result-1.md").write_text("Status: done\nx\n")
        w = watch.Watcher(self.root)
        self.status("working")
        w.scan(0)
        self.status("idle")
        w.scan(10)
        self.assertEqual([p for p in self.prompts() if p.endswith("/clear")], ["agent prompt w1:p4 /clear"])
        w.scan(20)
        w.scan(5000)
        self.assertEqual(self.idle_lines(), [])

    def test_working_manager_is_never_reported(self) -> None:
        self.manager()
        self.status("working")
        w = watch.Watcher(self.root)
        w.scan(0)
        w.scan(5000)
        self.assertEqual(self.idle_lines(), [])


if __name__ == "__main__":
    unittest.main()
