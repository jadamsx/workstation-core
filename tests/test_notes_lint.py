import contextlib
import io
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from datetime import date, timedelta
from importlib.machinery import SourceFileLoader
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LINT = REPO / "bin/notes-lint"
notes_lint = SourceFileLoader("notes_lint_under_test", str(LINT)).load_module()

TODAY = date.today().isoformat()
RELATIONS = ["decided_by", "implements", "supersedes", "superseded_by", "related_adrs"]
LEGACY_HEADS = [
    "Approach",
    "Why",
    "Plan header",
    "Node table",
    "Progress",
    "Acceptance",
    "Decisions",
    "Traps",
    "Out",
    "Links",
]
V2_HEADS = [
    "Context and scope",
    "Goals and non-goals",
    "Design",
    "Alternatives considered",
    "Cross-cutting concerns",
    "User Scenarios & Testing",
    "Requirements",
    "Success Criteria",
    "Plan header",
    "Node table",
    "Progress",
    "Traceability",
    "Decisions",
    "Traps",
    "Out",
    "Links",
]
PROPOSAL_HEADS = [
    "Summary",
    "Problem",
    "Proposal",
    "Alternatives",
    "Costs and risks",
    "Ask and decision needed",
    "Links",
]
TEMPLATES = {
    "decision": (
        [
            "title",
            "aliases",
            "type",
            "status",
            "area",
            "project",
            "updated",
            "verified",
            "sources",
            *RELATIONS,
            "ticket",
        ],
        ["Context", "Decision", "Why", "Alternatives", "Links"],
    ),
    "design": (
        [
            "title",
            "aliases",
            "type",
            "status",
            "format",
            "ticket",
            "project",
            "date",
            "superseded_by",
            "mr",
            "area",
            "updated",
            "verified",
            "sources",
            "decided_by",
            "implements",
            "supersedes",
            "related_adrs",
        ],
        V2_HEADS,
    ),
    "proposal": (
        [
            "title",
            "aliases",
            "type",
            "status",
            "format",
            "ticket",
            "project",
            "date",
            "superseded_by",
            "mr",
            "area",
            "updated",
            "verified",
            "sources",
            "decided_by",
            "implements",
            "supersedes",
            "related_adrs",
        ],
        PROPOSAL_HEADS,
    ),
    "howto": (
        [
            "title",
            "aliases",
            "type",
            "status",
            "area",
            "updated",
            "verified",
            "sources",
            *RELATIONS,
            "ticket",
        ],
        ["Goal", "Steps", "Check it worked", "Links"],
    ),
    "project": (
        [
            "title",
            "aliases",
            "type",
            "status",
            "area",
            "updated",
            "verified",
            "sources",
            *RELATIONS,
            "ticket",
        ],
        ["What this stream is", "Current state", "Where things are", "Open", "Links"],
    ),
    "reference": (
        [
            "title",
            "aliases",
            "type",
            "status",
            "area",
            "updated",
            "verified",
            "sources",
            *RELATIONS,
            "ticket",
        ],
        ["Links"],
    ),
    "research": (
        [
            "title",
            "aliases",
            "type",
            "status",
            "area",
            "project",
            "updated",
            "verified",
            "sources",
            *RELATIONS,
            "ticket",
        ],
        ["Answer", "Evidence", "Confidence", "What would change it", "Links"],
    ),
    "review": (
        [
            "title",
            "aliases",
            "type",
            "status",
            "area",
            "project",
            "url",
            "state",
            "updated",
            "verified",
            "sources",
        ],
        ["Threads", "Recheck log", "Links"],
    ),
    "runbook": (
        [
            "title",
            "aliases",
            "type",
            "status",
            "area",
            "updated",
            "verified",
            "sources",
            *RELATIONS,
            "ticket",
        ],
        ["Diagnose", "Fix", "Escalate", "Links"],
    ),
}
LIST_KEYS = {"aliases", "sources", *RELATIONS}


