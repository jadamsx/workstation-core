import json
import os
import signal
import stat
import sys
import subprocess
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
POLICY = json.loads((REPO / "claude/resource-policy.json").read_text())
sys.path.insert(0, str(REPO / "lib"))
import herdr_reports  # noqa: E402


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
    echo "{\\"result\\":{\\"process_info\\":{\\"shell_pid\\":${FAKE_SHELL_PID:-0},\\"cmdline\\":\\"$FAKE_CMDLINE\\",\\"foreground_processes\\":$fg}}}" ;;
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

    def bin(self, script: str, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([str(REPO / "bin" / script), *args], capture_output=True, text=True)

    def setup_run(self, cwd: Path | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([str(REPO / "bin/herdr-manager"), "setup"], capture_output=True, text=True, cwd=cwd or self.root.parent)

    def creates(self) -> list[str]:
        return [c for c in self.calls() if c.startswith("tab create")]

    def starts(self) -> list[str]:
        return [c for c in self.calls() if c.startswith("agent start")]

    def started_servers(self, start: str) -> set[str]:
        return set(json.loads(Path(start.split("--mcp-config ")[1].split()[0]).read_text())["mcpServers"])

    def trust_dialog(self) -> None:
        self.pane.write_text(f"Quick safety check\n{herdr_reports.TRUST_DIALOG}\n❯ 1. Yes, I trust this folder\n  2. No, exit\n")

    def real_trust_dialog(self) -> None:
        self.pane.write_text(
            f"Quick safety check: {herdr_reports.TRUST_DIALOG}\n ❯ No, exit\n   Yes, I trust this folder\n Enter to confirm · Esc to cancel\n"
        )

    def test_shell_reap_reports_an_unreadable_process_table_in_one_line(self) -> None:
        ps = self.log.parent / "bin/ps"
        ps.write_text("#!/bin/sh\nexit 1\n")
        ps.chmod(ps.stat().st_mode | stat.S_IXUSR)
        r = self.bin("shell-reap", "1")
        self.assertEqual((r.returncode, r.stderr.count("\n"), "Traceback" in r.stderr), (1, 1, False))


class SetupTests(ReportsCase):
    def test_setup_renames_the_lead_tab_and_opens_one_sonnet_work_tab_that_knows_the_lead_pane(self) -> None:
        r = self.setup_run()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("tab rename w1:t1 ◆ lead", self.calls())
        (work,) = self.creates()
        self.assertIn("--label ▸ work --env WORKSTATION_ROLE=work --env WORKSTATION_LEAD_PANE=w1:p1 --env DISABLE_AUTO_UPDATE=true", work)
        for item in herdr_reports.NO_STDIN_ENV:
            self.assertIn(f"--env {item}", work)
        (start,) = self.starts()
        self.assertIn("agent start work-space-one --kind claude --pane w1:p4 -- --model sonnet --strict-mcp-config", start)
        self.assertTrue(start.endswith("manager-brief.md"))
        self.assertEqual(self.started_servers(start), set(POLICY["roles"]["work"]))

    def test_setup_twice_changes_nothing(self) -> None:
        self.setup_run()
        os.environ["FAKE_TABS"] = '{"tab_id":"w1:t4","label":"▸ work"}'
        r = self.setup_run()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(self.creates()), 1)

    def test_setup_fails_when_the_existing_work_agent_lacks_the_brief_flag(self) -> None:
        os.environ["FAKE_TABS"] = '{"tab_id":"w1:t4","label":"▸ work"}'
        os.environ["FAKE_CMDLINE"] = "claude --model sonnet"
        r = self.setup_run()
        self.assertEqual(r.returncode, 2)
        self.assertIn("close the tab and rerun setup", r.stderr)
        self.assertEqual(self.creates(), [])

    def test_setup_fails_when_the_work_tab_has_no_pane(self) -> None:
        os.environ["FAKE_TABS"] = '{"tab_id":"w1:t9","label":"▸ work"}'
        r = self.setup_run()
        self.assertEqual(r.returncode, 2)

    def test_setup_outside_herdr_fails_before_any_tab(self) -> None:
        del os.environ["HERDR_PANE_ID"]
        self.assertEqual(self.setup_run().returncode, 2)
        self.assertEqual(self.creates(), [])

    def test_setup_fails_naming_file_and_role_for_a_bad_policy(self) -> None:
        module = SourceFileLoader("herdr_manager_policy", str(REPO / "bin/herdr-manager")).load_module()
        policy = self.root / "policy.json"
        self.root.mkdir(parents=True, exist_ok=True)
        for text in (None, "{", '{"roles": {}}'):
            policy.unlink(missing_ok=True)
            if text is not None:
                policy.write_text(text)
            with self.subTest(text=text), mock.patch.object(module, "POLICY", policy), mock.patch("sys.stderr") as err:
                self.assertEqual(module.main(["setup"]), 2)
                shown = "".join(c.args[0] for c in err.write.call_args_list)
                self.assertIn("policy.json", shown)
                self.assertIn("'work'", shown)

    def test_wait_for_shell_gives_up_while_the_pane_stays_busy(self) -> None:
        os.environ["FAKE_BUSY_POLLS"] = "999"
        self.assertFalse(herdr_reports.wait_for_shell("w1:p4", 0.3, 0.1))

    def test_setup_waits_until_the_shell_is_the_only_foreground_process(self) -> None:
        os.environ["FAKE_BUSY_POLLS"] = "3"
        self.assertEqual(self.setup_run().returncode, 0)
        calls = self.calls()
        first_start = next(i for i, c in enumerate(calls) if c.startswith("agent start"))
        self.assertEqual(len([c for c in calls[:first_start] if c.startswith("pane process-info")]), 4)

    def test_agent_start_is_retried_while_the_pane_is_busy(self) -> None:
        os.environ["FAKE_START_BUSY"] = "3"
        self.assertEqual(self.setup_run().returncode, 0)
        self.assertEqual(len(self.starts()), 4)

    def test_agent_start_gives_up_after_three_retries_and_closes_the_tab(self) -> None:
        os.environ["FAKE_START_BUSY"] = "9"
        self.assertEqual(self.setup_run().returncode, 1)
        self.assertEqual(len(self.starts()), 4)
        self.assertIn("tab close w1:t4", self.calls())

    def test_trust_dialog_is_accepted(self) -> None:
        self.trust_dialog()
        r = self.setup_run()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("agent send-keys w1:p4 Enter", self.calls())

    def test_blocked_start_with_the_trust_dialog_visible_sends_down_enter(self) -> None:
        (self.root.parent / "not-ready").write_text("")
        self.real_trust_dialog()
        r = self.setup_run()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(self.starts()), 1)
        self.assertIn("agent send-keys w1:p4 Down Enter", self.calls())

    def test_trust_then_imports_dialog_are_both_answered(self) -> None:
        self.trust_dialog()
        (self.root.parent / "next-pane").write_text(
            "Allow external CLAUDE.md file imports?\n ❯ No, disable external imports\n   Yes, allow external imports\n Enter to confirm · Esc to cancel\n"
        )
        r = self.setup_run()
        self.assertEqual(r.returncode, 0, r.stderr)
        sent = [c for c in self.calls() if c.startswith("agent send-keys")]
        self.assertEqual(sent, ["agent send-keys w1:p4 Enter", "agent send-keys w1:p4 Down Enter"])

    def test_blocked_start_without_a_trust_dialog_fails_with_the_pane_tail_and_closes_the_tab(self) -> None:
        (self.root.parent / "not-ready").write_text("")
        self.pane.write_text("something else\n")
        r = self.setup_run()
        self.assertEqual(r.returncode, 2)
        self.assertIn("something else", r.stderr)
        self.assertNotIn("agent send-keys", " ".join(self.calls()))
        self.assertIn("tab close w1:t4", self.calls())

    def test_trust_accepted_but_no_input_box_raises(self) -> None:
        self.trust_dialog()
        self.ready.write_text("still loading\n")
        manager = SourceFileLoader("herdr_manager_under_test", str(REPO / "bin/herdr-manager")).load_module()
        with mock.patch.object(manager, "STARTUP_TIMEOUT", 0.3), self.assertRaises(herdr_reports.ReportsError):
            manager.accept_trust_dialog("w1:p4", Path.cwd().resolve())

    def test_input_box_matches_both_prompt_glyphs(self) -> None:
        for text in ("> \n", "│ > \n", "❯ \n", "❯\xa0Try \"x\"\n", "  ? for shortcuts"):
            self.assertTrue(herdr_reports.INPUT_BOX.search(text), text)
        for text in ("loading\n", "❯Try\n", "echo > file\n"):
            self.assertFalse(herdr_reports.INPUT_BOX.search(text), text)


