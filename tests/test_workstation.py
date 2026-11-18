import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent


def load(home: Path):
    os.environ["WORKSTATION_HOME"] = str(home)
    os.environ["WORKSTATION_HOST"] = "scratch"
    spec = importlib.util.spec_from_file_location(
        "workstation_under_test", REPO / "lib" / "workstation.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_quiet(fn, *args) -> str:
    with contextlib.redirect_stdout(io.StringIO()) as out:
        fn(*args)
    return out.getvalue()


class ScratchCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.ws = load(self.home)


class HomeOverrideTest(unittest.TestCase):
    def test_workstation_home_moves_every_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            module = load(Path(tmp))
            dests = [item.dest for item in module.plan()]
        self.assertTrue(dests)
        self.assertTrue(all(Path(tmp) in d.parents for d in dests), dests)


class PlanTest(ScratchCase):
    def test_links_only_the_helper_bins(self) -> None:
        names = sorted(
            i.dest.name
            for i in self.ws.plan()
            if i.dest.parent == self.home / ".local/bin"
        )
        self.assertEqual(names, sorted(self.ws.BINS))

    def test_bytecode_directories_are_not_linked(self) -> None:
        dests = [item.dest.name for item in self.ws.claude_links()]
        self.assertNotIn("__pycache__", dests)

    def test_machine_overlay_comes_from_the_machines_env(self) -> None:
        machines = self.tmp / "machines"
        (machines / "scratch").mkdir(parents=True)
        (machines / "scratch" / "settings.overlay.json").write_text("{}")
        with mock.patch.dict(os.environ, {"WORKSTATION_MACHINES": str(machines)}):
            settings = next(
                i for i in self.ws.plan() if isinstance(i, self.ws.Settings)
            )
        self.assertEqual(
            settings.overlay, machines / "scratch" / "settings.overlay.json"
        )


class StatusTest(ScratchCase):
    def test_counts_items_that_need_attention(self) -> None:
        lines = run_quiet(self.ws.cmd_status).strip().splitlines()
        in_place, rest = lines[-1].split(" of ")
        total = int(rest.split()[0])
        self.assertEqual(int(in_place), total - len(lines[:-1]))
        self.assertEqual(total, len(self.ws.plan()))

    def test_status_is_clean_after_install(self) -> None:
        run_quiet(self.ws.cmd_install, False)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.ws.cmd_status(), 0)


class UninstallTest(ScratchCase):
    def test_restores_oldest_backup_across_installs(self) -> None:
        originals = {}
        for item in self.ws.plan():
            if item.kind == "link" and item.src.exists():
                item.dest.parent.mkdir(parents=True, exist_ok=True)
                item.dest.write_text(f"original {item.dest}")
                originals[item.dest] = item.dest.read_text()
        self.assertGreater(len(originals), 20)
        settings = self.ws.CLAUDE / "settings.json"
        settings.write_text('{"original": true}')
        originals[settings] = settings.read_text()

        run_quiet(self.ws.cmd_install, False)
        settings.write_text('{"drifted": true}')
        run_quiet(self.ws.cmd_install, False)
        run_quiet(self.ws.cmd_uninstall, False)

        for dest, text in originals.items():
            self.assertFalse(dest.is_symlink(), dest)
            self.assertEqual(dest.read_text(), text, dest)