def frontmatter(kind: str, base: bool = False, **over: str) -> str:
    defaults = {
        "title": "T",
        "type": kind,
        "status": "proposed" if kind == "design" else "current",
        "area": "platform",
        "updated": TODAY,
        "verified": TODAY,
        "date": TODAY,
        "ticket": "ABC-1" if kind == "design" else "[]",
    }
    lines = []
    for key in TEMPLATES[kind][0][:8] if base else TEMPLATES[kind][0]:
        if key == "format" and key not in over:
            continue
        default = "[]" if key in LIST_KEYS else defaults.get(key, "")
        value = over.get(key, default)
        lines.append(f"{key}: {value}".rstrip())
    return "---\n" + "\n".join(lines) + "\n---\n"


def body(
    kind: str, links: str, title: str = "A claim", heads: list[str] | None = None
) -> str:
    if heads is None:
        heads = LEGACY_HEADS if kind == "design" else TEMPLATES[kind][1]
    sections = "".join(f"## {h}\n\ntext\n\n" for h in heads if h != "Links")
    return f"# {title}\n\n{sections}## Links\n\n{links}\n"


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def make_vault(root: Path) -> None:
    for kind, (keys, heads) in TEMPLATES.items():
        write(
            root,
            f"templates/{kind}.md",
            "---\n"
            + "".join(f"{k}: []\n" if k in LIST_KEYS else f"{k}:\n" for k in keys)
            + "---\n# T\n\n"
            + "".join(f"## {h}\n" for h in heads),
        )
    index = frontmatter("reference", base=True, title="Home") + "# Home\n\n"
    index += "".join(
        f"- [[{t}]]: what does it answer?\n"
        for t in (
            "areas/platform/index|Platform",
            "projects/p/index|P",
            "reference/ref",
            "decisions/dec",
            "howto/how",
        )
    )
    write(root, "index.md", index)
    write(
        root,
        "areas/platform/index.md",
        frontmatter("reference", base=True, title="Platform") + "# Platform\n\n"
        "See [[decisions/dec|the decision]] for why the area exists.\n",
    )
    write(
        root,
        "decisions/dec.md",
        frontmatter("decision")
        + body(
            "decision", "Built for [[projects/p/index|P]], which needs this choice."
        ),
    )
    write(
        root,
        "reference/ref.md",
        frontmatter("reference")
        + "# Ref\n\n## Links\n\nThe steps that change it are in [[howto/how]].\n",
    )
    write(
        root,
        "howto/how.md",
        frontmatter("howto")
        + body("howto", "Operates [[reference/ref]], so read it first."),
    )
    write(
        root,
        "projects/p/index.md",
        frontmatter("project")
        + body(
            "project",
            "Built from [[projects/p/designs/ABC-1-thing]], which fixed the approach.",
        ).replace(
            "## Where things are\n\ntext",
            "## Where things are\n\n[[projects/p/designs/ABC-1-thing]] is the design and "
            "[[projects/p/research/q]] is the evidence.",
        ),
    )
    write(
        root,
        "projects/p/designs/ABC-1-thing.md",
        frontmatter("design", project="p")
        + body("design", "Rests on [[decisions/dec]], which fixed the access model."),
    )
    write(
        root,
        "projects/p/research/q.md",
        frontmatter("research", project="p")
        + body("research", "Informed [[decisions/dec]], whose choice rests on it."),
    )
    write(root, "projects/p/index.md", (root / "projects/p/index.md").read_text())


def sub(root: Path, rel: str, old: str, new: str) -> None:
    path = root / rel
    text = path.read_text()
    assert old in text, (rel, old)
    path.write_text(text.replace(old, new, 1))


class LintCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        make_vault(self.root)

    def lint(self, *args: str) -> tuple[int, list[str]]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = notes_lint.main(["--root", str(self.root), *args])
        return code, out.getvalue().splitlines()

    def rules(self, *args: str) -> set[str]:
        return {line.split(": ")[1] for line in self.lint(*args)[1]}