class NoStdinEnvTests(unittest.TestCase):
    def test_settings_env_adds_only_ci_to_the_tab_env_because_ci_strips_claude_colours(self) -> None:
        env = json.loads((REPO / "claude/settings.base.json").read_text())["env"]
        settings = {f"{k}={v}" for k, v in env.items() if k != "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"}
        self.assertEqual(settings, {"CI=1", *herdr_reports.NO_STDIN_ENV})
        self.assertNotIn("CI=1", herdr_reports.NO_STDIN_ENV)



class StopShellTests(unittest.TestCase):
    P = herdr_reports.Proc
    ROWS = [
        P(10, 5, 5000, 50.0, "claude --model sonnet"),
        P(20, 10, 900, 0.0, "/bin/zsh -c source /h/.claude/shell-snapshots/s.sh && eval 'make serve' < /dev/null"),
        P(21, 20, 900, 0.0, "make serve"),
    ]

    def test_stop_shell_accepts_only_a_shell_under_claude(self) -> None:
        rows = self.ROWS + [self.P(30, 1, 900, 0.0, "/bin/zsh -c orphan"), self.P(40, 20, 900, 0.0, "python3 x")]
        sent: list = []

        def stop(pid: int, caller: int = 999) -> None:
            herdr_reports.stop_shell(pid, lambda: rows, lambda p, sig: sent.append((p, sig)), caller)

        for pid in (40, 30, 10, 1):
            with self.assertRaises(herdr_reports.ReportsError):
                stop(pid)
        with self.assertRaises(herdr_reports.ReportsError):
            stop(20, caller=21)
        self.assertEqual(sent, [])
        stop(20)
        self.assertEqual(sent, [(40, signal.SIGTERM), (21, signal.SIGTERM), (20, signal.SIGTERM)])

    def test_ps_fields_parse(self) -> None:
        self.assertEqual(herdr_reports.clock_seconds("1-02:03:04"), 93784)
        self.assertEqual(herdr_reports.clock_seconds("35:36"), 2136)
        self.assertEqual(herdr_reports.clock_seconds("0:05.11"), 5.11)


if __name__ == "__main__":
    unittest.main()
