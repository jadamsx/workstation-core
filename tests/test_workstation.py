import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
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

    def test_zshenv_is_linked_and_sets_null_glob_for_agent_shells(self) -> None:
        dests = [i.dest for i in self.ws.plan()]
        self.assertIn(self.home / ".zshenv", dests)
        probe = "echo *.nomatch-xyz; echo done"
        env = {"HOME": str(self.home), "ZDOTDIR": str(self.tmp), "PATH": os.environ["PATH"]}
        (self.tmp / ".zshenv").write_text((REPO / "shell/zshenv").read_text())
        run = lambda extra: subprocess.run(
            ["zsh", "-c", probe], env={**env, **extra}, capture_output=True, text=True
        )
        self.assertEqual(run({"CLAUDECODE": "1"}).stdout, "\ndone\n")
        self.assertIn("no matches found", run({}).stderr)

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
        self.ws.ROOT = self.tmp / "root"
        shutil.copytree(
            REPO,
            self.ws.ROOT,
            ignore=shutil.ignore_patterns(".git", "worktrees", "__pycache__"),
        )
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

    def kickstarts(self) -> list[str]:
        return [c for c in self.launchctl_calls() if c.startswith("kickstart")]

    def change(self, rel: str) -> None:
        with (self.ws.ROOT / rel).open("a") as handle:
            handle.write("\n# changed\n")

    def test_changed_program_is_kickstarted(self) -> None:
        run_quiet(self.ws.cmd_install, False)
        self.change("bin/herdr-report-watch")
        out = run_quiet(self.ws.cmd_install, False)
        self.assertIn("restart agent", out)
        self.assertEqual(
            self.kickstarts(),
            [f"kickstart -k gui/{os.getuid()}/dev.workstation.herdr-report-watch"],
        )

    def test_changed_lib_is_kickstarted(self) -> None:
        run_quiet(self.ws.cmd_install, False)
        self.change("lib/herdr_reports.py")
        run_quiet(self.ws.cmd_install, False)
        self.assertEqual(len(self.kickstarts()), 1)

    def test_unchanged_program_is_not_kickstarted(self) -> None:
        run_quiet(self.ws.cmd_install, False)
        run_quiet(self.ws.cmd_install, False)
        self.assertEqual(self.kickstarts(), [])

    def test_missing_stamp_is_written_without_restart(self) -> None:
        run_quiet(self.ws.cmd_install, False)
        stamp = self.home / ".local/state/workstation/dev.workstation.herdr-report-watch.sha256"
        stamp.unlink()
        run_quiet(self.ws.cmd_install, False)
        self.assertTrue(stamp.exists())
        self.assertEqual(self.kickstarts(), [])

    def test_check_mode_does_not_kickstart(self) -> None:
        run_quiet(self.ws.cmd_install, False)
        self.change("bin/herdr-report-watch")
        out = run_quiet(self.ws.cmd_install, True)
        self.assertIn("would restart agent", out)
        self.assertEqual(self.kickstarts(), [])

    def test_uninstall_removes_the_stamp(self) -> None:
        run_quiet(self.ws.cmd_install, False)
        run_quiet(self.ws.cmd_uninstall, False)
        stamp = self.home / ".local/state/workstation/dev.workstation.herdr-report-watch.sha256"
        self.assertFalse(stamp.exists())

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

    def test_only_git_network_commands_skip_the_sandbox(self) -> None:
        excluded = self.base["sandbox"]["excludedCommands"]
        for cmd in ("ps *", "shell-reap *", "gh *", "launchctl *", "git fetch*", "git push*", "git pull*", "git clone*", "git ls-remote*"):
            self.assertIn(cmd, excluded)
        self.assertNotIn("git *", excluded)
        self.assertNotIn("kill *", excluded)

    def test_git_state_and_caches_are_writable_in_the_sandbox(self) -> None:
        writable = self.base["sandbox"]["filesystem"]["allowWrite"]
        for path in ("**/.git", "~/.gitconfig", "~/.config/git", "~/.local/share/uv"):
            self.assertIn(path, writable)

    def test_allow_is_narrow_and_has_no_blanket_git(self) -> None:
        allow = self.base["permissions"]["allow"]
        self.assertNotIn("Bash(git *)", allow)
        self.assertNotIn("Bash(kill *)", allow)
        for rule in ("Bash(gh *)", "Bash(launchctl *)", "Bash(git fetch*)", "Bash(git push*)", "Bash(git worktree*)", "Bash(herdr *)", "Bash(ps *)", "Bash(shell-reap *)", "Bash(docker ps*)", "Bash(docker logs*)", "Bash(docker inspect*)"):
            self.assertIn(rule, allow)

    def test_destructive_git_stays_denied(self) -> None:
        deny = self.base["permissions"]["deny"]
        for rule in ("Bash(git stash)", "Bash(git stash push*)", "Bash(git stash pop*)", "Bash(git restore *)", "Bash(git checkout -- *)"):
            self.assertIn(rule, deny)
        self.assertIn("Read(~/.ssh/**)", deny)
        self.assertNotIn("Bash(git stash*)", deny)
        for rule in ("Bash(git stash list*)", "Bash(git stash show*)"):
            self.assertIn(rule, self.base["permissions"]["allow"])
        for rule in ("Bash(git push * -f*)", "Bash(git push *+*)", "Bash(git * reset --hard*)", "Bash(git * clean *)", "Bash(git checkout .*)", "Bash(git -c *=*)", "Bash(git config *core.sshCommand*)", "Bash(git push --delete*)", "Bash(git push -f*)", "Bash(gh repo delete*)", "Bash(gh auth *)", "Bash(launchctl submit*)"):
            self.assertIn(rule, deny)

    def test_remote_branch_pushes_and_api_deletes_ask(self) -> None:
        ask = self.base["permissions"]["ask"]
        for rule in ("Bash(git push *:main*)", "Bash(git push *:master*)", "Bash(git push *:develop*)", "Bash(gh api * -X DELETE*)"):
            self.assertIn(rule, ask)

    def test_git_hooks_are_not_writable_in_the_sandbox(self) -> None:
        self.assertIn("**/.git/hooks", self.base["sandbox"]["filesystem"]["denyWrite"])


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