class ReviewNoteTest(LintCase):
    def test_mr_note_under_reviews_is_a_clean_review_note(self) -> None:
        write(
            self.root,
            "projects/p/reviews/review-1.md",
            frontmatter("review", project="p", url="u", state="open")
            + body(
                "review", "Reviewed under [[projects/p/index|P]], whose rules apply."
            ),
        )
        sub(
            self.root,
            "projects/p/index.md",
            "[[projects/p/research/q]] is the evidence.",
            "[[projects/p/research/q]] is the evidence and [[projects/p/reviews/review-1]] is an MR under review.",
        )
        self.assertEqual(self.lint()[1], [])

    def record(self, **over: str) -> None:
        write(
            self.root,
            "projects/p/reviews/review-2.md",
            frontmatter("review", project="p", url="u", state="open", **over)
            + body(
                "review", "Reviewed under [[projects/p/index|P]], whose rules apply."
            ),
        )

    def test_record_without_hub_link_passes(self) -> None:
        self.record()
        self.assertEqual(self.lint(), (0, []))

    def test_record_without_any_link_passes(self) -> None:
        write(
            self.root,
            "projects/p/reviews/review-3.md",
            frontmatter("review", project="p", url="u", state="open")
            + body("review", "Nothing to link yet."),
        )
        self.assertEqual(self.lint(), (0, []))

    def test_record_with_empty_links_passes(self) -> None:
        self.record()
        sub(
            self.root,
            "projects/p/reviews/review-2.md",
            "\ntext\n",
            "\ntext with [[projects/p/index|P]]\n",
        )
        sub(
            self.root,
            "projects/p/reviews/review-2.md",
            "\nReviewed under [[projects/p/index|P]], whose rules apply.\n",
            "",
        )
        self.assertEqual(self.lint(), (0, []))

    def test_record_with_bad_frontmatter_still_fails(self) -> None:
        self.record(status="nope")
        self.assertEqual(self.rules(), {"status-invalid"})

    def test_other_type_in_reviews_is_flagged(self) -> None:
        write(
            self.root,
            "projects/p/reviews/review-1.md",
            frontmatter("research", project="p")
            + body("research", "Informed [[decisions/dec]], whose choice rests on it."),
        )
        self.assertIn("type-folder", self.rules())

    def test_extra_sub_from_env_is_a_review_folder(self) -> None:
        write(
            self.root,
            "projects/p/mrs/review-1.md",
            frontmatter("review", project="p", url="u", state="open")
            + body(
                "review", "Reviewed under [[projects/p/index|P]], whose rules apply."
            ),
        )
        self.assertIn("structure", self.rules())
        with mock.patch.dict("os.environ", {"NOTES_EXTRA_SUBS": "mrs:review"}):
            self.assertEqual(self.lint(), (0, []))


NODES = (
    "| Node | Agent | Owns | Wave | Covers |\n|---|---|---|---|---|\n"
    "| N1 | edit-builder | a.py | 1 | FR-001 |\n| N2 | edit-builder | b.py | 1 | FR-002, FR-001 |\n"
)
TRACE = "| Req | Nodes | Test | Status |\n|---|---|---|---|\n| FR-001 | N1 | t1 | open |\n| FR-002 | N2 | t2 | open |\n"
REQS = "### Functional Requirements\n\n- **FR-001**: System MUST a\n- **FR-002**: System MUST b\n"
V2_REL = "projects/p/designs/ABC-2-v2.md"


SCS = "### Measurable Outcomes\n\n- **SC-001**: p95 under 300 ms\n"
TRACE_SC = TRACE + "| SC-001 | N1 | perf-tester | open |\n"


