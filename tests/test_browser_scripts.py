import struct
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "lib"))
import browser_common  # noqa: E402


def load_script(name: str):
    return SourceFileLoader(
        name.replace("-", "_"), str(REPO / "bin" / name)
    ).load_module()


class ArgumentTest(unittest.TestCase):
    def test_viewport_parses_and_rejects_garbage(self) -> None:
        self.assertEqual(
            browser_common.parse_viewport("1440x900"), {"width": 1440, "height": 900}
        )
        with self.assertRaises(browser_common.BrowserSetupError):
            browser_common.parse_viewport("wide")

    def test_missing_state_names_the_login_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            browser_common.STATE_DIR = Path(tmp)
            with self.assertRaisesRegex(
                browser_common.BrowserSetupError, "browser-login dev"
            ):
                browser_common.load_state("dev")
            (Path(tmp) / "dev.json").write_text("{}")
            self.assertEqual(
                browser_common.load_state("dev"), str(Path(tmp) / "dev.json")
            )
            self.assertIsNone(browser_common.load_state(None))

    def test_shot_defaults(self) -> None:
        args = load_script("shot").parse_args(["http://x"])
        self.assertEqual(
            (args.viewport, args.full_page, args.env), ("1440x900", False, None)
        )

    def test_shot_turns_a_path_into_a_file_url(self) -> None:
        self.assertTrue(load_script("shot").resolve_url(__file__).startswith("file://"))
        self.assertEqual(
            load_script("shot").resolve_url("https://a.b/c"), "https://a.b/c"
        )

    def test_bad_viewport_exits_2_without_launching(self) -> None:
        result = subprocess.run(
            [REPO / "bin/shot", "http://x", "--viewport", "bad"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)


class ShotSmokeTest(unittest.TestCase):
    def test_local_page_is_captured_at_viewport_size(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            page, out = Path(tmp) / "p.html", Path(tmp) / "o.png"
            page.write_text("<html><body><h1>hi</h1></body></html>")
            result = subprocess.run(
                [REPO / "bin/shot", str(page), "--out", str(out)],
                capture_output=True,
                text=True,
            )
            if "Executable doesn't exist" in result.stderr:
                self.skipTest("no Chromium installed")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), str(out))
            self.assertEqual(struct.unpack(">II", out.read_bytes()[16:24]), (1440, 900))


if __name__ == "__main__":
    unittest.main()
