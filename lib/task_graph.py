#!/usr/bin/env python3
"""Cumulative node index behind bin/node-index.

Counts how often a node signature (kind + normalised title + actor) recurs
across tasks, so "this step is repeatable, extract it" is measured rather
than recalled. Stdlib only.

Usage:
  task_graph.py record --task <slug> [--repo <name>] [--date YYYY-MM-DD] < nodes.json
  task_graph.py report [--min 3] [--json] [--all]
  task_graph.py mark <signature> --status extracted|open|wontfix [--note "..."]
  task_graph.py kinds

nodes.json is a JSON array of objects with at least: kind, title, actor.
Extra keys are ignored. Re-recording the same task slug replaces that task's
contribution (idempotent re-runs).

Index location: $AGENT_NODE_INDEX, else ~/.agent/process/node-index.json
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path

KINDS = (
    "recon",
    "spec-read",
    "design",
    "interface-change",
    "implement",
    "migrate-callsites",
    "config-wire",
    "data-migration",
    "test-write",
    "verify-run",
    "verify-manual",
    "docs",
    "review",
    "release",
    "decision",
    "spike",
)

STOPWORDS = frozenset(
    "a an the and or of to for in on at by with from into via this that its it "
    "is are be add adds new all any then than so we our".split()
)

_DOUBLE_KEEP = frozenset("lsz")


def index_path() -> Path:
    env = os.environ.get("AGENT_NODE_INDEX")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".agent" / "process" / "node-index.json"


def load(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "signatures": {}}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"corrupt index at {path}: {exc}")
    data.setdefault("version", 1)
    data.setdefault("signatures", {})
    return data


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def _fold(token: str) -> str:
    """Porter-lite stem: collapse plural/gerund/past wording drift to one key.

    map/mapping -> map, callsite/callsites -> callsit,
    migrate/migrating/migrated -> migrat, verify/verifies -> verifi.
    """
    if token.isdigit() or len(token) < 4:
        return token
    # plurals
    if token.endswith(("ses", "xes", "zes", "ches", "shes")):
        token = token[:-2]
    elif token.endswith("ies") and len(token) > 4:
        token = token[:-3] + "i"
    elif token.endswith("s") and not token.endswith(("ss", "us", "is")):
        token = token[:-1]
    # gerund / past
    for suffix in ("ing", "ed"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            token = token[: -len(suffix)]
            break
    # undouble a doubled final consonant left by the strip (mapp -> map)
    if (
        len(token) > 3
        and token[-1] == token[-2]
        and token[-1].isalpha()
        and token[-1] not in "aeiou"
        and token[-1] not in _DOUBLE_KEEP
    ):
        token = token[:-1]
    # silent trailing e, so callsite and callsit-(es) meet
    if len(token) > 3 and token.endswith("e"):
        token = token[:-1]
    # terminal y behaves as i (verify / verifies)
    if len(token) > 2 and token.endswith("y") and token[-2] not in "aeiou":
        token = token[:-1] + "i"
    return token


def normalise(title: str) -> str:
    words = re.findall(r"[a-z0-9]+", title.lower())
    kept = sorted({_fold(w) for w in words if w not in STOPWORDS})
    return " ".join(kept)


def signature(kind: str, title: str, actor: str) -> str:
    return f"{kind}|{actor}|{normalise(title)}"


def cmd_record(args: argparse.Namespace) -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        raise SystemExit("record: expected a JSON array of nodes on stdin")
    try:
        nodes = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"record: invalid JSON on stdin: {exc}")
    if not isinstance(nodes, list):
        raise SystemExit("record: stdin must be a JSON array")

    bad = sorted(
        {n.get("kind", "<missing>") for n in nodes if n.get("kind") not in KINDS}
    )
    if bad:
        raise SystemExit(
            "record: unknown kind(s): "
            + ", ".join(bad)
            + "\nallowed: "
            + ", ".join(KINDS)
        )

    path = index_path()
    data = load(path)
    sigs = data["signatures"]
    task = args.task
    date = args.date or _dt.date.today().isoformat()
    # Accept a path or a bare name; store the bare name so counts group per repo.
    repo = Path(args.repo).name if args.repo else Path.cwd().name

    # Idempotent: drop any prior contribution from this task slug.
    for entry in list(sigs.values()):
        entry["occurrences"] = [o for o in entry["occurrences"] if o["task"] != task]
    for key in [k for k, v in sigs.items() if not v["occurrences"]]:
        del sigs[key]

    for node in nodes:
        kind = node["kind"]
        title = str(node.get("title", "")).strip()
        actor = str(node.get("actor", "main")).strip() or "main"
        if not title:
            raise SystemExit("record: every node needs a non-empty title")
        key = signature(kind, title, actor)
        entry = sigs.setdefault(
            key,
            {
                "kind": kind,
                "actor": actor,
                "titles": [],
                "occurrences": [],
                "status": "open",
                "note": "",
            },
        )
        if title not in entry["titles"]:
            entry["titles"].append(title)
        entry["occurrences"].append({"task": task, "repo": repo, "date": date})

    save(path, data)
    hot = sum(
        1
        for e in sigs.values()
        if len(e["occurrences"]) >= args.min and e["status"] == "open"
    )
    print(f"recorded {len(nodes)} node(s) for {task} -> {path}")
    print(f"{len(sigs)} signature(s) tracked; {hot} at/over threshold {args.min}")
    return 0


def _rows(data: dict, min_count: int, show_all: bool) -> list[dict]:
    rows = []
    for key, entry in data["signatures"].items():
        count = len(entry["occurrences"])
        if not show_all and (count < min_count or entry["status"] != "open"):
            continue
        rows.append(
            {
                "signature": key,
                "kind": entry["kind"],
                "actor": entry["actor"],
                "count": count,
                "status": entry["status"],
                "titles": entry["titles"],
                "repos": sorted({o["repo"] for o in entry["occurrences"]}),
                "tasks": [o["task"] for o in entry["occurrences"]],
                "last_seen": max(o["date"] for o in entry["occurrences"]),
                "note": entry.get("note", ""),
            }
        )
    rows.sort(key=lambda r: (-r["count"], r["kind"], r["signature"]))
    return rows


def cmd_report(args: argparse.Namespace) -> int:
    data = load(index_path())
    rows = _rows(data, args.min, args.all)
    if args.json:
        print(json.dumps(rows, indent=2))
        return 0
    if not rows:
        print(f"no signatures at/over threshold {args.min} (index: {index_path()})")
        return 0
    print(f"extraction candidates (count >= {args.min}) — index: {index_path()}\n")
    for row in rows:
        print(
            f"[{row['count']}x] {row['kind']} / {row['actor']}  status={row['status']}"
        )
        print(f"      titles: {'; '.join(row['titles'])}")
        print(f"      repos:  {', '.join(row['repos'])}   last: {row['last_seen']}")
        print(f"      tasks:  {', '.join(row['tasks'])}")
        if row["note"]:
            print(f"      note:   {row['note']}")
        print(f"      sig:    {row['signature']}")
        print()
    return 0


def cmd_mark(args: argparse.Namespace) -> int:
    path = index_path()
    data = load(path)
    entry = data["signatures"].get(args.signature)
    if entry is None:
        raise SystemExit(f"mark: unknown signature {args.signature!r}")
    entry["status"] = args.status
    if args.note:
        entry["note"] = args.note
    save(path, data)
    print(f"{args.signature} -> {args.status}")
    return 0


def cmd_kinds(_: argparse.Namespace) -> int:
    print("\n".join(KINDS))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="task_graph.py", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    rec = sub.add_parser("record", help="record a task's nodes (JSON array on stdin)")
    rec.add_argument(
        "--task", required=True, help="task slug, e.g. YYYY-MM-DD-add-health-probe"
    )
    rec.add_argument("--repo", help="repo name (default: cwd name)")
    rec.add_argument("--date", help="YYYY-MM-DD (default: today)")
    rec.add_argument(
        "--min", type=int, default=3, help="candidate threshold for the summary line"
    )
    rec.set_defaults(func=cmd_record)

    rep = sub.add_parser("report", help="list extraction candidates")
    rep.add_argument("--min", type=int, default=3)
    rep.add_argument("--json", action="store_true")
    rep.add_argument(
        "--all", action="store_true", help="include below-threshold and non-open rows"
    )
    rep.set_defaults(func=cmd_report)

    mark = sub.add_parser("mark", help="set a signature's status")
    mark.add_argument("signature")
    mark.add_argument(
        "--status", required=True, choices=("extracted", "open", "wontfix")
    )
    mark.add_argument("--note")
    mark.set_defaults(func=cmd_mark)

    kinds = sub.add_parser("kinds", help="print the allowed node kinds")
    kinds.set_defaults(func=cmd_kinds)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