def v2_note(
    reqs: str = REQS,
    nodes: str = NODES,
    trace: str = TRACE,
    scs: str = "text\n",
    **fm: str,
) -> str:
    text = body(
        "design",
        "Rests on [[decisions/dec]], which fixed the access model.",
        heads=V2_HEADS,
    )
    for head, content in (
        ("Requirements", reqs),
        ("Success Criteria", scs),
        ("Node table", nodes),
        ("Traceability", trace),
    ):
        text = text.replace(f"## {head}\n\ntext\n", f"## {head}\n\n{content}", 1)
    return frontmatter("design", **{"project": "p", "format": "v2", **fm}) + text


def add_v2(root: Path, **kw: str) -> None:
    write(root, V2_REL, v2_note(**kw))
    sub(
        root,
        "projects/p/index.md",
        "[[projects/p/research/q]] is the evidence.",
        "[[projects/p/research/q]] is the evidence and [[projects/p/designs/ABC-2-v2]] the second design.",
    )


class V2Test(LintCase):
    def v2(self, **kw: str) -> set[str]:
        add_v2(self.root, **kw)
        return self.rules()

    def test_complete_v2_note_is_clean(self) -> None:
        add_v2(self.root)
        self.assertEqual(self.lint(), (0, []))

    def test_legacy_note_needs_no_v2_sections(self) -> None:
        self.assertEqual(self.lint(), (0, []))

    def test_v2_note_needs_the_back_half_headings(self) -> None:
        add_v2(self.root)
        sub(self.root, V2_REL, "## Traceability\n\n", "## Trace\n\n")
        self.assertIn("heading-missing", self.rules())

    def test_minimal_v2_note_may_drop_the_front_half(self) -> None:
        add_v2(self.root)
        for head in sorted(notes_lint.V2_OPTIONAL):
            sub(self.root, V2_REL, f"## {head}\n\ntext\n\n", "")
        self.assertEqual(self.lint(), (0, []))

    def test_front_half_still_runs_in_order(self) -> None:
        add_v2(self.root)
        sub(
            self.root,
            V2_REL,
            "## Design\n\ntext\n\n## Alternatives considered\n\ntext\n\n",
            "## Alternatives considered\n\ntext\n\n## Design\n\ntext\n\n",
        )
        self.assertIn("heading-order", self.rules())

    def test_unknown_format_is_flagged(self) -> None:
        self.assertIn("format-invalid", self.v2(format="v3"))

    def test_proposal_format_uses_the_proposal_headings(self) -> None:
        write(
            self.root,
            "projects/p/designs/ABC-3-prop.md",
            frontmatter("design", project="p", format="proposal")
            + body(
                "design",
                "Detailed in [[projects/p/designs/ABC-1-thing]].",
                heads=PROPOSAL_HEADS,
            ),
        )
        sub(
            self.root,
            "projects/p/index.md",
            "[[projects/p/research/q]] is the evidence.",
            "[[projects/p/research/q]] is the evidence and [[projects/p/designs/ABC-3-prop]] the proposal.",
        )
        self.assertEqual(self.lint(), (0, []))

    def test_fr_without_node_is_flagged(self) -> None:
        self.assertEqual(self.v2(nodes=NODES.replace("FR-002, ", "")), {"fr-uncovered"})

    def test_node_covering_unknown_fr_is_flagged(self) -> None:
        self.assertEqual(
            self.v2(nodes=NODES.replace("FR-002, ", "FR-009, ")),
            {"covers-unknown", "fr-uncovered"},
        )

    def test_node_with_empty_covers_is_flagged(self) -> None:
        self.assertEqual(
            self.v2(nodes=NODES + "| N3 | edit-builder | c.py | 2 |  |\n"),
            {"covers-empty"},
        )

    def test_node_table_without_covers_column_is_flagged(self) -> None:
        nodes = "| Node | Agent |\n|---|---|\n| N1 | edit-builder |\n"
        self.assertEqual(self.v2(nodes=nodes), {"covers-column"})

    def test_fr_missing_from_traceability_is_flagged(self) -> None:
        self.assertEqual(
            self.v2(trace=TRACE.replace("| FR-002 | N2 | t2 | open |\n", "")),
            {"trace-missing"},
        )

    def test_sc_missing_from_traceability_is_flagged(self) -> None:
        self.assertEqual(self.v2(scs=SCS), {"trace-missing"})

    def test_sc_row_without_test_is_flagged(self) -> None:
        self.assertEqual(
            self.v2(scs=SCS, trace=TRACE + "| SC-001 | N1 |  | open |\n"),
            {"trace-test-empty"},
        )

    def test_sc_row_with_agent_is_clean(self) -> None:
        self.assertEqual(self.v2(scs=SCS, trace=TRACE_SC), set())

    def test_traceability_without_req_column_is_flagged(self) -> None:
        self.assertEqual(self.v2(trace="| Test |\n|---|\n| t |\n"), {"trace-column"})

    def test_requirements_without_fr_lines_is_flagged(self) -> None:
        self.assertIn(
            "fr-missing",
            self.v2(reqs="none\n", nodes=NODES.replace("FR-001", "FR-009")),
        )


