import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[2] / "claude/hooks"
RM_RF = "rm " + "-rf"


def run_hook(
    name: str, payload: dict, env: dict | None = None
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOKS / name)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env={**os.environ, **(env or {})},
    )


class ChangeGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)

    def bash(self, command: str) -> subprocess.CompletedProcess:
        return run_hook(
            "pre-commit-guard.py",
            {
                "tool_name": "Bash",
                "cwd": str(self.repo),
                "tool_input": {"command": command},
            },
        )

    def test_long_title_blocked_for_gh_and_glab(self) -> None:
        title = "x" * 81
        for command in (
            f'gh pr create --title "{title}"',
            f'glab mr create --title "{title}"',
        ):
            result = self.bash(command)
            self.assertEqual(result.returncode, 2, command)
            self.assertIn("too long", result.stderr)

    def test_short_title_allowed(self) -> None:
        self.assertEqual(
            self.bash('gh pr create --title "Add a thing" --draft').returncode, 0
        )

    def test_github_template_headings_required(self) -> None:
        template = self.repo / ".github/pull_request_template.md"
        template.parent.mkdir()
        template.write_text("## Summary\n## Testing\n")
        result = self.bash(
            'gh pr create --title "Add a thing" --body "## Summary\nDone"'
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Testing", result.stderr)
        self.assertEqual(
            self.bash(
                'gh pr create -t "T" -b "## Summary\nx\n## Testing\ny"'
            ).returncode,
            0,
        )

    def test_gitlab_template_headings_required(self) -> None:
        template = self.repo / ".gitlab/merge_request_templates/default.md"
        template.parent.mkdir(parents=True)
        template.write_text("## What\n")
        result = self.bash('glab mr create --title "T" --description "nothing"')
        self.assertEqual(result.returncode, 2)
        self.assertIn("What", result.stderr)


class CommitGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)

    def commit(self, message: str) -> subprocess.CompletedProcess:
        command = 'git commit -m "' + message + '"'
        return run_hook(
            "pre-commit-guard.py",
            {
                "tool_name": "Bash",
                "cwd": str(self.repo),
                "tool_input": {"command": command},
            },
        )

    def test_plain_message_allowed_by_default(self) -> None:
        self.assertEqual(self.commit("Sum token usage across calls").returncode, 0)

    def test_precommit_config_without_installed_hook_blocked(self) -> None:
        (self.repo / ".pre-commit-config.yaml").write_text("repos: []\n")
        result = self.commit("Sum token usage")
        self.assertEqual(result.returncode, 2)
        self.assertIn("pre-commit install", result.stderr)

    def test_precommit_config_with_installed_hook_allowed(self) -> None:
        (self.repo / ".pre-commit-config.yaml").write_text("repos: []\n")
        (self.repo / ".git/hooks/pre-commit").write_text("#!/bin/sh\n")
        self.assertEqual(self.commit("Sum token usage").returncode, 0)

    def test_staged_what_comment_blocked(self) -> None:
        (self.repo / "a.py").write_text("# Initialize the counter\ncount = 0\n")
        subprocess.run(["git", "add", "a.py"], cwd=self.repo, check=True)
        result = self.commit("Add counter")
        self.assertEqual(result.returncode, 2)
        self.assertIn("comments", result.stderr)


