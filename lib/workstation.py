#!/usr/bin/env python3
"""Install, inspect and remove the core workstation setup on this machine.

Every mode works from one plan: links into ``~/.claude``, the merged ``settings.json``, the MCP
servers in ``claude/mcp.json``, the plugins in ``claude/plugins.json`` and the few helper commands
the skills call (linked into ``~/.local/bin``), each knowing how to check itself against the live
machine. ``WORKSTATION_HOME`` and ``WORKSTATION_HOST`` override the home directory and hostname so the plan can be exercised against a scratch home;
``WORKSTATION_MACHINES`` names a directory of ``<host>/settings.overlay.json`` files merged on top.
"""

from __future__ import annotations

import argparse
import json
import os
import pwd
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REAL_HOME = Path(pwd.getpwuid(os.getuid()).pw_dir)
HOME = Path(os.environ.get("WORKSTATION_HOME") or Path.home())
LIVE = HOME == REAL_HOME
CLAUDE = HOME / ".claude"
BACKUPS = HOME / "workstation-backups"
MERGE = ROOT / "lib" / "merge-settings.py"
BINS = ("shot", "browser-login", "notes-lint", "current-project", "node-index")
OK, MISSING, DIFFERS, DISPLACES, SKIPPED = (
    "ok",
    "missing",
    "differs",
    "displaces",
    "skipped",
)


def hostname() -> str:
    return (
        os.environ.get("WORKSTATION_HOST")
        or subprocess.run(
            ["hostname", "-s"], capture_output=True, text=True, check=True
        ).stdout.strip()
    )


def is_junk(path: Path) -> bool:
    return (
        "__pycache__" in path.parts
        or path.name == ".DS_Store"
        or re.search(r"\.(pyc|bak(-.*)?)$", path.name) is not None
    )


def same(a: Path, b: Path) -> bool:
    if a.is_dir() != b.is_dir():
        return False
    if not a.is_dir():
        return a.read_bytes() == b.read_bytes()
    names_a = {p.relative_to(a) for p in a.rglob("*") if p.is_file() and not is_junk(p)}
    names_b = {p.relative_to(b) for p in b.rglob("*") if p.is_file() and not is_junk(p)}
    return names_a == names_b and all(
        (a / n).read_bytes() == (b / n).read_bytes() for n in names_a
    )


class Backup:
    """Moves (or copies, with ``keep``) displaced files under ~/workstation-backups/<timestamp>/ and records where each came from."""

    def __init__(self) -> None:
        self.dir = BACKUPS / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        self.entries: list[dict[str, str]] = []

    def stash(self, path: Path, keep: bool = False) -> None:
        rel = path.relative_to(HOME)
        target = self.dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if keep:
            shutil.copy2(path, target)
        else:
            shutil.move(str(path), str(target))
        self.entries.append({"dest": str(path), "backup": str(rel)})

    def save(self) -> None:
        if self.entries:
            (self.dir / "manifest.json").write_text(
                json.dumps(self.entries, indent=2) + "\n"
            )


class Item:
    kind = "item"
    verb = "apply"

    def __init__(self, dest: Path) -> None:
        self.dest = dest

    def describe(self) -> str:
        return str(self.dest)

    def state(self) -> str:
        raise NotImplementedError

    def detail(self) -> str:
        return ""

    def apply(self, backup: Backup) -> None:
        raise NotImplementedError

    def uninstall(self, restorable: set[str]) -> None:
        return None


class Link(Item):
    kind, verb = "link", "link"

    def __init__(self, dest: Path, src: Path) -> None:
        super().__init__(dest)
        self.src = src

    def describe(self) -> str:
        return f"{self.dest} -> {self.src}"

    def state(self) -> str:
        if self.dest.is_symlink() and Path(os.readlink(self.dest)) == self.src:
            return OK
        return DISPLACES if os.path.lexists(self.dest) else MISSING

    def detail(self) -> str:
        if self.state() != DISPLACES:
            return ""
        if self.dest.is_symlink():
            return f"real symlink to {os.readlink(self.dest)}"
        return (
            "identical copy"
            if same(self.dest, self.src)
            else "content differs from repo"
        )

    def apply(self, backup: Backup) -> None:
        if os.path.lexists(self.dest):
            backup.stash(self.dest)
        self.dest.parent.mkdir(parents=True, exist_ok=True)
        self.dest.symlink_to(self.src)

    def uninstall(self, restorable: set[str]) -> None:
        if self.dest.is_symlink() and ROOT in Path(os.readlink(self.dest)).parents:
            self.dest.unlink()