class BaselineTest(LintCase):
    def test_good_vault_is_clean(self) -> None:
        self.assertEqual(self.lint(), (0, []))

    def test_progress_checklist_with_in_progress_marks_is_clean(self) -> None:
        sub(
            self.root,
            "projects/p/designs/ABC-1-thing.md",
            "## Progress\n\ntext\n",
            "## Progress\n- [x] N1 a\n- [~] N2 b\n- [ ] N3 c\n- [ ] review\n- [ ] MR\n- [ ] CI green\n\n",
        )
        self.assertEqual(self.lint(), (0, []))

    def test_design_without_progress_section_is_flagged(self) -> None:
        sub(
            self.root,
            "projects/p/designs/ABC-1-thing.md",
            "## Progress\n\ntext\n\n",
            "",
        )
        self.assertIn("heading-missing", self.rules())

    def test_output_line_format(self) -> None:
        sub(self.root, "reference/ref.md", "status: current", "status: nope")
        code, lines = self.lint()
        self.assertEqual(code, 1)
        self.assertRegex(lines[0], r"^reference/ref\.md:\d+: status-invalid: .+")


def bad_date(root: Path) -> None:
    sub(root, "reference/ref.md", f"updated: {TODAY}", "updated: 2026-13-45")


def old_verified(days: int):
    def mutate(root: Path) -> None:
        sub(
            root,
            "reference/ref.md",
            f"verified: {TODAY}",
            f"verified: {(date.today() - timedelta(days=days)).isoformat()}",
        )

    return mutate


def write_note(rel: str, text: str):
    return lambda root: write(root, rel, text)


def drop_key(rel: str, key: str):
    def mutate(root: Path) -> None:
        path = root / rel
        path.write_text(re.sub(rf"(?m)^{key}:.*\n", "", path.read_text(), count=1))

    return mutate


def replace(rel: str, old: str, new: str):
    return lambda root: sub(root, rel, old, new)


def append(rel: str, text: str):
    def mutate(root: Path) -> None:
        path = root / rel
        path.write_text(path.read_text().rstrip("\n") + "\n" + text)

    return mutate


def superseded(root: Path) -> None:
    sub(
        root,
        "decisions/dec.md",
        "superseded_by: []",
        'superseded_by: ["[[howto/how]]"]',
    )
    sub(root, "decisions/dec.md", "status: current", "status: superseded")


def two_notes_same_name(root: Path) -> None:
    write(root, "howto/dec.md", (root / "howto/how.md").read_text())
    sub(root, "index.md", "- [[howto/how]]", "- [[howto/how]]: how?\n- [[howto/dec]]")
    sub(root, "reference/ref.md", "[[howto/how]]", "[[dec]]")


