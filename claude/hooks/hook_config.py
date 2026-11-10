"""Layer data for the guard hooks, read from every ``*.json`` in ``hooks.d`` beside them.

Each layer ships its own file there (``personal.json``, ``team.json``), so no build step has to
merge anything. Files load in name order: lists add up, objects merge, scalars from a later file
win. ``HOOKS_CONFIG_DIR`` points elsewhere. A missing directory means every default applies.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

REMOTE_PATH_RE = re.compile(
    r"^(?:[\w+.-]+://[^/]+/|[^/]*:)?((?:[\w.-]+/)+[\w.-]+?)(?:\.git)?/?$"
)


def merge(base: Any, extra: Any) -> Any:
    if isinstance(base, dict) and isinstance(extra, dict):
        return {
            **base,
            **{k: merge(base[k], v) if k in base else v for k, v in extra.items()},
        }
    if isinstance(base, list) and isinstance(extra, list):
        return base + [v for v in extra if v not in base]
    return extra


def load() -> dict[str, Any]:
    folder = Path(
        os.environ.get("HOOKS_CONFIG_DIR")
        or Path(__file__).resolve().parent / "hooks.d"
    )
    config: dict[str, Any] = {}
    for path in sorted(folder.glob("*.json")) if folder.is_dir() else []:
        config = merge(config, json.loads(path.read_text()))
    return config


def ticket_exempt(prefixes: list[str], cwd: str, project_id: str = "") -> bool:
    """True when the change belongs to a project whose path starts with one of ``prefixes``.

    The path comes from the source control host's project id when it is a full path, else from the ``origin`` remote.
    """
    if not prefixes:
        return False
    path = project_id.strip("/")
    if "/" not in path:
        try:
            url = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=10,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return False
        found = REMOTE_PATH_RE.search(url)
        path = found.group(1) if found else ""
    return path.lower().startswith(tuple(p.lower() for p in prefixes))