class Settings(Item):
    kind, verb = "merge", "merge"

    def __init__(self, dest: Path, base: Path, overlay: Path) -> None:
        super().__init__(dest)
        self.base = base
        self.overlay = overlay

    def describe(self) -> str:
        overlay = f" + {self.overlay}" if self.overlay.exists() else ""
        return f"{self.base.relative_to(ROOT)}{overlay} into {self.dest}"

    def run(self, mode: str) -> str:
        cmd = [
            sys.executable,
            str(MERGE),
            mode,
            "--base",
            str(self.base),
            "--live",
            str(self.dest),
            "--home",
            str(HOME),
        ]
        if self.overlay.exists():
            cmd += ["--overlay", str(self.overlay)]
        return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout

    def merged(self) -> dict:
        return json.loads(self.run("merge"))

    def live(self) -> dict:
        return json.loads(self.dest.read_text())

    def state(self) -> str:
        if not self.dest.exists():
            return MISSING
        return OK if self.merged() == self.live() else DIFFERS

    def detail(self) -> str:
        if self.state() != DIFFERS:
            return ""
        merged, live = self.merged(), self.live()
        return "keys that would change: " + ", ".join(
            sorted(k for k in {*merged, *live} if merged.get(k) != live.get(k))
        )

    def apply(self, backup: Backup) -> None:
        text = self.run("merge")
        if self.dest.exists():
            backup.stash(self.dest, keep=True)
        self.dest.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.dest.parent, prefix=f".{self.dest.name}.")
        try:
            with os.fdopen(fd, "w") as handle:
                handle.write(text)
            os.replace(tmp, self.dest)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise

    def uninstall(self, restorable: set[str]) -> None:
        if self.state() == OK and str(self.dest) in restorable:
            self.dest.unlink()


class McpServers(Item):
    """Applies the servers in claude/mcp.json to ~/.claude.json, skipping any that need a secret from env."""

    kind, verb = "merge", "merge"

    def __init__(self, dest: Path, src: Path) -> None:
        super().__init__(dest)
        self.src = src

    def describe(self) -> str:
        return f"{self.src.relative_to(ROOT)} servers into {self.dest}"

    def wanted(self) -> dict:
        servers = json.loads(self.src.read_text())["mcpServers"]
        text = json.dumps(
            {
                n: c
                for n, c in servers.items()
                if not any("${" in v for v in c.get("env", {}).values())
            }
        )
        return json.loads(text.replace("${HOME}", str(HOME)))

    def live(self) -> dict:
        return json.loads(self.dest.read_text()) if self.dest.exists() else {}

    def state(self) -> str:
        if not self.dest.exists():
            return MISSING
        current = self.live().get("mcpServers", {})
        return (
            OK
            if all(current.get(n) == c for n, c in self.wanted().items())
            else DIFFERS
        )

    def detail(self) -> str:
        current = self.live().get("mcpServers", {})
        changing = [n for n, c in self.wanted().items() if current.get(n) != c]
        return "servers that would change: " + ", ".join(changing)

    def apply(self, backup: Backup) -> None:
        data = self.live()
        servers = data.setdefault("mcpServers", {})
        servers.update(self.wanted())
        if self.dest.exists():
            backup.stash(self.dest, keep=True)
        fd, tmp = tempfile.mkstemp(dir=self.dest.parent, prefix=f".{self.dest.name}.")
        try:
            with os.fdopen(fd, "w") as handle:
                json.dump(data, handle, indent=2)
            os.chmod(tmp, 0o600)
            os.replace(tmp, self.dest)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise


class PluginCommand(Item):
    kind, verb = "run", "run"

    def __init__(self, label: str, cmd: list[str], present: bool) -> None:
        super().__init__(Path(label))
        self.cmd = cmd
        self.present = present

    def describe(self) -> str:
        return " ".join(self.cmd)

    def state(self) -> str:
        if not LIVE:
            return SKIPPED
        return OK if self.present else MISSING

    def apply(self, backup: Backup) -> None:
        subprocess.run(self.cmd, check=True)


def claude_links() -> list[Item]:
    items: list[Item] = []
    for kind in ("skills", "agents", "hooks"):
        for src in sorted((ROOT / "claude" / kind).glob("*")):
            if not src.name.startswith(".") and not is_junk(src):
                items.append(Link(CLAUDE / kind / src.name, src))
    for src in sorted((ROOT / "claude").glob("*.md")):
        items.append(Link(CLAUDE / src.name, src))
    for name in (
        "statusline-command.sh",
        "reference",
        "checklists",
        "disciplines",
        "templates",
        "engines",
        "themes",
        "context",
    ):
        if (ROOT / "claude" / name).exists():
            items.append(Link(CLAUDE / name, ROOT / "claude" / name))
    return items


def plugin_items() -> list[Item]:
    if not (ROOT / "claude/plugins.json").exists():
        return []
    spec = json.loads((ROOT / "claude/plugins.json").read_text())
    plugin_dir = CLAUDE / "plugins"
    known = (
        json.loads((plugin_dir / "known_marketplaces.json").read_text())
        if (plugin_dir / "known_marketplaces.json").exists()
        else {}
    )
    installed_file = plugin_dir / "installed_plugins.json"
    installed = (
        json.loads(installed_file.read_text()).get("plugins", {})
        if installed_file.exists()
        else {}
    )
    items: list[Item] = []
    for market in spec["marketplaces"]:
        source = market["source"]
        target = source.get("repo") or source["url"]
        items.append(
            PluginCommand(
                market["name"],
                ["claude", "plugin", "marketplace", "add", target],
                market["name"] in known,
            )
        )
    for plugin in spec["plugins"]:
        items.append(
            PluginCommand(
                plugin, ["claude", "plugin", "install", plugin], plugin in installed
            )
        )
    return items


