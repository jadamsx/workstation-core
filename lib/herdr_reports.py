"""Paths and herdr calls shared by herdr-manager, herdr-report-watch and the manager-* commands."""
import json
import os
import re
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

NAME = re.compile(r"[a-z][a-z0-9_-]{0,31}")
LEAD_TAB = "◆ lead"
MANAGER_TAB = "▸ "
ASK_TAB = "? ask"
TRUST_DIALOG = "Is this a project you created or one you trust?"
INPUT_BOX = re.compile(r"\? for shortcuts|^[│ ]*> ", re.M)


class ReportsError(Exception):
    pass


def reports_root() -> Path:
    return Path(os.environ.get("WORKSTATION_REPORTS_ROOT") or Path.home() / ".local/state/workstation/reports")


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "space"


def herdr(*args: str) -> dict:
    out = subprocess.run(["herdr", *args], check=True, capture_output=True, text=True).stdout
    return json.loads(out)["result"] if out.strip() else {}


def pane_text(pane: str) -> str:
    return subprocess.run(["herdr", "pane", "read", pane, "--source", "visible"], check=True, capture_output=True, text=True).stdout


def wait_for_pane(pane: str, accept: Callable[[str], object], timeout: float, interval: float = 0.2) -> str | None:
    """The first pane text `accept` approves, or None after `timeout` seconds."""
    deadline = time.monotonic() + timeout
    while True:
        text = pane_text(pane)
        if accept(text):
            return text
        if time.monotonic() >= deadline:
            return None
        time.sleep(interval)


def shell_only(pane: str) -> bool:
    """True when the pane's foreground processes are just the user's shell, so `herdr agent start` will not find it busy."""
    info = herdr("pane", "process-info", "--pane", pane).get("process_info", {})
    procs = info.get("foreground_processes", [])
    shell = Path(os.environ.get("SHELL", "")).name
    return len(procs) == 1 and (not shell or procs[0].get("argv0", "").lstrip("-") == shell)


def wait_for_shell(pane: str, timeout: float, interval: float = 0.2) -> bool:
    deadline = time.monotonic() + timeout
    while True:
        if shell_only(pane):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(interval)


def space_dir() -> Path:
    wid = os.environ.get("HERDR_WORKSPACE_ID")
    if not wid:
        raise ReportsError("not inside herdr: HERDR_WORKSPACE_ID is unset")
    return reports_root() / slug(herdr("workspace", "get", wid)["workspace"]["label"])


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def pane_states() -> dict[str, str] | None:
    """Agent status by pane id as herdr reports it now, or None when herdr cannot be asked."""
    try:
        return {p["pane_id"]: p.get("agent_status", "unknown") for p in herdr("pane", "list").get("panes", [])}
    except (subprocess.CalledProcessError, OSError, ValueError, KeyError):
        return None


def live_panes() -> set[str] | None:
    """Pane ids herdr reports now, or None when herdr cannot be asked."""
    states = pane_states()
    return None if states is None else set(states)


def manager_folder(name: str) -> Path:
    folder = space_dir() / name
    if not (folder / "manager.json").exists():
        raise ReportsError(f"no manager named {name!r} in this space")
    return folder


def close_manager(folder: Path) -> None:
    """Close the manager's tab and mark it closed so the watcher and repair leave it alone."""
    info = json.loads((folder / "manager.json").read_text())
    if info.get("closed"):
        return
    try:
        herdr("tab", "close", info["tab_id"])
    except subprocess.CalledProcessError:
        if info["pane_id"] in (live_panes() or set()):
            raise
    write_atomic(folder / "manager.json", json.dumps({**info, "closed": True}))


def read_manager(folder: Path) -> dict:
    return json.loads((folder / "manager.json").read_text())
