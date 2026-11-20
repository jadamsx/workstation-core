"""Paths and herdr calls shared by herdr-manager and shell-reap."""
import json
import os
import re
import signal
import subprocess
import time
from pathlib import Path
from typing import Callable, NamedTuple

LEAD_TAB = "◆ lead"
WORK_TAB = "▸ work"
TRUST_DIALOG = "Is this a project you created or one you trust?"
NO_STDIN_ENV = ("GIT_TERMINAL_PROMPT=0", "PAGER=cat", "GIT_PAGER=cat", "GIT_EDITOR=true")
INPUT_BOX = re.compile(r"\? for shortcuts|^[│ ]*[>❯]\s", re.M)


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


class Proc(NamedTuple):
    pid: int
    ppid: int
    age: float
    cpu: float
    command: str


def clock_seconds(text: str) -> float:
    """Seconds in a ps `[[dd-]hh:]mm:ss[.ff]` field."""
    days, _, clock = text.rpartition("-")
    total = 0.0
    for part in clock.split(":"):
        total = total * 60 + float(part)
    return total + (int(days) * 86400 if days else 0)


def read_procs() -> list[Proc]:
    out = subprocess.run(["ps", "-axo", "pid,ppid,etime,time,command"], check=True, capture_output=True, text=True).stdout
    rows = (line.split(None, 4) for line in out.splitlines()[1:])
    return [Proc(int(r[0]), int(r[1]), clock_seconds(r[2]), clock_seconds(r[3]), r[4]) for r in rows if len(r) == 5]


def argv0(proc: Proc) -> str:
    return Path(proc.command.split(None, 1)[0]).name.lstrip("-")


SHELLS = {"bash", "zsh", "sh"}
BASH_TOOL_SHELL = re.compile(r"^\S*(?:bash|zsh|sh) -c (?:-l )?source \S*shell-snapshots/")
KILL_GRACE_SECONDS = 5


def stop_shell(pid: int, procs: Callable[[], list[Proc]] = read_procs, kill: Callable[[int, int], None] = os.kill,
               caller: int | None = None, wait: bool = False) -> None:
    """SIGTERM a shell that has a claude process above it; with `wait`, SIGKILL it if it outlives the grace period.

    Refuses anything else, and the caller's own process chain, with ReportsError.
    """
    by_pid = {p.pid: p for p in procs()}

    def chain(start: int) -> list[Proc]:
        found: list[Proc] = []
        while start in by_pid and by_pid[start] not in found:
            found.append(by_pid[start])
            start = by_pid[start].ppid
        return found

    target = by_pid.get(pid)
    if pid <= 1 or target is None:
        raise ReportsError(f"{pid} is not a running process")
    if argv0(target) not in SHELLS:
        raise ReportsError(f"{pid} is not a shell")
    above = chain(target.ppid)
    if not any(argv0(p) == "claude" for p in above):
        raise ReportsError(f"{pid} has no claude process above it")
    if pid in {p.pid for p in chain(os.getpid() if caller is None else caller)}:
        raise ReportsError(f"{pid} is the caller's own shell")
    kids: dict[int, list[int]] = {}
    for p in by_pid.values():
        kids.setdefault(p.ppid, []).append(p.pid)
    order, queue = [], [pid]
    while queue:
        order.append(queue.pop(0))
        queue += kids.get(order[-1], [])
    for victim in reversed(order):
        kill(victim, signal.SIGTERM)
    if not wait:
        return
    deadline = time.monotonic() + KILL_GRACE_SECONDS
    while time.monotonic() < deadline:
        try:
            kill(pid, 0)
        except OSError:
            return
        time.sleep(0.1)
    if same_process(target, procs):
        kill(pid, signal.SIGKILL)


def same_process(was: Proc, procs: Callable[[], list[Proc]]) -> bool:
    """True when the pid still runs the same command and is no younger, so a reused pid is not mistaken for it."""
    now = next((p for p in procs() if p.pid == was.pid), None)
    return now is not None and now.command == was.command and now.age >= was.age