class AgentTest(ScratchCase):
    def setUp(self) -> None:
        super().setUp()
        bindir = self.tmp / "fakebin"
        bindir.mkdir()
        self.calls = self.tmp / "calls"
        loaded = self.tmp / "loaded"
        launchctl = bindir / "launchctl"
        launchctl.write_text(
            f'#!/bin/sh\necho "$@" >> {self.calls}\n'
            f"case $1 in print) [ -e {loaded} ];; bootstrap) touch {loaded};; "
            f"bootout) rm -f {loaded};; esac\n"
        )
        (bindir / "herdr").write_text("#!/bin/sh\n")
        for f in bindir.iterdir():
            f.chmod(0o755)
        patcher = mock.patch.dict(
            os.environ, {"PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}"}
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.ws.LIVE = True
        self.plist = (
            self.home / "Library/LaunchAgents/dev.workstation.herdr-report-watch.plist"
        )

    def launchctl_calls(self) -> list[str]:
        return self.calls.read_text().splitlines() if self.calls.exists() else []

    def test_install_renders_and_loads_the_watcher(self) -> None:
        run_quiet(self.ws.cmd_install, False)
        text = self.plist.read_text()
        self.assertIn(f"{self.ws.ROOT}/bin/herdr-report-watch", text)
        self.assertIn(str(self.home), text)
        self.assertNotIn("__ROOT__", text)
        self.assertNotIn("__HOME__", text)
        bootstraps = [c for c in self.launchctl_calls() if c.startswith("bootstrap")]
        self.assertEqual(bootstraps, [f"bootstrap gui/{os.getuid()} {self.plist}"])

    def test_second_install_does_not_reload(self) -> None:
        run_quiet(self.ws.cmd_install, False)
        before = self.launchctl_calls()
        run_quiet(self.ws.cmd_install, False)
        new = self.launchctl_calls()[len(before) :]
        self.assertFalse([c for c in new if c.split()[0] in ("bootstrap", "bootout")])

    def test_changed_plist_is_booted_out_then_bootstrapped(self) -> None:
        run_quiet(self.ws.cmd_install, False)
        self.plist.write_text("stale")
        run_quiet(self.ws.cmd_install, False)
        verbs = [
            c.split()[0] for c in self.launchctl_calls() if c.split()[0] != "print"
        ]
        self.assertEqual(verbs, ["bootstrap", "bootout", "bootstrap"])

    def test_uninstall_boots_out_and_removes_the_plist(self) -> None:
        run_quiet(self.ws.cmd_install, False)
        run_quiet(self.ws.cmd_uninstall, False)
        self.assertFalse(self.plist.exists())
        self.assertIn(
            f"bootout gui/{os.getuid()}/dev.workstation.herdr-report-watch",
            self.launchctl_calls(),
        )

    def test_skipped_when_herdr_is_missing(self) -> None:
        (self.tmp / "fakebin" / "herdr").unlink()
        with mock.patch.object(self.ws.shutil, "which", return_value=None):
            out = run_quiet(self.ws.cmd_install, False)
        self.assertIn("herdr not on PATH", out)
        self.assertFalse(self.plist.exists())


class SettingsApplyTest(ScratchCase):
    def make(self):
        base = self.tmp / "base.json"
        meta = {
            "ownedKeys": ["new"],
            "ownedHookPath": "/.claude/hooks/",
            "foreignHookMarkers": [],
            "dropHookMarkers": [],
        }
        base.write_text(json.dumps({"new": 1, "x-workstation": meta}))
        dest = self.home / ".claude" / "settings.json"
        dest.parent.mkdir(parents=True)
        dest.write_text('{"original": 1}')
        self.ws.ROOT = self.tmp
        return self.ws.Settings(dest, base, self.tmp / "no-overlay.json")

    def test_failure_mid_write_leaves_original(self) -> None:
        settings = self.make()
        with mock.patch.object(self.ws.os, "replace", side_effect=OSError("disk")):
            with self.assertRaises(OSError):
                settings.apply(self.ws.Backup())
        self.assertEqual(settings.dest.read_text(), '{"original": 1}')
        self.assertEqual(
            [p.name for p in settings.dest.parent.iterdir()], ["settings.json"]
        )

    def test_success_replaces_and_keeps_backup_copy(self) -> None:
        settings = self.make()
        backup = self.ws.Backup()
        settings.apply(backup)
        self.assertEqual(json.loads(settings.dest.read_text())["new"], 1)
        self.assertEqual(
            (backup.dir / ".claude/settings.json").read_text(), '{"original": 1}'
        )

    def test_foreign_hook_survives_when_base_lists_no_markers(self) -> None:
        settings = self.make()
        meta = {"ownedKeys": ["new"], "ownedHookPath": "/.claude/hooks/"}
        settings.base.write_text(json.dumps({"new": 1, "x-workstation": meta}))
        foreign = {"hooks": [{"type": "command", "command": "other-tool notify"}]}
        settings.dest.write_text(json.dumps({"hooks": {"Stop": [foreign]}}))
        settings.apply(self.ws.Backup())
        self.assertEqual(
            json.loads(settings.dest.read_text())["hooks"]["Stop"], [foreign]
        )


class BaseSettingsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.base = json.loads((REPO / "claude" / "settings.base.json").read_text())

    def test_forge_and_launchctl_skip_the_sandbox_and_are_allowed(self) -> None:
        for cmd in ("gh", "git", "launchctl"):
            self.assertIn(f"{cmd} *", self.base["sandbox"]["excludedCommands"])
            self.assertIn(f"Bash({cmd} *)", self.base["permissions"]["allow"])

    def test_destructive_git_stays_denied(self) -> None:
        deny = self.base["permissions"]["deny"]
        for rule in ("Bash(git stash*)", "Bash(git restore *)", "Bash(git checkout -- *)"):
            self.assertIn(rule, deny)
        self.assertIn("Read(~/.ssh/**)", deny)


class McpAndPluginsTest(ScratchCase):
    def test_install_writes_core_mcp_servers_to_claude_json(self) -> None:
        run_quiet(self.ws.cmd_install, False)
        servers = json.loads((self.home / ".claude.json").read_text())["mcpServers"]
        self.assertEqual(sorted(servers), ["chrome-devtools", "playwright"])
        self.assertIn("@playwright/mcp@0.0.85", servers["playwright"]["args"])

    def test_plugin_commands_are_skipped_outside_the_real_home(self) -> None:
        self.ws.ROOT = self.tmp
        (self.tmp / "claude").mkdir()
        (self.tmp / "claude/plugins.json").write_text(
            json.dumps(
                {
                    "marketplaces": [{"name": "m", "source": {"repo": "o/m"}}],
                    "plugins": ["p@m"],
                }
            )
        )
        items = self.ws.plugin_items()
        self.assertEqual([i.cmd[-1] for i in items], ["o/m", "p@m"])
        self.assertEqual({i.state() for i in items}, {self.ws.SKIPPED})
        with mock.patch.object(self.ws.subprocess, "run") as run:
            run_quiet(self.ws.cmd_install, False)
        self.assertNotIn(
            ["claude", "plugin", "install", "p@m"],
            [c.args[0] for c in run.call_args_list],
        )


if __name__ == "__main__":
    unittest.main()