def reorder_keys(root: Path) -> None:
    sub(
        root,
        "reference/ref.md",
        "status: current\narea: platform\n",
        "area: platform\nstatus: current\n",
    )


def unlinked_note(root: Path) -> None:
    write(root, "reference/lonely.md", (root / "reference/ref.md").read_text())


def linked_from_area(root: Path) -> None:
    unlinked_note(root)
    sub(
        root,
        "areas/platform/index.md",
        "for why the area exists.",
        "for why the area exists, and [[reference/lonely]] says what it holds.",
    )


def stray_in_project(root: Path) -> None:
    write(root, "projects/p/notes.md", (root / "reference/ref.md").read_text())


def hub_forgets_note(root: Path) -> None:
    sub(
        root,
        "projects/p/index.md",
        " and [[projects/p/research/q]] is the evidence.",
        ".",
    )


CASES = [
    # rule, failing mutation, passing near-miss
    (
        "fm-missing",
        write_note(
            "reference/ref.md", "# Ref\n\n## Links\n\n[[howto/how]] says how.\n"
        ),
        None,
    ),
    (
        "fm-syntax",
        replace("reference/ref.md", "---\ntitle", "---\nnot a key\ntitle"),
        None,
    ),
    ("fm-key-missing", drop_key("reference/ref.md", "verified"), None),
    (
        "fm-key-unknown",
        replace("reference/ref.md", "ticket: []", "ticket: []\nowner: x"),
        None,
    ),
    ("key-order", reorder_keys, None),
    (
        "type-invalid",
        replace("reference/ref.md", "type: reference", "type: incident"),
        None,
    ),
    (
        "type-folder",
        replace("reference/ref.md", "type: reference", "type: howto"),
        None,
    ),
    (
        "status-invalid",
        replace("reference/ref.md", "status: current", "status: done"),
        replace("reference/ref.md", "status: current", "status: paused"),
    ),
    (
        "status-invalid",
        replace(
            "projects/p/designs/ABC-1-thing.md", "status: proposed", "status: current"
        ),
        replace(
            "projects/p/designs/ABC-1-thing.md", "status: proposed", "status: shipped"
        ),
    ),
    ("date-format", bad_date, None),
    ("area-unknown", replace("reference/ref.md", "area: platform", "area: mars"), None),
    (
        "project-key",
        replace("projects/p/designs/ABC-1-thing.md", "project: p", "project: other"),
        None,
    ),
    ("project-key", replace("decisions/dec.md", "project:\n", "project: p\n"), None),
    (
        "relation-quote",
        replace("decisions/dec.md", "decided_by: []", "decided_by: [[how]]"),
        replace("decisions/dec.md", "decided_by: []", 'decided_by: ["[[howto/how]]"]'),
    ),
    (
        "relation-form",
        replace("decisions/dec.md", "decided_by: []", "decided_by: howto/how"),
        None,
    ),
    (
        "ticket-form",
        replace("decisions/dec.md", "ticket: []", 'ticket: ["[[howto/how]]"]'),
        replace("decisions/dec.md", "ticket: []", "ticket: [ABC-12]"),
    ),
    (
        "status-superseded",
        replace(
            "decisions/dec.md", "superseded_by: []", 'superseded_by: ["[[howto/how]]"]'
        ),
        superseded,
    ),
    ("heading-missing", replace("decisions/dec.md", "## Why\n", "## Because\n"), None),
    (
        "heading-order",
        replace(
            "decisions/dec.md",
            "## Why\n\ntext\n\n## Alternatives\n",
            "## Alternatives\n\ntext\n\n## Why\n",
        ),
        None,
    ),
    (
        "links-last",
        append("decisions/dec.md", "\n## Open\n\ntext"),
        replace("decisions/dec.md", "## Why", "## Extra\n\ntext\n\n## Why"),
    ),
    (
        "links-empty",
        replace(
            "decisions/dec.md",
            "Built for [[projects/p/index|P]], which needs this choice.",
            "Nothing.",
        ),
        None,
    ),
    (
        "bare-label",
        replace("reference/ref.md", "The steps", "Related: [[howto/how]]\n\nThe steps"),
        replace(
            "reference/ref.md",
            "The steps",
            "Related work is in a sentence, so it is fine. The steps",
        ),
    ),
    (
        "bare-label",
        replace("reference/ref.md", "The steps", "Area: platform\n\nThe steps"),
        None,
    ),
    (
        "bare-link",
        replace("reference/ref.md", "The steps", "- [[howto/how]]\n\nThe steps"),
        None,
    ),
    (
        "no-outbound",
        replace(
            "reference/ref.md",
            "The steps that change it are in [[howto/how]].",
            "No links here.",
        ),
        None,
    ),
    (
        "area-backlink",
        replace(
            "reference/ref.md",
            "The steps",
            "Back to [[areas/platform/index|Platform]]. The steps",
        ),
        None,
    ),
    (
        "design-name",
        lambda r: shutil.move(
            str(r / "projects/p/designs/ABC-1-thing.md"),
            str(r / "projects/p/designs/thing.md"),
        ),
        None,
    ),
    ("h1-missing", replace("reference/ref.md", "# Ref\n", "Intro text.\n"), None),
    (
        "link-broken",
        replace("reference/ref.md", "[[howto/how]]", "[[howto/nope]]"),
        replace("reference/ref.md", "[[howto/how]]", "[[howto/how.md]]"),
    ),
    ("link-ambiguous", two_notes_same_name, None),
    (
        "link-heading",
        replace("reference/ref.md", "[[howto/how]]", "[[howto/how#Missing section]]"),
        replace(
            "reference/ref.md", "[[howto/how]]", "[[howto/how#check it worked|check]]"
        ),
    ),
    ("orphan", unlinked_note, linked_from_area),
    ("project-hub", hub_forgets_note, None),
    ("structure", stray_in_project, None),
    ("structure", write_note("loose.md", "x\n"), None),
    (
        "whitespace",
        replace("reference/ref.md", "[[howto/how]].", "[[howto/how]]. \t"),
        replace("reference/ref.md", "The steps", "Break line  \nThe steps"),
    ),
    (
        "whitespace",
        lambda r: (r / "reference/ref.md").write_text(
            (r / "reference/ref.md").read_text() + "\n"
        ),
        None,
    ),
    ("fm-empty", replace("reference/ref.md", "title: T", "title:"), None),
    (
        "fm-value",
        replace("reference/ref.md", "sources: []", 'sources: ["[[howto/how]]"]'),
        None,
    ),
    ("stale-verified", old_verified(61), old_verified(60)),
    ("format-invalid", lambda r: add_v2(r, format="v3"), lambda r: add_v2(r)),
    ("fr-missing", lambda r: add_v2(r, reqs="none\n"), lambda r: add_v2(r)),
    (
        "fr-uncovered",
        lambda r: add_v2(r, nodes=NODES.replace("FR-002, ", "")),
        lambda r: add_v2(r),
    ),
    (
        "covers-column",
        lambda r: add_v2(r, nodes="| Node |\n|---|\n| N1 |\n"),
        lambda r: add_v2(r),
    ),
    (
        "covers-empty",
        lambda r: add_v2(r, nodes=NODES + "| N3 | x | c | 2 |  |\n"),
        lambda r: add_v2(r),
    ),
    (
        "covers-unknown",
        lambda r: add_v2(r, nodes=NODES.replace("FR-002, ", "FR-009, ")),
        lambda r: add_v2(r),
    ),
    (
        "trace-column",
        lambda r: add_v2(r, trace="| Test |\n|---|\n| t |\n"),
        lambda r: add_v2(r),
    ),
    (
        "trace-missing",
        lambda r: add_v2(r, trace=TRACE.replace("| FR-002 | N2 | t2 | open |\n", "")),
        lambda r: add_v2(r),
    ),
    (
        "trace-test-empty",
        lambda r: add_v2(r, scs=SCS, trace=TRACE + "| SC-001 | N1 |  | open |\n"),
        lambda r: add_v2(r, scs=SCS, trace=TRACE_SC),
    ),
]


