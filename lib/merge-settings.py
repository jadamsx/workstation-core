#!/usr/bin/env python3
"""Merge the repo's settings base and machine overlay into a live Claude Code settings.json.

``merge`` prints the new live file: keys named in ``x-workstation.ownedKeys`` come from
base + overlay, hook entries pointing into ~/.claude/hooks/ are replaced by the base's, and
everything else (for example herdr's SessionStart hook) is kept as found. ``adopt`` prints a
new base built from the live file, subtracting what the overlay contributes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HOME_TOKEN = "__HOME__"


def load(path: Path | None, home: str) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text().replace(HOME_TOKEN, home))


def deep_merge(base: Any, overlay: Any) -> Any:
    if isinstance(base, dict) and isinstance(overlay, dict):
        merged = dict(base)
        for key, value in overlay.items():
            merged[key] = deep_merge(base[key], value) if key in base else value
        return merged
    if isinstance(base, list) and isinstance(overlay, list):
        return base + [item for item in overlay if item not in base]
    return overlay


def subtract(live: Any, overlay: Any, base: Any) -> Any:
    """Remove from ``live`` what the overlay contributes; scalars the overlay sets revert to base."""
    if isinstance(live, dict) and isinstance(overlay, dict):
        out = {}
        for key, value in live.items():
            if key not in overlay:
                out[key] = value
                continue
            base_value = base.get(key) if isinstance(base, dict) else None
            kept = subtract(value, overlay[key], base_value)
            if kept is not None and kept != {} and kept != []:
                out[key] = kept
        return out
    if isinstance(live, list) and isinstance(overlay, list):
        return [item for item in live if item not in overlay]
    return base


def commands(entry: dict[str, Any]) -> list[str]:
    return [hook.get("command", "") for hook in entry.get("hooks", [])]


def is_owned(entry: dict[str, Any], meta: dict[str, Any]) -> bool:
    return any(
        meta["ownedHookPath"] in c
        and not any(m in c for m in meta.get("foreignHookMarkers", []))
        for c in commands(entry)
    )


def is_dropped(entry: dict[str, Any], meta: dict[str, Any]) -> bool:
    return any(m in c for c in commands(entry) for m in meta.get("dropHookMarkers", []))


def merge(
    base: dict[str, Any], overlay: dict[str, Any], live: dict[str, Any]
) -> dict[str, Any]:
    meta = base["x-workstation"]
    desired = deep_merge(
        {k: v for k, v in base.items() if k != "x-workstation"}, overlay
    )
    result = dict(live)
    for key in meta["ownedKeys"]:
        if key in desired:
            result[key] = desired[key]
        else:
            result.pop(key, None)
    hooks: dict[str, list[Any]] = {}
    for event in dict.fromkeys([*desired.get("hooks", {}), *live.get("hooks", {})]):
        kept = [
            e
            for e in live.get("hooks", {}).get(event, [])
            if not is_owned(e, meta) and not is_dropped(e, meta)
        ]
        entries = desired.get("hooks", {}).get(event, []) + kept
        if entries:
            hooks[event] = entries
    if hooks:
        result["hooks"] = hooks
    else:
        result.pop("hooks", None)
    return result


def adopt(
    base: dict[str, Any], overlay: dict[str, Any], live: dict[str, Any]
) -> dict[str, Any]:
    meta = base["x-workstation"]
    new = {k: v for k, v in base.items() if k not in ("x-workstation", "hooks")}
    for key in meta["ownedKeys"]:
        if key in live:
            new[key] = subtract(live[key], overlay.get(key), base.get(key))
        else:
            new.pop(key, None)
    hooks = {}
    for event, entries in live.get("hooks", {}).items():
        owned = [e for e in entries if is_owned(e, meta) and not is_dropped(e, meta)]
        if owned:
            hooks[event] = owned
    new["hooks"] = hooks
    new["x-workstation"] = meta
    return new


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["merge", "adopt"])
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--overlay", type=Path)
    parser.add_argument("--live", type=Path, required=True)
    parser.add_argument("--home", required=True)
    args = parser.parse_args()
    base, overlay, live = (
        load(p, args.home) for p in (args.base, args.overlay, args.live)
    )
    result = (
        merge(base, overlay, live)
        if args.command == "merge"
        else adopt(base, overlay, live)
    )
    text = json.dumps(result, indent=2)
    if args.command == "adopt":
        text = text.replace(args.home, HOME_TOKEN)
    sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
