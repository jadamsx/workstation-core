import importlib.util
import os
import subprocess
import tempfile
import unittest
import urllib.request
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "bin/md-pdf"
FIXTURES = REPO / "tests/fixtures"
HOW_TO_RUN = "run with: uv run --with markdown --with pytest python -m pytest tests/test_md_pdf.py"
CDN_PROBE = "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"


def load_script():
    loader = SourceFileLoader("md_pdf_under_test", str(SCRIPT))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    return module


def run(note: Path, out: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(SCRIPT), str(note), str(out)], capture_output=True, text=True, timeout=180
    )


def diagram(html: str) -> str:
    return html.split('<div class="mermaid">', 1)[1].split("</div>", 1)[0]


class PrepareTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.md_pdf = load_script()
        except ModuleNotFoundError as err:
            raise unittest.SkipTest(f"{err.name} is not installed; {HOW_TO_RUN}") from err

    def test_front_matter_is_stripped_and_mermaid_becomes_a_div(self) -> None:
        html, blocks = self.md_pdf.render_html(
            "---\ntitle: x\n---\n# Head\n\n```mermaid\nflowchart LR\n  A --> B\n```\n"
        )
        self.assertNotIn("title: x", html)
        self.assertEqual(blocks, 1)
        self.assertIn('<div class="mermaid">flowchart LR', html)
        self.assertNotIn("<code", html)

    def test_other_fences_stay_code(self) -> None:
        html, blocks = self.md_pdf.render_html("```python\nprint(1)\n```\n")
        self.assertEqual(blocks, 0)
        self.assertIn("<code", html)

    def test_crlf_note_strips_front_matter_and_finds_the_fence(self) -> None:
        text = "---\r\ntitle: x\r\n---\r\n# H\r\n\r\n```mermaid  \r\nflowchart LR\r\n  A --> B\r\n```  \r\n"
        html, blocks = self.md_pdf.render_html(text)
        self.assertNotIn("title: x", html)
        self.assertEqual(blocks, 1)
        self.assertEqual(diagram(html), "flowchart LR\n  A --&gt; B")

    def test_list_nested_fence_is_dedented(self) -> None:
        html, blocks = self.md_pdf.render_html(
            "- item\n\n    ```mermaid\n    flowchart LR\n      A --> B\n    ```\n"
        )
        self.assertEqual(blocks, 1)
        self.assertEqual(diagram(html), "flowchart LR\n  A --&gt; B")

    def test_note_text_resembling_a_placeholder_stays(self) -> None:
        html, _ = self.md_pdf.render_html("MERMAIDBLOCK0\n\n```mermaid\nflowchart LR\n  A --> B\n```\n")
        self.assertIn("MERMAIDBLOCK0", html)
        self.assertEqual(html.count('<div class="mermaid">'), 1)

    def test_csp_allows_only_pinned_script_and_our_init(self) -> None:
        html, _ = self.md_pdf.render_html("<script>alert(1)</script>\n")
        self.assertIn("Content-Security-Policy", html)
        csp = self.md_pdf.content_security_policy()
        self.assertIn("default-src 'none'", csp)
        self.assertNotIn("unsafe-inline'; img", csp.split("style-src")[0])
        self.assertIn(f'integrity="{self.md_pdf.MERMAID_SRI}"', html)

    def test_prose_about_syntax_errors_is_not_a_parse_error(self) -> None:
        self.md_pdf.check_diagrams(
            '<p>Syntax error in text</p><div class="mermaid" data-processed="true"><svg></svg></div>', 1
        )

    def test_error_svg_is_a_parse_error(self) -> None:
        with self.assertRaisesRegex(self.md_pdf.RenderError, "parse error"):
            self.md_pdf.check_diagrams('<svg aria-roledescription="error"></svg>', 1)

    def test_undrawn_diagram_is_not_called_a_parse_error(self) -> None:
        with self.assertRaisesRegex(self.md_pdf.RenderError, "drew 0 of 1"):
            self.md_pdf.check_diagrams('<div class="mermaid">flowchart</div>', 1)


def render_environment_error() -> str:
    try:
        load_script().find_chrome()
    except ModuleNotFoundError as err:
        return f"{err.name} is not installed; {HOW_TO_RUN}"
    except Exception as err:
        return str(err)
    try:
        urllib.request.urlopen(CDN_PROBE, timeout=10).close()
    except OSError as err:
        return f"mermaid CDN unreachable: {err}"
    return ""


class RenderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        reason = render_environment_error()
        if reason:
            raise unittest.SkipTest(reason)

    def test_diagrams_render_to_an_a4_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "nested/dir/plan.pdf"
            result = run(FIXTURES / "md-pdf-good.md", out)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = out.read_bytes()
            self.assertTrue(data.startswith(b"%PDF"))
            self.assertRegex(data, rb"/MediaBox \[0 0 59[45]\.\d+ 841\.\d+\]")
            self.assertIn(str(out.resolve()), result.stdout)

    def test_broken_mermaid_exits_non_zero_naming_the_parse_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "bad.pdf"
            result = run(FIXTURES / "md-pdf-broken.md", out)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("parse error", result.stderr)
            self.assertFalse(out.exists())

    def test_failed_render_leaves_no_stale_pdf_counted_as_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "plan.pdf"
            out.write_bytes(b"%PDF-stale")
            result = run(FIXTURES / "md-pdf-broken.md", out)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(out.read_bytes(), b"%PDF-stale")

    def test_prose_mentioning_syntax_error_still_renders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "n.md"
            note.write_text("Mermaid shows Syntax error in text on a bad block.\n\n```mermaid\nflowchart LR\n  A --> B\n```\n")
            result = run(note, Path(tmp) / "n.pdf")
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_raw_html_in_a_note_does_not_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / "n.md"
            note.write_text(
                "<script>document.body.setAttribute('data-pwned','1')</script>\n\n"
                "```mermaid\nflowchart LR\n  A --> B\n```\n"
            )
            module = load_script()
            page, _ = module.render_html(note.read_text())
            html = Path(tmp) / "p.html"
            html.write_text(page)
            dom = subprocess.run(
                [module.find_chrome(), "--headless", "--disable-gpu", f"--user-data-dir={tmp}/prof",
                 "--virtual-time-budget=8000", "--dump-dom", html.as_uri()],
                capture_output=True, text=True, timeout=120,
            ).stdout
            self.assertNotIn("data-pwned", dom.split("<body", 1)[1].split(">", 1)[0])


class MissingChromeTest(unittest.TestCase):
    def test_missing_chrome_exits_non_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [str(SCRIPT), str(FIXTURES / "md-pdf-good.md"), str(Path(tmp) / "x.pdf")],
                capture_output=True,
                text=True,
                env={**os.environ, "MD_PDF_CHROME": "/nonexistent"},
                timeout=60,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("chrome", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