class RuleTest(LintCase):
    def test_each_rule_fails_on_its_fixture_and_passes_on_the_near_miss(self) -> None:
        for n, (rule, bad, ok) in enumerate(CASES):
            with self.subTest(rule=rule, case=n):
                self.setUp()
                bad(self.root)
                self.assertIn(rule, self.rules(), f"{rule} not reported")
                if ok:
                    self.setUp()
                    ok(self.root)
                    self.assertNotIn(
                        rule, self.rules(), f"{rule} reported on the passing fixture"
                    )

    def test_every_rule_in_the_linter_has_a_failing_fixture(self) -> None:
        self.assertEqual(notes_lint.RULES - {rule for rule, _, _ in CASES}, set())

    def test_stale_verified_is_a_warning_not_an_error(self) -> None:
        old_verified(90)(self.root)
        code, lines = self.lint()
        self.assertEqual(code, 0)
        self.assertIn("(warning)", lines[0])


class CliTest(LintCase):
    def test_paths_limit_the_report_but_not_the_link_graph(self) -> None:
        sub(self.root, "reference/ref.md", "status: current", "status: nope")
        sub(self.root, "howto/how.md", "status: current", "status: nope")
        lines = self.lint(str(self.root / "howto/how.md"))[1]
        self.assertTrue(
            lines and all(line.startswith("howto/how.md:") for line in lines)
        )

    def test_links_flag_ignores_format_rules(self) -> None:
        sub(self.root, "reference/ref.md", "status: current", "status: nope")
        self.assertEqual(self.lint("--links"), (0, []))
        sub(self.root, "reference/ref.md", "[[howto/how]]", "[[howto/nope]]")
        self.assertEqual(self.rules("--links"), {"link-broken"})

    def test_fix_reorders_keys_and_trims_whitespace_only(self) -> None:
        reorder_keys(self.root)
        sub(self.root, "reference/ref.md", "The steps", "The steps  \t")
        path = self.root / "reference/ref.md"
        words_before = sorted(re.findall(r"\w+", path.read_text()))
        self.assertEqual(self.lint("--fix"), (0, []))
        self.assertEqual(sorted(re.findall(r"\w+", path.read_text())), words_before)
        self.assertIn(
            "type: reference\nstatus: current\narea: platform", path.read_text()
        )

    def test_fix_never_adds_content(self) -> None:
        drop_key("reference/ref.md", "verified")(self.root)
        before = (self.root / "reference/ref.md").read_text()
        code, _ = self.lint("--fix")
        self.assertEqual(code, 1)
        self.assertEqual((self.root / "reference/ref.md").read_text(), before)

    def test_templates_drive_the_format(self) -> None:
        sub(self.root, "templates/reference.md", "## Links", "## Links\n## Extra")
        self.assertIn("heading-missing", self.rules())

    def test_missing_templates_is_a_usage_error(self) -> None:
        shutil.rmtree(self.root / "templates")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(notes_lint.main(["--root", str(self.root)]), 2)

    def test_excluded_folders_are_not_linted(self) -> None:
        write(self.root, "adr/ADR-1-x.md", "no frontmatter at all\n")
        write(self.root, "README.md", "plain\n")
        write(self.root, ".obsidian/x.md", "plain\n")
        self.assertEqual(self.lint(), (0, []))

    def test_script_runs_as_a_command(self) -> None:
        result = subprocess.run(
            [sys.executable, str(LINT), "--root", str(self.root)],
            capture_output=True,
            text=True,
        )
        self.assertEqual((result.returncode, result.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
