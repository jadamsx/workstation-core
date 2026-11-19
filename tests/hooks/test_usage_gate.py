import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
gate = SourceFileLoader("usage_gate_under_test", str(ROOT / "bin/usage-gate")).load_module()


class GateCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name).resolve()
        self.usage = self.base / "usage.json"
        self.override = self.base / "usage-override"
        self.env = {
            **{k: v for k, v in os.environ.items() if not k.startswith("USAGE")},
            "USAGE_FILE": str(self.usage),
            "USAGE_OVERRIDE_FILE": str(self.override),
        }

    def write(self, five: float | None = 10, seven: float | None = 10, reset: float | None = None, age: float = 0) -> float:
        reset = reset or time.time() + 3600
        window = lambda pct: None if pct is None else {"used_percentage": pct, "resets_at": reset}
        self.usage.write_text(json.dumps({"five_hour": window(five), "seven_day": window(seven)}))
        stamp = time.time() - age
        os.utime(self.usage, (stamp, stamp))
        return reset

    def cli(self, **extra: str) -> subprocess.CompletedProcess:
        return subprocess.run([str(ROOT / "bin/usage-gate")], capture_output=True, text=True, env={**self.env, **extra})


class GateTest(GateCase):
    def test_parks_at_5h_95_or_7d_90_until_the_reset(self) -> None:
        for five, seven in ((95, 10), (10, 90), (99, 95)):
            reset = self.write(five, seven)
            r = self.cli()
            self.assertEqual(r.returncode, 1)
            self.assertIn("parked until", r.stdout)
            os.environ.update(self.env)
            self.assertEqual(gate.parked_until(), reset)

    def test_under_the_thresholds_is_open_and_silent(self) -> None:
        self.write(94, 89)
        r = self.cli()
        self.assertEqual((r.returncode, r.stdout), (0, ""))

    def test_thresholds_come_from_the_environment(self) -> None:
        self.write(50, 10)
        self.assertEqual(self.cli(USAGE_GATE_5H="50").returncode, 1)
        self.write(10, 50)
        self.assertEqual(self.cli(USAGE_GATE_7D="50").returncode, 1)

    def test_missing_stale_or_rate_limit_free_readings_fail_open(self) -> None:
        self.assertEqual(self.cli().returncode, 0)
        self.write(99, 99, age=901)
        self.assertEqual(self.cli().returncode, 0)
        self.usage.write_text("{}")
        self.assertEqual(self.cli().returncode, 0)
        self.usage.write_text("not json")
        self.assertEqual(self.cli().returncode, 0)
        for body in ("[1]", "null"):
            self.usage.write_text(body)
            r = self.cli()
            self.assertEqual((r.returncode, r.stderr), (0, ""))

    def test_a_window_that_already_reset_does_not_park(self) -> None:
        self.write(99, 10, reset=time.time() - 5)
        self.assertEqual(self.cli().returncode, 0)

    def test_env_off_and_an_unexpired_override_lift_it_but_an_expired_one_does_not(self) -> None:
        self.write(99, 10)
        self.assertEqual(self.cli(USAGE_GATE="off").returncode, 0)
        self.override.write_text(str(time.time() + 600))
        self.assertEqual(self.cli().returncode, 0)
        self.override.write_text(str(time.time() - 1))
        self.assertEqual(self.cli().returncode, 1)


class HookTest(GateCase):
    def run_hook(self, payload: dict, **extra: str) -> subprocess.CompletedProcess:
        payload = {"tool_name": "Agent", "tool_input": {}, "cwd": str(self.base), **payload}
        return subprocess.run(
            [sys.executable, str(ROOT / "claude/hooks/usage-gate-hook.py")],
            input=json.dumps(payload), text=True, capture_output=True, env={**self.env, **extra},
        )

    def test_denies_a_new_top_level_spawn_when_parked(self) -> None:
        self.write(99, 10)
        r = self.run_hook({})
        self.assertEqual(r.returncode, 2)
        self.assertIn("parked until", r.stderr)

    def test_allows_a_sub_spawn_from_a_session_in_an_owns_worktree(self) -> None:
        self.write(99, 10)
        tree = self.base / "tree"
        (tree / "sub").mkdir(parents=True)
        (tree / ".owns").write_text("node: N1\n")
        self.assertEqual(self.run_hook({"cwd": str(tree / "sub")}).returncode, 0)

    def test_allows_a_spawn_from_inside_a_subagent(self) -> None:
        self.write(99, 10)
        self.assertEqual(self.run_hook({"agent_id": "abc"}).returncode, 0)

    def test_allows_when_open_overridden_or_not_an_agent_call(self) -> None:
        self.write(10, 10)
        self.assertEqual(self.run_hook({}).returncode, 0)
        self.write(99, 10)
        self.assertEqual(self.run_hook({}, USAGE_GATE="off").returncode, 0)
        self.assertEqual(self.run_hook({"tool_name": "Bash"}).returncode, 0)


class StatuslineTest(GateCase):
    def run_line(self, payload: dict) -> None:
        subprocess.run(
            ["bash", str(ROOT / "claude/statusline-command.sh")],
            input=json.dumps(payload), text=True, capture_output=True, env=self.env, check=True,
        )

    def test_an_unwritable_usage_file_is_silent(self) -> None:
        self.env["USAGE_FILE"] = str(self.base / "missing-dir" / "usage.json")
        limits = {"five_hour": {"used_percentage": 1, "resets_at": 1900000000}}
        r = subprocess.run(
            ["bash", str(ROOT / "claude/statusline-command.sh")],
            input=json.dumps({"rate_limits": limits}), text=True, capture_output=True, env=self.env,
        )
        self.assertEqual(r.stderr, "")

    def test_writes_the_rate_limits_atomically_and_skips_a_payload_without_them(self) -> None:
        self.run_line({"model": {"id": "m"}})
        self.assertFalse(self.usage.exists())
        limits = {"five_hour": {"used_percentage": 42, "resets_at": 1900000000}, "seven_day": {"used_percentage": 7, "resets_at": 1900500000}}
        self.run_line({"model": {"id": "m"}, "rate_limits": limits})
        self.assertEqual(json.loads(self.usage.read_text()), limits)
        self.assertEqual(sorted(p.name for p in self.base.iterdir()), ["usage.json"])


if __name__ == "__main__":
    unittest.main()