def bin_links() -> list[Item]:
    return [
        Link(HOME / ".local/bin" / name, ROOT / "bin" / name)
        for name in BINS
        if (ROOT / "bin" / name).exists()
    ]


def plan() -> list[Item]:
    """Every item to install or check."""
    machines = Path(os.environ.get("WORKSTATION_MACHINES") or ROOT / "machines")
    settings = Settings(
        CLAUDE / "settings.json",
        ROOT / "claude/settings.base.json",
        machines / hostname() / "settings.overlay.json",
    )
    mcp = (
        [McpServers(HOME / ".claude.json", ROOT / "claude/mcp.json")]
        if (ROOT / "claude/mcp.json").exists()
        else []
    )
    return [
        *claude_links(),
        *([settings] if settings.base.exists() else []),
        *mcp,
        *bin_links(),
        *plugin_items(),
    ]


def line(prefix: str, item: Item, state: str) -> str:
    extra = item.detail()
    return f"{prefix:<20}{item.describe()}  [{state}{': ' + extra if extra else ''}]"


def summarize(items: list[Item]) -> str:
    parts = []
    for kind in dict.fromkeys(i.kind for i in items):
        group = [i for i in items if i.kind == kind]
        todo = [i for i in group if i.state() not in (OK, SKIPPED)]
        displaced = sum(1 for i in todo if i.state() == DISPLACES)
        parts.append(
            f"{kind} {len(group)} ({len(group) - len(todo)} ok, {len(todo)} to do, {displaced} displace a real file)"
        )
    return "; ".join(parts)


def cmd_install(dry_run: bool) -> int:
    items = plan()
    backup = Backup()
    try:
        for item in items:
            state = item.state()
            if state in (OK, SKIPPED):
                if dry_run:
                    print(line(state, item, state))
                continue
            print(line(f"would {item.verb}" if dry_run else item.verb, item, state))
            if dry_run:
                continue
            if item.kind != "run" and HOME not in item.dest.parents:
                raise SystemExit(f"refusing to touch {item.dest}: outside {HOME}")
            item.apply(backup)
    finally:
        backup.save()
    print(summarize(items))
    if dry_run:
        print("dry run, nothing changed")
    elif backup.entries:
        print(f"displaced files saved under {backup.dir}")
    return 0


def cmd_status() -> int:
    items = plan()
    off = 0
    for item in items:
        state = item.state()
        if state not in (OK, SKIPPED):
            off += 1
            print(line(state, item, state))
    git = subprocess.run(
        ["git", "-C", str(ROOT), "status", "--porcelain"],
        capture_output=True,
        text=True,
    ).stdout.split("\n")
    pending = len([g for g in git if g])
    print(
        f"{len(items) - off} of {len(items)} in place, {off} need attention, {pending} uncommitted repo files"
    )
    return 1 if off else 0


def backup_manifests() -> list[Path]:
    return sorted(BACKUPS.glob("*/manifest.json")) if BACKUPS.exists() else []


def restore_plan() -> list[tuple[Path, Path, str]]:
    """(dest, stash, backup name) per dest; the oldest backup holds the file as it was before any install."""
    chosen: dict[str, tuple[Path, Path, str]] = {}
    for manifest in backup_manifests():
        for entry in json.loads(manifest.read_text()):
            chosen.setdefault(
                entry["dest"],
                (
                    Path(entry["dest"]),
                    manifest.parent / entry["backup"],
                    manifest.parent.name,
                ),
            )
    return list(chosen.values())


def cmd_uninstall(dry_run: bool) -> int:
    entries = restore_plan()
    restorable = {str(dest) for dest, _, _ in entries}
    for item in plan():
        if item.state() == OK and (item.kind == "link" or str(item.dest) in restorable):
            print(f"{'would remove' if dry_run else 'remove':<20}{item.dest}")
            if not dry_run:
                item.uninstall(restorable)
    for dest, stash, name in entries:
        if os.path.lexists(dest):
            print(f"{'left':<20}{dest}  [exists, not overwritten]")
            continue
        print(f"{'would restore' if dry_run else 'restore':<20}{dest}  [from {name}]")
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(stash), str(dest))
    if not entries:
        print("no backup with a manifest found, nothing to restore")
    if dry_run:
        print("dry run, nothing changed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="install.sh", description=__doc__)
    parser.add_argument(
        "command", nargs="?", choices=["install", "status", "uninstall"]
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print every action without changing anything",
    )
    args = parser.parse_args()
    dry_run = args.dry_run or args.command is None
    command = args.command or "install"
    if command == "status":
        return cmd_status()
    if command == "install":
        return cmd_install(dry_run)
    return cmd_uninstall(dry_run)


if __name__ == "__main__":
    sys.exit(main())
