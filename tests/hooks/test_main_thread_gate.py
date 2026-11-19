import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / "claude/hooks/main-thread-gate.py"
spec = importlib.util.spec_from_file_location("main_thread_gate", HOOK)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

BLOCKED = [
    "pytest -q tests",
    "uv run pytest",
    "uv run --with pytest pytest -q tests",
    "uv run python -m pytest",
    "python3 -m unittest discover",
    "cd app && npm test",
    "npm run build",
    "pnpm lint",
    "pnpm run typecheck",
    "tsc --noEmit",
    "mypy src",
    "uv run ruff check .",
    "npx eslint .",
    "npx prettier --write .",
    "make test",
    "make -j4 build",
    "pre-commit run --all-files",
    "go test ./...",
    "cargo build --release",
    "CI=1 pytest",
    "git status && pytest",
]
ALLOWED = [
    "git status",
    "git log --oneline -5",
    "git diff",
    "git add -A",
    'git commit -m "fix pytest and npm test wiring"',
    "git push origin main",
    "ls -la",
    "cat tests/test_x.py",
    "grep -rn pytest .",
    "rg 'npm test'",
    "herdr tab list",
    "workspace notifications",
    "pnpm install",
    "npm install",
    "make deploy",
    "go mod tidy",
    "pre-commit install",
    "git commit -m \"$(cat <<'EOF'\n:sparkles: add pytest\npytest everywhere\nEOF\n)\"",
]


class MatcherTest(unittest.TestCase):
    def test_blocked_commands(self) -> None:
        for command in BLOCKED:
            with self.subTest(command=command):
                self.assertTrue(gate.blocked_command(command))

    def test_allowed_commands(self) -> None:
        for command in ALLOWED:
            with self.subTest(command=command):
                self.assertFalse(gate.blocked_command(command))


class PayloadTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.env = {
            **os.environ,
            "MAIN_THREAD_GATE_STATE": tmp.name,
            "NOTES_DIR": "/home/u/notes",
            "DRAFTS_DIR": "/home/u/drafts",
        }
        self.env.pop("WORKSTATION_REPORTS", None)

    def run_hook(self, payload: dict) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=self.env,
        )

    def pre(self, tool: str, tool_input: dict, **extra: str) -> dict:
        return {
            "hook_event_name": "PreToolUse",
            "session_id": "s1",
            "tool_name": tool,
            "tool_input": tool_input,
            **extra,
        }

    def test_main_thread_edit_blocked_naming_builder(self) -> None:
        result = self.run_hook(self.pre("Edit", {"file_path": "/repo/a.py"}))
        self.assertEqual(result.returncode, 2)
        self.assertIn("builder", result.stderr)

    def test_all_edit_tools_blocked(self) -> None:
        for tool in ("Write", "NotebookEdit", "MultiEdit"):
            self.assertEqual(
                self.run_hook(self.pre(tool, {"file_path": "/repo/a.py"})).returncode, 2
            )

    def test_main_thread_test_run_blocked_naming_digest(self) -> None:
        result = self.run_hook(self.pre("Bash", {"command": "uv run pytest"}))
        self.assertEqual(result.returncode, 2)
        self.assertIn("run-digest", result.stderr)

    def test_subagent_payload_allowed(self) -> None:
        extra = {"agent_id": "a1", "agent_type": "builder"}
        self.assertEqual(
            self.run_hook(
                self.pre("Edit", {"file_path": "/repo/a.py"}, **extra)
            ).returncode,
            0,
        )
        self.assertEqual(
            self.run_hook(self.pre("Bash", {"command": "pytest"}, **extra)).returncode,
            0,
        )

    def test_agent_type_alone_is_still_main_thread(self) -> None:
        payload = self.pre("Edit", {"file_path": "/repo/a.py"}, agent_type="custom")
        self.assertFalse(gate.is_subagent(payload))
        self.assertEqual(self.run_hook(payload).returncode, 2)

    def test_plain_bash_and_reads_allowed(self) -> None:
        self.assertEqual(
            self.run_hook(self.pre("Bash", {"command": "git status"})).returncode, 0
        )
        self.assertEqual(
            self.run_hook(self.pre("Read", {"file_path": "/repo/a.py"})).returncode, 0
        )

    def test_plan_and_memory_files_exempt(self) -> None:
        paths = (
            "/home/u/.claude/plans/x.md",
            "/home/u/.claude/projects/p/memory/m.md",
            "/home/u/drafts/ABC-1/plan.md",
            "/home/u/notes/projects/p/designs/ABC-1-x.md",
            "/home/u/drafts/notes/deep/idea.md",
        )
        for path in paths:
            for tool in ("Write", "Edit"):
                self.assertEqual(
                    self.run_hook(self.pre(tool, {"file_path": path})).returncode, 0
                )

    def test_code_under_notes_still_blocked(self) -> None:
        payload = self.pre("Write", {"file_path": "/home/u/notes/bin/tool.py"})
        self.assertEqual(self.run_hook(payload).returncode, 2)

    def test_code_under_drafts_still_blocked(self) -> None:
        payload = self.pre("Write", {"file_path": "/home/u/drafts/ABC-1/app.py"})
        self.assertEqual(self.run_hook(payload).returncode, 2)

    def test_vault_notes_resolved_before_matching(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name).resolve()
        (root / "real").mkdir()
        (root / "repo").mkdir()
        (root / "link").symlink_to(root / "real")
        (root / "real" / "escape").symlink_to(root / "repo")
        self.env["NOTES_DIR"] = str(root / "link")
        for path, code in (
            (root / "real" / "n.md", 0),
            (root / "link" / "n.md", 0),
            (root / "real" / "bin.py", 2),
            (root / "link" / ".." / "repo" / "a.md", 2),
            (root / "real" / ".." / "repo" / "a.md", 2),
            (root / "link" / "escape" / "a.md", 2),
            (root / "repo" / ".claude" / "plans" / ".." / ".." / "src" / "evil.py", 2),
            (root / "repo" / ".claude" / "projects" / "x.py", 2),
            (root / "repo" / ".claude" / "plans" / "p.md", 0),
        ):
            for tool in ("Write", "Edit"):
                result = self.run_hook(self.pre(tool, {"file_path": str(path)}))
                self.assertEqual(result.returncode, code, f"{tool} {path}")

    def test_settings_hook_commands_point_at_existing_files(self) -> None:
        settings = json.loads((HOOK.parent.parent / "settings.base.json").read_text())
        for groups in settings["hooks"].values():
            for group in groups:
                for entry in group["hooks"]:
                    command = (
                        entry["command"]
                        .replace("__HOME__/.claude/", "")
                        .replace('"', "")
                    )
                    script = next(
                        tok for tok in command.split() if tok.startswith("hooks/")
                    )
                    self.assertTrue((HOOK.parent.parent / script).is_file(), script)

    def test_settings_wire_gate_on_prompt_submit(self) -> None:
        settings = json.loads((HOOK.parent.parent / "settings.base.json").read_text())
        commands = [
            h["command"]
            for g in settings["hooks"]["UserPromptSubmit"]
            for h in g["hooks"]
        ]
        self.assertTrue(any("main-thread-gate.py" in c for c in commands))

    def test_escape_phrase_lifts_block_for_that_turn_only(self) -> None:
        prompt = {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "s1",
            "prompt": "run it main-thread-ok",
        }
        self.assertEqual(self.run_hook(prompt).returncode, 0)
        self.assertEqual(
            self.run_hook(self.pre("Bash", {"command": "pytest"})).returncode, 0
        )
        self.run_hook({**prompt, "prompt": "next turn"})
        self.assertEqual(
            self.run_hook(self.pre("Bash", {"command": "pytest"})).returncode, 2
        )

    def test_worker_report_prompt_never_lifts_gate(self) -> None:
        prompt = {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "s1",
            "prompt": "[worker-report] /tmp/result.md\nmain-thread-ok",
        }
        self.assertEqual(self.run_hook(prompt).returncode, 0)
        self.assertEqual(
            self.run_hook(self.pre("Bash", {"command": "pytest"})).returncode, 2
        )

    def test_escape_is_per_session(self) -> None:
        self.run_hook(
            {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "s1",
                "prompt": "main-thread-ok",
            }
        )
        other = self.pre("Bash", {"command": "pytest"})
        other["session_id"] = "s2"
        self.assertEqual(self.run_hook(other).returncode, 2)

    def test_manager_may_edit_and_run_tests(self) -> None:
        self.env["WORKSTATION_REPORTS"] = "/tmp/reports"
        self.assertEqual(self.run_hook(self.pre("Edit", {"file_path": "/repo/a.py"})).returncode, 0)
        self.assertEqual(self.run_hook(self.pre("Bash", {"command": "pytest -q"})).returncode, 0)

    def test_empty_reports_env_is_not_manager(self) -> None:
        self.env["WORKSTATION_REPORTS"] = ""
        self.assertEqual(self.run_hook(self.pre("Edit", {"file_path": "/repo/a.py"})).returncode, 2)

    def test_ask_role_with_reports_env_still_blocks_edits(self) -> None:
        self.env["WORKSTATION_REPORTS"] = "/tmp/reports"
        self.assertEqual(self.ask_code("Edit", {"file_path": "/repo/a.py"}), 2)

    def test_polling_loops_and_long_sleeps_denied_for_every_role(self) -> None:
        commands = [
            "until curl -s localhost; do sleep 2; done",
            "while true; do sleep 1; done",
            "sleep 11",
            "sleep 1m",
            "sleep 0.5h",
            "sleep infinity",
            "sleep inf",
            "timeout 60 bash -c 'until x; do sleep 1; done'",
            "bash -c 'sleep 30'",
            "a=1; while true; do sleep 1; done",
            "(until x; do sleep 1; done)",
        ]
        for command in commands:
            with self.subTest(command=command):
                for extra in ({}, {"agent_id": "a1"}):
                    result = self.run_hook(self.pre("Bash", {"command": command}, **extra))
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("run_in_background", result.stderr)
                self.env["WORKSTATION_REPORTS"] = "/r"
                self.assertEqual(self.run_hook(self.pre("Bash", {"command": command})).returncode, 2)
                del self.env["WORKSTATION_REPORTS"]

    def test_short_sleep_and_quoted_text_allowed(self) -> None:
        allowed = (
            "sleep 2",
            "sleep 10",
            'echo "while we sleep 30"',
            "git log --until=1d; sleep 2",
            "echo until done; sleep 2",
            "while read x; do echo $x; done < f; sleep 1",
            "cat <<EOF\nsleep 30\nEOF",
            "bash -c 'sleep 2'",
        )
        for command in allowed:
            self.assertEqual(self.run_hook(self.pre("Bash", {"command": command})).returncode, 0, command)

    def test_ask_gate_still_applies_beside_the_sleep_rule(self) -> None:
        self.assertEqual(self.ask_code("Bash", {"command": "ls"}), 0)
        self.assertEqual(self.ask_code("Bash", {"command": "make deploy"}), 2)

    def test_background_command_gets_timeout_wrapper(self) -> None:
        tool_input = {"command": "echo 'it''s'", "run_in_background": True}
        result = self.run_hook(self.pre("Bash", tool_input))
        self.assertEqual(result.returncode, 0)
        out = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        updated = out["updatedInput"]
        self.assertTrue(updated["run_in_background"])
        self.assertRegex(updated["command"], r"^(gtimeout 1200|perl -e 'alarm 1200; exec @ARGV' --) \"\$\{SHELL:-bash\}\" -c ")
        shell = subprocess.run(updated["command"], shell=True, text=True, capture_output=True)
        self.assertEqual(shell.stdout.strip(), "its")

    def test_wrapper_runs_under_the_user_shell_and_keeps_quoting(self) -> None:
        command = "echo \"a b\" '$HOME' $0; echo \"it's\""
        updated = gate.with_timeout(self.pre("Bash", {"command": command, "run_in_background": True}))
        env = {**os.environ, "SHELL": "/bin/sh"}
        shell = subprocess.run(updated["command"], shell=True, text=True, capture_output=True, env=env)
        self.assertEqual(shell.stdout.splitlines(), ["a b $HOME /bin/sh", "it's"])

    def test_commands_matched_by_permission_rules_are_not_wrapped(self) -> None:
        for command in (
            "git push --force",
            "FOO=1 git push",
            "gh pr merge 1",
            "glab mr list",
            "launchctl unload x",
            "rm -rf x",
            "sudo ls",
            "docker ps",
            "kubectl get pods",
            "shell-reap",
            "ps aux",
        ):
            with self.subTest(command=command):
                self.assertIsNone(gate.with_timeout(self.pre("Bash", {"command": command, "run_in_background": True})))
        wrapped = gate.with_timeout(self.pre("Bash", {"command": "git2 x; sleep 3", "run_in_background": True}))
        self.assertIn("-c ", wrapped["command"])

    def test_foreground_and_wrapped_commands_unchanged(self) -> None:
        self.assertEqual(self.run_hook(self.pre("Bash", {"command": "echo hi"})).stdout, "")
        wrapped = {"command": "gtimeout 1200 bash -c 'echo hi'", "run_in_background": True}
        self.assertEqual(self.run_hook(self.pre("Bash", wrapped)).stdout, "")
        perl = {"command": "perl -e 'alarm 1200; exec @ARGV' -- bash -c 'x'", "run_in_background": True}
        self.assertEqual(self.run_hook(self.pre("Bash", perl)).stdout, "")

    def ask_code(self, tool: str, tool_input: dict, **extra: str) -> int:
        self.env["WORKSTATION_ROLE"] = "ask"
        return self.run_hook(self.pre(tool, tool_input, **extra)).returncode

    def test_ask_role_blocks_herdr_and_manager_bypasses(self) -> None:
        for command in (
            "herdr agent prompt w1:p1 hello",
            "herdr agent send-keys w1:p1 Enter",
            "herdr pane send-text w1:p1 hi",
            'bash -c "herdr agent prompt w1:p1 hi"',
            "echo $(herdr agent prompt w1:p1 hi)",
            '"herdr" agent prompt w1:p1 hi',
            "herdr tab close w1:t1",
            "herdr pane read w1:p1 && herdr pane send-text w1:p1 x",
            'manager-send work "go"',
            "manager-close work",
            "manager-start x --prompt go",
            "herdr-manager close",
            "git status && herdr agent prompt w1:p1 hi",
            "python3 -c \"import subprocess; subprocess.run(['herdr','pane','send-text','p','x'])\"",
        ):
            self.assertEqual(self.ask_code("Bash", {"command": command}), 2, command)

    def test_ask_role_blocks_file_writing_bash(self) -> None:
        for command in (
            "sed -i s/a/b/ f.txt",
            "sed -n -i p f.txt",
            "echo x | tee f.txt",
            "echo x > f.txt",
            "echo x >> f.txt",
            "echo x 2> err.txt",
            "cat <<EOF > f.txt\nx\nEOF",
            "git commit -m x",
            "git add .",
            "git push",
            "git -C repo checkout main",
            "git reset --hard",
            "git rm a",
            "git mv a b",
            "git clean -fd",
            "git stash",
            "git apply p.diff",
            "git merge x",
            "git rebase x",
            "git cherry-pick x",
            "git status && rm a",
            "mv a b",
            "cp a b",
            "mkdir d",
            "touch a",
            "chmod +x a",
            "find . -name x -delete",
            "find . -exec rm {} ;",
            "curl -X POST http://h",
            "curl -X DELETE http://h",
            "gh api -X PATCH repos/o/r",
            "gh pr create",
            "gh pr merge 1",
            "gh issue comment 1",
            "gh pr edit 1",
            "gh issue close 1",
        ):
            self.assertEqual(self.ask_code("Bash", {"command": command}), 2, command)

    def test_ask_role_refuses_quote_tricks_substitution_and_chains(self) -> None:
        for command in (
            "h''erdr agent prompt w1:p1 hi",
            'h""erdr pane send-text w1:p1 hi',
            '"h"erdr agent prompt w1:p1 hi',
            "h\\erdr agent prompt w1:p1 hi",
            "manager''-send work go",
            "manager-''send work go",
            "`herdr agent prompt w1:p1 hi`",
            "echo `id`",
            "echo $(id)",
            'echo "$(id)"',
            'echo "`id`"',
            "echo ${HOME}",
            "<(ls)",
            "cat <(ls)",
            "cat < f",
            "ls; herdr agent prompt w1:p1 hi",
            "ls | python3 -c pass",
            "ls || rm a",
            "ls & rm a",
            "ls\nrm a",
            "ls && (rm a)",
            "$H agent prompt w1:p1 hi",
            "A=1 ls",
            "env herdr agent prompt w1:p1 hi",
            "/bin/rm a",
            "./ls",
            "xargs rm",
            "bash -c ls",
            "echo x >f",
            "echo x>f",
            "echo x >| f",
            "ls &> f",
            "ls >&2 > f",
            "git diff --output=f",
            "git log --output f",
            "git branch -D x",
            "git branch new",
            "git -c alias.x=!rm x",
            "rg --pre sh x",
            "gh api -XPATCH repos/o/r",
            "gh api repos/o/r -f a=b",
            "gh api --method POST repos/o/r",
            "glab api --method PUT projects/1",
            "curl -sXPOST http://h",
            "curl -o f http://h",
            "curl -d x http://h",
            "find . -fprint f",
            "echo 'unterminated",
            "find . \\\n-delete",
            "gh api -\\\nX POST repos/o/r",
            'find . -ex"$X"ec echo {} \\;',
            "ls $WORKSTATION_REPORTS_ROOT",
            "echo hi >&2x",
            "echo hi >&2/tmp/y",
            "gh auth status -t",
            "gh config get oauth_token",
            "glab auth status",
            "curl -s http://h",
            "git -c core.fsmonitor=x status",
            "file -C -m x",
            "gh api -iX POST repos/o/r",
            "gh api -if query=x graphql",
            "glab api -pX PUT projects/1",
            "gh api -iFa=b graphql",
            "gh api -fa=b graphql",
            "git diff --textconv",
            "git log -p --ext-diff",
            "git show --ext-diff HEAD",
            "git diff --no-index /dev/null ~/.aws/credentials",
            "git diff --no-index a b",
            "git -C ~ diff .zshenv .zshrc",
            "git -C ../other diff a b",
            "git log -p -- /etc/passwd",
            "git show HEAD:../x",
            "git diff ~/.ssh/id_rsa",
        ):
            self.assertEqual(self.ask_code("Bash", {"command": command}), 2, command)

    def test_ask_role_allows_quoted_args_variables_and_read_chains(self) -> None:
        for command in (
            "git log --format='%h %s' -3",
            'git log --format="%h > %s"',
            "cd repo && git status",
            "git status; git diff --stat | head -5",
            "git diff HEAD -- src/a.py",
            "git log main..HEAD",
            "gh api repos/o/r/pulls",
            "gh pr list || glab mr list",
            "h''erdr pane read w1:p1",
            "ls 2>&1 | wc -l",
        ):
            self.assertEqual(self.ask_code("Bash", {"command": command}), 0, command)

    def test_ask_message_lists_the_allowed_commands_from_the_sets(self) -> None:
        self.env["WORKSTATION_ROLE"] = "ask"
        result = self.run_hook(self.pre("Edit", {"file_path": "/repo/a.py"}))
        for word in ("ls", "rg", "log", "blame", "pane read", "workspace get"):
            self.assertIn(word, result.stderr)

    def test_ask_role_blocks_non_readonly_agents_and_edits(self) -> None:
        for agent in ("builder", "builder-small", "rebase-resolver", "general-purpose", "explorer"):
            self.assertEqual(self.ask_code("Agent", {"subagent_type": agent}), 2, agent)
        for tool in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
            self.assertEqual(self.ask_code(tool, {"file_path": "/home/u/notes/a.md"}), 2, tool)
            self.assertEqual(self.ask_code(tool, {"file_path": "/repo/a.py"}, agent_id="a1"), 2, tool)
        self.assertEqual(self.ask_code("SendMessage", {"to": "x", "message": "hi"}), 2)
        sub = {"command": "herdr agent prompt w1:p1 hi"}
        self.assertEqual(self.ask_code("Bash", sub, agent_id="a1"), 2)

    def test_ask_role_keeps_reads_and_cannot_be_escaped(self) -> None:
        for command in (
            "herdr pane read w1:p1",
            "herdr pane list",
            "herdr tab list",
            "herdr workspace list",
            "herdr workspace get w1",
            "herdr agent list",
            "git log -3",
            "gh pr list",
            "git status",
            "git diff --stat",
            "git show HEAD",
            "git branch -a",
            "git -C repo log --oneline",
            "rg foo src",
            "grep '>' file",
            "grep -rn \"a > b\" .",
            "cat a | head -5",
            "tail -n 3 a",
            "ls -la 2>/dev/null",
            "ls > /dev/null 2>&1",
            "wc -l a",
            "find . -name x",
            "gh pr view 1",
            "glab mr list",
        ):
            self.assertEqual(self.ask_code("Bash", {"command": command}), 0, command)
        for agent in ("code-locator", "researcher", "run-digest", "web-fetch", "Explore"):
            self.assertEqual(self.ask_code("Agent", {"subagent_type": agent}), 0, agent)
        self.run_hook({"hook_event_name": "UserPromptSubmit", "session_id": "s1", "prompt": "main-thread-ok"})
        self.assertEqual(self.ask_code("Bash", {"command": "herdr agent prompt w1:p1 hi"}), 2)
        self.assertEqual(self.ask_code("Edit", {"file_path": "/repo/a.py"}), 2)

    def test_other_roles_may_prompt_and_spawn_builders(self) -> None:
        for env in ({}, {"WORKSTATION_ROLE": "lead"}):
            self.env.pop("WORKSTATION_ROLE", None)
            self.env.update(env)
            self.assertEqual(self.run_hook(self.pre("Bash", {"command": "herdr agent prompt w1:p1 hi"})).returncode, 0)
            self.assertEqual(self.run_hook(self.pre("Agent", {"subagent_type": "builder"})).returncode, 0)

    def test_settings_route_agent_spawns_to_the_gate(self) -> None:
        settings = json.loads((HOOK.parent.parent / "settings.base.json").read_text())
        matchers = [g["matcher"] for g in settings["hooks"]["PreToolUse"] if "main-thread-gate.py" in g["hooks"][0]["command"]]
        self.assertTrue(any("Agent" in m.split("|") for m in matchers))

    def test_malformed_payload_fails_closed_for_ask_only(self) -> None:
        self.env["WORKSTATION_ROLE"] = "ask"
        for raw in ("nope", "[1]"):
            result = subprocess.run([sys.executable, str(HOOK)], input=raw, text=True, capture_output=True, env=self.env)
            self.assertEqual(result.returncode, 2, raw)

    def test_malformed_payload_fails_open(self) -> None:
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input="nope",
            text=True,
            capture_output=True,
            env=self.env,
        )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
