import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[2] / "claude/hooks"
BRIEF = Path(__file__).resolve().parents[2] / "claude/templates/manager-brief.md"


def run_hook(name: str, payload: dict, reports: Path | None) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "WORKSTATION_REPORTS"}
    if reports is not None:
        env["WORKSTATION_REPORTS"] = str(reports)
    return subprocess.run(
        [sys.executable, str(HOOKS / name)], input=json.dumps(payload), text=True, capture_output=True, env=env
    )


class ReportsCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name).resolve()
        self.reports = self.base / "reports"
        self.reports.mkdir()


class ReportFormatGuardTest(ReportsCase):
    def write(self, name: str, content: str, reports: Path | None = ...) -> subprocess.CompletedProcess:
        return run_hook(
            "report-format-guard.py",
            {"tool_name": "Write", "tool_input": {"file_path": str(self.reports / name), "content": content}},
            self.reports if reports is ... else reports,
        )

    def bash(self, command: str) -> subprocess.CompletedProcess:
        return run_hook("report-format-guard.py", {"tool_name": "Bash", "tool_input": {"command": command}}, self.reports)

    def test_write_of_a_well_formed_report_passes(self) -> None:
        self.assertEqual(self.write("result-20250101-120000.md", "Status: done\nbody").returncode, 0)
        self.assertEqual(self.write("result-1.md", "Status: decision\nq").returncode, 0)
        self.assertEqual(self.write(".draft", "Status: done\nbody").returncode, 0)

    def test_write_with_a_wrong_name_is_blocked_with_the_exact_command(self) -> None:
        result = self.write("report.md", "Status: done\n")
        self.assertEqual(result.returncode, 2)
        self.assertIn('mv "$WORKSTATION_REPORTS/.draft" "$WORKSTATION_REPORTS/result-$(date +%Y%m%d-%H%M%S).md"', result.stderr)

    def test_write_without_a_status_first_line_is_blocked(self) -> None:
        for content in ("Done\n", "\nSummary\nStatus: done", "Status: finished\n"):
            result = self.write("result-1.md", content)
            self.assertEqual(result.returncode, 2, content)
            self.assertIn("Status: decision", result.stderr)

    def test_write_outside_the_folder_or_without_the_variable_passes(self) -> None:
        other = run_hook(
            "report-format-guard.py",
            {"tool_name": "Write", "tool_input": {"file_path": str(self.base / "notes.md"), "content": "x"}},
            self.reports,
        )
        self.assertEqual(other.returncode, 0)
        self.assertEqual(self.write("report.md", "x", reports=None).returncode, 0)

    def test_bash_heredoc_and_inline_content_are_checked(self) -> None:
        good = f"cat > \"$WORKSTATION_REPORTS/result-1.md\" <<'EOF'\nStatus: done\nbody\nEOF"
        bad = f"cat > {self.reports}/result-1.md <<'EOF'\nSummary\nEOF"
        self.assertEqual(self.bash(good).returncode, 0)
        self.assertEqual(self.bash(bad).returncode, 2)
        self.assertEqual(self.bash(f"printf 'Status: done\\nx' > {self.reports}/result-1.md").returncode, 0)
        self.assertEqual(self.bash(f"echo 'all fine' > {self.reports}/result-1.md").returncode, 2)

    def test_bash_wrong_names_are_blocked_for_each_way_of_writing(self) -> None:
        for command in (
            'echo x > "$WORKSTATION_REPORTS/notes.txt"',
            'echo x | tee "${WORKSTATION_REPORTS}/out.md"',
            f"cp /tmp/a {self.reports}/copy.md",
            'mv /tmp/a "$WORKSTATION_REPORTS/"',
            'touch "$WORKSTATION_REPORTS/x"',
        ):
            self.assertEqual(self.bash(command).returncode, 2, command)

    def test_bash_move_of_the_draft_checks_the_draft_content(self) -> None:
        move = 'mv "$WORKSTATION_REPORTS/.draft" "$WORKSTATION_REPORTS/result-$(date +%Y%m%d-%H%M%S).md"'
        (self.reports / ".draft").write_text("notes\n")
        self.assertEqual(self.bash(move).returncode, 2)
        (self.reports / ".draft").write_text("Status: done\nbody\n")
        self.assertEqual(self.bash(move).returncode, 0)
        self.assertEqual(self.bash(f'mv "$WORKSTATION_REPORTS/.draft" "$WORKSTATION_REPORTS/final.md"').returncode, 2)

    def test_bash_draft_write_and_reads_pass(self) -> None:
        for command in (
            'cat > "$WORKSTATION_REPORTS/.draft"',
            'ls "$WORKSTATION_REPORTS"',
            'cat "$WORKSTATION_REPORTS/result-1.md"',
            "git status",
        ):
            self.assertEqual(self.bash(command).returncode, 0, command)

    def test_bash_does_nothing_without_the_variable(self) -> None:
        result = run_hook(
            "report-format-guard.py",
            {"tool_name": "Bash", "tool_input": {"command": f"echo x > {self.reports}/notes.txt"}},
            None,
        )
        self.assertEqual(result.returncode, 0)


class ManagerBriefInjectTest(ReportsCase):
    def start(self, source: str, reports: Path | None) -> subprocess.CompletedProcess:
        return run_hook("manager-brief-inject.py", {"source": source}, reports)

    def test_compact_and_clear_return_the_brief_as_context(self) -> None:
        for source in ("compact", "clear"):
            out = json.loads(self.start(source, self.reports).stdout)["hookSpecificOutput"]
            self.assertEqual(out["hookEventName"], "SessionStart")
            self.assertEqual(out["additionalContext"], BRIEF.read_text())

    def test_other_sources_and_non_manager_sessions_print_nothing(self) -> None:
        self.assertEqual(self.start("startup", self.reports).stdout, "")
        self.assertEqual(self.start("resume", self.reports).stdout, "")
        self.assertEqual(self.start("compact", None).stdout, "")


if __name__ == "__main__":
    unittest.main()