class PushGuardTest(unittest.TestCase):
    def push(
        self, change_json: str, tool: str = "gh", command: str = "git push"
    ) -> subprocess.CompletedProcess:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        repo = root / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        bin_dir = root / "bin"
        bin_dir.mkdir()
        sub = "pr" if tool == "gh" else "mr"
        fake = bin_dir / tool
        fake.write_text(
            f"#!/bin/sh\n[ \"$1\" = {sub} ] || exit 1\necho '{change_json}'\n"
        )
        fake.chmod(0o755)
        env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}"}
        return subprocess.run(
            [sys.executable, str(HOOKS / "pre-push-guard.py")],
            env=env,
            text=True,
            capture_output=True,
            input=json.dumps(
                {
                    "tool_name": "Bash",
                    "cwd": str(repo),
                    "tool_input": {"command": command},
                }
            ),
        )

    def test_clean_change_allowed(self) -> None:
        result = self.push(
            '{"title": "Add a thing", "body": "Done", "reviewDecision": ""}'
        )
        self.assertEqual(result.returncode, 0)

    def test_placeholder_body_blocked(self) -> None:
        result = self.push(
            '{"title": "Add a thing", "body": "Briefly summarise it", "reviewDecision": ""}'
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("placeholder", result.stderr)

    def test_approved_github_change_blocked(self) -> None:
        result = self.push(
            '{"title": "T", "body": "Done", "reviewDecision": "APPROVED"}'
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("already approved", result.stderr)

    def test_gitlab_placeholder_blocked(self) -> None:
        result = self.push(
            '{"title": "T", "description": "Provide a concise overview", "iid": 4}',
            tool="glab",
        )
        self.assertEqual(result.returncode, 2)

    def test_no_open_change_allowed(self) -> None:
        self.assertEqual(self.push("{}").returncode, 0)

    def test_heredoc_and_quoted_push_words_allowed(self) -> None:
        approved = '{"title": "T", "body": "Done", "reviewDecision": "APPROVED"}'
        for command in (
            "cat > notes.md <<'EOF'\ngit push origin main\nEOF",
            'git commit -m "docs: explain git push"',
            "echo 'git push' | wc -c",
        ):
            with self.subTest(command=command):
                self.assertEqual(self.push(approved, command=command).returncode, 0)

    def test_real_push_still_gated_in_a_command_chain(self) -> None:
        approved = '{"title": "T", "body": "Done", "reviewDecision": "APPROVED"}'
        for command in (
            "git push",
            "cd . && git -C . push origin b",
            "FOO=1 git push; ls",
            "sudo git push",
            "env git push",
            'bash -c "git push"',
        ):
            with self.subTest(command=command):
                self.assertEqual(self.push(approved, command=command).returncode, 2)


class SharedEnvGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.hosts = Path(tmp.name) / "shared-envs.txt"
        self.hosts.write_text((HOOKS / "shared-envs.example.txt").read_text())

    def call(self, tool: str, url: str = "") -> subprocess.CompletedProcess:
        payload = {
            "tool_name": f"mcp__playwright__browser_{tool}",
            "tool_input": {"url": url},
        }
        return run_hook(
            "shared-env-guard.py", payload, {"SHARED_ENVS_FILE": str(self.hosts)}
        )

    def test_write_on_shared_host_blocked(self) -> None:
        self.call("navigate", "https://app.staging.example.com/app")
        self.assertEqual(self.call("fill_form").returncode, 2)

    def test_suffix_and_exact_entries(self) -> None:
        for url, code in [
            ("https://qa.staging.example.com", 2),
            ("https://www.production.example.com", 2),
            ("https://notstaging.example.com", 0),
            ("https://other.production.example.com", 0),
        ]:
            self.call("navigate", url)
            self.assertEqual(self.call("fill_form").returncode, code, url)

    def test_write_on_local_host_allowed(self) -> None:
        self.call("navigate", "http://localhost:3000")
        self.assertEqual(self.call("fill_form").returncode, 0)

    def test_click_on_shared_host_allowed(self) -> None:
        self.call("navigate", "https://app.staging.example.com/app")
        self.assertEqual(self.call("click").returncode, 0)

    def test_missing_hosts_file_shares_nothing(self) -> None:
        self.hosts.unlink()
        self.call("navigate", "https://app.staging.example.com")
        self.assertEqual(self.call("fill_form").returncode, 0)


class RmGuardTest(unittest.TestCase):
    def bash(
        self, command: str, cwd: str = "/work", escape: object = False
    ) -> subprocess.CompletedProcess:
        tool_input: dict = {"command": command}
        if escape:
            tool_input["dangerouslyDisableSandbox"] = escape
        return run_hook(
            "rm-guard.py",
            {"tool_name": "Bash", "tool_input": tool_input, "cwd": cwd},
            {"DRAFTS_DIR": str(Path.home() / "drafts")},
        )

    def test_recursive_rm_outside_safe_roots_blocked(self) -> None:
        for cmd in [
            "rm -r /",
            "rm -r ~",
            "rm -r ~/code/app",
            "rm -r ../x",
            "rm -R *",
            "rm -r ~/.cache/../.ssh",
            "rm -r $TMPDIR/a ~/Documents",
            "rm -r $UNSET/x",
            "rm -r $(pwd)",
            "ls && rm -R /work/src",
            "rm -r ~/drafts",
            "rm --recursive /work/src",
        ]:
            result = self.bash(cmd)
            self.assertEqual(result.returncode, 2, cmd)
            self.assertIn("rm", result.stderr)

    def test_recursive_rm_in_safe_roots_allowed(self) -> None:
        home = str(Path.home())
        for cmd in [
            "rm -r $TMPDIR/scratch",
            "rm -r ${TMPDIR}/a/b",
            f"rm -r {home}/drafts/x",
            "rm -r ~/drafts/x/y",
            "rm -r ~/code/app/.claude/worktrees/feat",
            "rm -r node_modules",
            "rm -r /work/web/node_modules/.cache",
            "rm -r .venv dist build",
            "rm -r src/__pycache__",
            "rm -r ~/.cache/uv",
            "rm -r -- dist",
            "rm -r /work/a/dist/*",
        ]:
            self.assertEqual(self.bash(cmd).returncode, 0, cmd)

    def test_non_recursive_rm_and_other_commands_allowed(self) -> None:
        for cmd in [
            "rm file.txt",
            "rm -f /work/a.log",
            "git add rm",
            "rm -r",
            "echo rm -r /",
        ]:
            self.assertEqual(self.bash(cmd).returncode, 0, cmd)

    def test_rm_rf_denied_anywhere_in_text(self) -> None:
        for cmd in [
            RM_RF + " $TMPDIR/x",
            f"echo '{RM_RF} /'",
            "rm " + "-fr dist",
            "rm " + "-r -f dist",
            "rm " + "--recursive --force dist",
            f"cat <<EOF\n{RM_RF} x\nEOF",
            f"ls # {RM_RF}",
            "rm x " + "-rf",
            "rm " + "-R x -f",
            "rm " + "'-rf' x",
            "/bin/rm " + "-rf x",
            '"rm" ' + "-rf x",
            "rm x " + "--recursive --force",
            "rm \\\n" + "-rf x",
            "ls && rm a " + "-f -r",
            "sudo rm " + "-fr x",
            "git rm " + "-rf x",
        ]:
            result = self.bash(cmd)
            self.assertEqual(result.returncode, 2, cmd)
            self.assertIn("move it to ~/.Trash", result.stderr)

    def test_unexpected_error_in_new_checks_fails_closed(self) -> None:
        result = run_hook(
            "rm-guard.py", {"tool_name": "Bash", "tool_input": {"command": 5}}
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("rm-guard failed", result.stderr)

    def test_sandbox_escape_allowed_after_rm_check(self) -> None:
        result = self.bash("git fetch origin 2>&1 | tail -3", escape=True)
        self.assertEqual(result.returncode, 0)
        decision = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "allow")
        self.assertEqual(self.bash(RM_RF + " dist", escape=True).returncode, 2)

    def test_force_push_and_hard_reset_blocked(self) -> None:
        for cmd in [
            "git push --force origin b",
            "git -C repo push -f",
            "git push origin +b",
            "git reset --" + "hard HEAD~1",
            "(git push -f)",
            'bash -c "git push -f"',
        ]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.bash(cmd).returncode, 2)

    def test_plain_push_and_soft_reset_allowed(self) -> None:
        quoted = 'git commit -m "fix\ngit reset --' + 'hard is blocked\nok"'
        for cmd in [
            "git push origin b",
            "git reset --soft HEAD~1",
            "cat <<EOF\ngit push -f\nEOF",
            quoted,
        ]:
            with self.subTest(cmd=cmd):
                self.assertEqual(self.bash(cmd).returncode, 0)

    def test_non_bash_tool_ignored(self) -> None:
        result = run_hook(
            "rm-guard.py", {"tool_name": "Read", "tool_input": {"command": RM_RF + " /"}}
        )
        self.assertEqual(result.returncode, 0)


class AgentModelGateTest(unittest.TestCase):
    def spawn(self, **tool_input: object) -> subprocess.CompletedProcess:
        return run_hook(
            "agent-model-gate.py", {"tool_name": "Agent", "tool_input": tool_input}
        )

    def test_builtins_without_model_get_their_default_injected(self) -> None:
        for agent, default in [("Explore", "haiku"), ("Plan", "sonnet"), ("claude", "sonnet")]:
            tool_input = {"prompt": "x", "subagent_type": agent}
            result = self.spawn(**tool_input)
            self.assertEqual(result.returncode, 0, agent)
            out = json.loads(result.stdout)["hookSpecificOutput"]
            self.assertEqual(out["permissionDecision"], "allow")
            self.assertEqual(
                out["updatedInput"], {**tool_input, "model": default}, agent
            )

    def test_explicit_model_passes_untouched(self) -> None:
        for model in ["sonnet", "haiku"]:
            result = self.spawn(prompt="x", subagent_type="Explore", model=model)
            self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_opus_on_builtin_blocked(self) -> None:
        self.assertEqual(
            self.spawn(prompt="x", subagent_type="Explore", model="opus").returncode, 2
        )

    def test_unknown_unpinned_agent_without_model_blocked(self) -> None:
        self.assertEqual(
            self.spawn(prompt="x", subagent_type="no-such-agent-xyz").returncode, 2
        )

    def test_opus_blocked_without_override_config(self) -> None:
        result = self.spawn(prompt="x", subagent_type="no-such-agent-xyz", model="opus")
        self.assertEqual(result.returncode, 2)


class EnvFileGuardTest(unittest.TestCase):
    def edit(self, name: str, tool: str = "Edit") -> subprocess.CompletedProcess:
        return run_hook(
            "env-file-guard.py",
            {"tool_name": tool, "tool_input": {"file_path": f"/repo/{name}"}},
        )

    def test_template_env_files_allowed(self) -> None:
        for name in (
            ".env.example",
            ".env.local.example",
            ".env.sample",
            ".env.template",
        ):
            self.assertEqual(self.edit(name).returncode, 0, name)

    def test_real_env_files_blocked(self) -> None:
        for name in (".env.production", ".env.local"):
            for tool in ("Edit", "Write", "MultiEdit"):
                self.assertEqual(self.edit(name, tool).returncode, 2, name)

    def test_plain_env_and_lookalikes_not_affected(self) -> None:
        for name in (".env", "foo.env", "env.production"):
            self.assertEqual(self.edit(name).returncode, 0, name)


class DraftsLayoutGuardTest(unittest.TestCase):
    ENV = {"DRAFTS_DIR": "/home/u/drafts", "NOTES_DIR": "/home/u/notes"}

    def write(self, root: str, *parts: str) -> subprocess.CompletedProcess:
        path = str(Path("/home/u", root, *parts))
        return run_hook(
            "drafts-layout-guard.py",
            {"tool_name": "Write", "tool_input": {"file_path": path}},
            self.ENV,
        )

    def test_project_paths_allowed(self) -> None:
        self.assertEqual(
            self.write("drafts", "projects", "app", "ABC-1", "x.md").returncode, 0
        )
        self.assertEqual(self.write("notes", "projects", "x", "y.md").returncode, 0)

    def test_new_drafts_top_level_blocked_with_target(self) -> None:
        result = self.write("drafts", "ABC-9999", "x.md")
        self.assertEqual(result.returncode, 2)
        self.assertIn("drafts/projects/", result.stderr)

    def test_new_notes_top_level_blocked(self) -> None:
        self.assertEqual(self.write("notes", "scratch", "x.md").returncode, 2)

    def test_other_paths_ignored(self) -> None:
        self.assertEqual(self.write("code", "app", "x.md").returncode, 0)


class LayerConfigTest(unittest.TestCase):
    """Data a layer ships in hooks.d adds to the defaults; without it nothing changes."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.conf = self.root / "hooks.d"
        self.conf.mkdir()
        self.env = {
            "HOOKS_CONFIG_DIR": str(self.conf),
            "DRAFTS_DIR": str(self.root / "drafts"),
            "NOTES_DIR": str(self.root / "notes"),
        }
        self.repo = self.root / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)

    def config(self, name: str, data: dict) -> None:
        (self.conf / name).write_text(json.dumps(data))

    def write(self, root: str, *parts: str) -> subprocess.CompletedProcess:
        path = str(self.root.joinpath(root, *parts))
        return run_hook(
            "drafts-layout-guard.py",
            {"tool_name": "Write", "tool_input": {"file_path": path}},
            self.env,
        )

    def bash(self, command: str) -> subprocess.CompletedProcess:
        return run_hook(
            "pre-commit-guard.py",
            {
                "tool_name": "Bash",
                "cwd": str(self.repo),
                "tool_input": {"command": command},
            },
            self.env,
        )

    def test_opus_override_agents_added(self) -> None:
        spawn = {
            "tool_name": "Agent",
            "tool_input": {"prompt": "x", "subagent_type": "audit-x", "model": "opus"},
        }
        self.assertEqual(run_hook("agent-model-gate.py", spawn, self.env).returncode, 2)
        self.config("a.json", {"opus_override": ["audit-x"]})
        self.assertEqual(run_hook("agent-model-gate.py", spawn, self.env).returncode, 0)

    def test_drafts_and_notes_folders_added_across_files(self) -> None:
        self.assertEqual(self.write("drafts", "audits", "x.md").returncode, 2)
        self.config("a.json", {"drafts_allowed": ["audits"]})
        self.config("b.json", {"drafts_allowed": ["demos"], "notes_allowed": ["adr"]})
        for root, top in (("drafts", "audits"), ("drafts", "demos"), ("notes", "adr")):
            self.assertEqual(self.write(root, top, "x.md").returncode, 0, top)
        self.assertEqual(self.write("drafts", "other", "x.md").returncode, 2)

    def test_retired_path_blocked_with_redirect(self) -> None:
        retired = self.root / "code" / "_notes"
        self.config("a.json", {"retired_paths": [str(retired)]})
        result = run_hook(
            "drafts-layout-guard.py",
            {"tool_name": "Write", "tool_input": {"file_path": str(retired / "x.md")}},
            self.env,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("retired", result.stderr)

    def test_lint_skipped_folder_added(self) -> None:
        code = (
            "import importlib.util as u; s = u.spec_from_file_location('g', 'notes-lint-guard.py'); "
            "m = u.module_from_spec(s); s.loader.exec_module(m); print(sorted(m.SKIPPED))"
        )
        run = lambda: (  # noqa: E731
            subprocess.run(
                [sys.executable, "-c", code],
                cwd=HOOKS,
                env={**os.environ, **self.env},
                capture_output=True,
                text=True,
            ).stdout
        )
        self.assertNotIn("adr", run())
        self.config("a.json", {"lint_skipped": ["adr"]})
        self.assertIn("'adr'", run())
        self.assertIn("'templates'", run())

    def test_ticket_key_required_in_title_unless_project_exempt(self) -> None:
        command = "glab mr create --title 'Add a thing'"
        self.assertEqual(self.bash(command).returncode, 0)
        self.config(
            "a.json",
            {
                "change": {
                    "title_requires_ticket": True,
                    "ticket_exempt_projects": ["grp/tools/"],
                }
            },
        )
        self.assertEqual(self.bash(command).returncode, 2)
        self.assertEqual(
            self.bash("glab mr create --title 'ABC-12 Add a thing'").returncode, 0
        )
        subprocess.run(
            ["git", "remote", "add", "origin", "git@host:grp/tools/x.git"],
            cwd=self.repo,
            check=True,
        )
        self.assertEqual(self.bash(command).returncode, 0)

    def test_command_cd_and_repo_flag_pick_the_exempt_project(self) -> None:
        self.config(
            "a.json",
            {
                "change": {
                    "title_requires_ticket": True,
                    "ticket_exempt_projects": ["jadamsx/"],
                }
            },
        )
        other = self.root / "other"
        other.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=other, check=True)
        subprocess.run(
            ["git", "remote", "add", "origin", "git@github.com:jadamsx/x.git"],
            cwd=other,
            check=True,
        )
        create = 'gh pr create --title "🔧 No ticket"'
        self.assertEqual(self.bash(f"cd {other} && {create}").returncode, 0)
        self.assertEqual(self.bash(create).returncode, 2)
        self.assertEqual(self.bash(f"{create} --repo jadamsx/x").returncode, 0)

    def test_gitmoji_and_commit_ticket_rules(self) -> None:
        self.config(
            "a.json",
            {
                "change": {
                    "require_gitmoji": True,
                    "commit_forbids_ticket": True,
                    "commit_ticket_key": "ABC-\\d+",
                }
            },
        )
        self.assertEqual(self.bash('git commit -m "Plain"').returncode, 2)
        self.assertEqual(
            self.bash('git commit -m "\U0001f41b ABC-1 Fix"').returncode, 2
        )
        self.assertEqual(
            self.bash('git commit -m "\U0001f41b Fix UTF-8 reads"').returncode, 0
        )

    def test_mcp_change_tool_checked_and_bot_text_cut(self) -> None:
        payload = {
            "tool_name": "mcp__scm__create_merge_request",
            "cwd": str(self.repo),
            "tool_input": {
                "project_id": "grp/x",
                "title": "T",
                "description": "ok\n___\n" + "x" * 4000,
            },
        }
        self.assertEqual(
            run_hook("pre-commit-guard.py", payload, self.env).returncode, 2
        )
        self.config("a.json", {"change": {"description_cut_markers": ["\n___"]}})
        self.assertEqual(
            run_hook("pre-commit-guard.py", payload, self.env).returncode, 0
        )

    def test_extra_placeholder_blocks_push(self) -> None:
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        fake = bin_dir / "gh"
        fake.write_text(
            '#!/bin/sh\necho \'{"title": "T", "body": "XXX-", "reviewDecision": ""}\'\n'
        )
        fake.chmod(0o755)
        env = {**self.env, "PATH": f"{bin_dir}:{os.environ['PATH']}"}
        payload = {
            "tool_name": "Bash",
            "cwd": str(self.repo),
            "tool_input": {"command": "git push"},
        }
        self.assertEqual(run_hook("pre-push-guard.py", payload, env).returncode, 0)
        self.config("a.json", {"change": {"placeholders": ["XXX-"]}})
        self.assertEqual(run_hook("pre-push-guard.py", payload, env).returncode, 2)


class NoMarkerTest(unittest.TestCase):
    def test_push_needs_no_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
            payload = {"tool_name": "Bash", "cwd": tmp, "tool_input": {"command": "git push"}}
            self.assertEqual(run_hook("pre-push-guard.py", payload).returncode, 0)

    def test_tag_and_delete_pushes_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
            for command in (
                "git push origin --tags",
                "git push origin refs/tags/v1",
                "git push origin --delete old",
            ):
                payload = {"tool_name": "Bash", "cwd": tmp, "tool_input": {"command": command}}
                self.assertEqual(run_hook("pre-push-guard.py", payload).returncode, 0, command)


if __name__ == "__main__":
    unittest.main()


class RemotePathTest(unittest.TestCase):
    def test_every_remote_form_gives_the_project_path(self) -> None:
        sys.path.insert(0, str(HOOKS))
        from hook_config import REMOTE_PATH_RE

        cases = {
            "https://github.com/owner/repo.git": "owner/repo",
            "https://gitlab.com/group/sub/repo": "group/sub/repo",
            "git@github.com:owner/repo.git": "owner/repo",
            "ssh://git@host:22/group/sub/repo.git": "group/sub/repo",
        }
        for url, path in cases.items():
            found = REMOTE_PATH_RE.search(url)
            self.assertEqual(found and found.group(1), path, url)
