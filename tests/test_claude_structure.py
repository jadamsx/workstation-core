import re
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = ROOT / "claude"
SKILLS = sorted((CLAUDE / "skills").glob("*/SKILL.md"))
SKILL_NAMES = [p.parent.name for p in SKILLS]
LAYERS = ("engines", "checklists", "disciplines", "agents")
LAYER_FILES = [p for d in LAYERS for p in sorted((CLAUDE / d).glob("*.md"))]
ALL_MD = sorted(p for p in CLAUDE.rglob("*.md") if "hooks" not in p.parts)
SHIP = CLAUDE / "engines/ship.md"
SKILL_LINE_CAP = 60
LONG_STANDALONE = {"diagrams", "handoff-write"}
HEADINGS = ["## When", "## Inputs", "## Differs", "## Output"]
ENGINES = {"plan", "build", "review", "write", "ship"}
FORGE_WORDS = re.compile(r"\bgh\b|glab|GitHub|GitLab|Jira|\bPRs?\b|\bMRs?\b")
FORGE_EXCEPTIONS: dict[str, str] = {}
OLD_AGENTS = [
    "edit-builder",
    "node-builder",
    "test-run-digest",
    "ci-log-digest",
    "ticket-digest",
    "change-status",
]
PATH_REF = re.compile(r"\b(engines|checklists|disciplines|agents)/([a-z0-9-]+)\.md")
MIN_WORDS = 12
SKIP_DUP_DIRS = {"templates"}


def rel(path: Path) -> str:
    return str(path.relative_to(CLAUDE))


def frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}
    return dict(
        line.split(":", 1) for line in match.group(1).splitlines() if ":" in line
    )


class SkillShape(unittest.TestCase):
    def test_skill_frontmatter_and_headings(self):
        for path in SKILLS:
            text = path.read_text()
            fm = {k.strip(): v.strip() for k, v in frontmatter(text).items()}
            with self.subTest(skill=rel(path)):
                self.assertEqual(fm.get("name"), path.parent.name)
                self.assertTrue(fm.get("description"), "description missing")
                self.assertLessEqual(len(fm["description"]), 200)
                for heading in HEADINGS:
                    self.assertRegex(text, rf"(?m)^{heading}\b")
                if "engine" in fm:
                    self.assertIn(fm["engine"], ENGINES)
                    self.assertIn("params", fm)
                    self.assertTrue((CLAUDE / f"engines/{fm['engine']}.md").exists())

    def test_skill_length(self):
        for path in SKILLS:
            if path.parent.name in LONG_STANDALONE:
                continue
            lines = len(path.read_text().splitlines())
            with self.subTest(skill=rel(path)):
                self.assertLessEqual(lines, SKILL_LINE_CAP)


class Layering(unittest.TestCase):
    def test_lower_layers_name_no_skill(self):
        names = "|".join(re.escape(n) for n in SKILL_NAMES)
        hyphenated = "|".join(re.escape(n) for n in SKILL_NAMES if "-" in n)
        pattern = re.compile(
            rf"(?<![\w/.~-])/({names})(?![\w/-])|skills/({names})\b|(?<![\w/.-])({hyphenated})(?![\w/-])"
        )
        for path in LAYER_FILES:
            for n, line in enumerate(path.read_text().splitlines(), 1):
                with self.subTest(at=f"{rel(path)}:{n}"):
                    self.assertIsNone(pattern.search(line), line)

    def test_forge_words_only_in_ship(self):
        for path in ALL_MD:
            if path == SHIP or rel(path) in FORGE_EXCEPTIONS:
                continue
            for n, line in enumerate(path.read_text().splitlines(), 1):
                with self.subTest(at=f"{rel(path)}:{n}"):
                    self.assertIsNone(FORGE_WORDS.search(line), line)

    def test_no_forge_word_or_gitlab_change_syntax(self):
        banned = re.compile(r"(?i)forge|(?<![\w\[])!(?:\d+|N)\b")
        files = [
            p
            for root in (CLAUDE, CLAUDE.parent / "docs")
            for p in sorted(root.rglob("*"))
            if p.is_file()
            and "__pycache__" not in p.parts
            and p.suffix in {".md", ".py", ".json", ".sh", ".txt"}
        ]
        for path in files:
            for n, line in enumerate(path.read_text().splitlines(), 1):
                with self.subTest(at=f"{path}:{n}"):
                    self.assertIsNone(banned.search(line), line)

    def test_referenced_paths_resolve(self):
        for path in ALL_MD:
            for n, line in enumerate(path.read_text().splitlines(), 1):
                for match in PATH_REF.finditer(line):
                    target = CLAUDE / match.group(0)
                    with self.subTest(at=f"{rel(path)}:{n}", ref=match.group(0)):
                        self.assertTrue(target.exists())

    def test_no_old_agent_names(self):
        for path in ALL_MD:
            text = path.read_text()
            for old in OLD_AGENTS:
                with self.subTest(file=rel(path), name=old):
                    self.assertNotIn(old, text)


class Prose(unittest.TestCase):
    def test_no_assumed_main_branch(self):
        for path in sorted(p for d in (CLAUDE, ROOT / "docs") for p in d.rglob("*.md")):
            with self.subTest(file=str(path.relative_to(ROOT))):
                self.assertNotIn("origin/main", path.read_text())

    def test_no_em_dashes(self):
        for path in ALL_MD:
            with self.subTest(file=rel(path)):
                self.assertNotIn("—", path.read_text())

    def test_no_sentence_in_two_files(self):
        seen: dict[str, set[str]] = defaultdict(set)
        for path in ALL_MD:
            if path.parent.name in SKIP_DUP_DIRS:
                continue
            body = re.sub(r"\A---\n.*?\n---\n", "", path.read_text(), flags=re.S)
            for chunk in re.split(r"(?<=[.!?])\s+|\n+", body):
                words = re.sub(
                    r"[^a-z0-9 ]", "", chunk.lower().replace("`", "")
                ).split()
                if len(words) >= MIN_WORDS:
                    seen[" ".join(words)].add(rel(path))
        dupes = {s: sorted(f) for s, f in seen.items() if len(f) > 1}
        self.assertEqual(dupes, {}, "\n".join(f"{f}: {s}" for s, f in dupes.items()))


class Intensity(unittest.TestCase):
    DOCS = sorted((CLAUDE.parent / "docs").rglob("*.md"))

    def test_old_tier_scale_is_gone(self):
        old = re.compile(r"\btier\b|`(?:quick|standard|critical)`", re.I)
        for path in ALL_MD + self.DOCS:
            with self.subTest(file=str(path)):
                self.assertIsNone(old.search(path.read_text()))

    def test_intensity_values_are_the_one_scale(self):
        value = re.compile(r"intensity:\s*([A-Za-z-]+)")
        for path in ALL_MD + self.DOCS:
            for found in value.findall(path.read_text()):
                with self.subTest(file=str(path), value=found):
                    self.assertIn(found, {"light", "medium", "intense"})


if __name__ == "__main__":
    unittest.main()
