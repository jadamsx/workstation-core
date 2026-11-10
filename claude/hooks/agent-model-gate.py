#!/usr/bin/env python3
"""Refuse Agent spawns that would run on the session model or on the wrong model for the agent.

Subagents never run on the session model; they burn the usage budget.
An agent whose definition pins a `model:` may omit `model` (the pin applies) or repeat it.
Opus is allowed by explicit override only for the agents in MODEL_CONFIG["opus_override"]. Agents without a
pin must name sonnet or haiku, except the built-ins in BUILTIN_DEFAULT_SONNET: with no `model` the
hook injects sonnet through updatedInput. Forks always inherit and pass.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from hook_config import load

MODEL_CONFIG = {
    "cheap": {"sonnet", "haiku"},
    "opus_override": set(load().get("opus_override", [])),
    "builtin_default_sonnet": {"explore", "general-purpose", "plan", "claude"},
}
CHEAP = MODEL_CONFIG["cheap"]
OPUS_OVERRIDE = MODEL_CONFIG["opus_override"]
BUILTIN_DEFAULT_SONNET = MODEL_CONFIG["builtin_default_sonnet"]
AGENT_DIRS = (Path.home() / ".claude" / "agents", Path.home() / ".claude" / "plugins")
MODEL_LINE = re.compile(r"^model:\s*([\w.-]+)\s*$", re.MULTILINE)


def pinned_model(agent: str) -> str | None:
    name = agent.split(":")[-1]
    for root in AGENT_DIRS:
        for path in root.rglob(f"{name}.md"):
            if path.parent.name != "agents":
                continue
            head = path.read_text(errors="ignore").split("---", 2)
            match = MODEL_LINE.search(head[1] if len(head) > 2 else "")
            if match:
                return match.group(1)
    return None


def is_bare_builtin(agent: str) -> bool:
    return (
        ":" not in agent
        and agent.lower() in BUILTIN_DEFAULT_SONNET
        and not (AGENT_DIRS[0] / f"{agent}.md").exists()
    )


def block(message: str) -> None:
    print(f"Agent spawn blocked: {message}", file=sys.stderr)
    sys.exit(2)


def allow_with_sonnet(tool_input: dict) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "updatedInput": {**tool_input, "model": "sonnet"},
                }
            }
        )
    )
    sys.exit(0)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    if payload.get("tool_name") != "Agent":
        sys.exit(0)
    tool_input = payload.get("tool_input") or {}
    agent = tool_input.get("subagent_type") or "general-purpose"
    if agent == "fork":
        sys.exit(0)
    model = tool_input.get("model")
    pin = pinned_model(agent)
    name = agent.split(":")[-1]

    if model is None and is_bare_builtin(agent):
        allow_with_sonnet(tool_input)
    if pin and model in (None, pin):
        sys.exit(0)
    if model == "opus" and name in OPUS_OVERRIDE:
        sys.exit(0)
    if model in CHEAP:
        sys.exit(0)
    if pin:
        block(
            f"{agent} is pinned to {pin}; omit model or pass {pin!r} (opus only for {sorted(OPUS_OVERRIDE) or 'none'})."
        )
    block(
        f'model={model!r} for {agent}. Unpinned subagents must name model: "sonnet" (edits, reviews) '
        'or "haiku" (search, bulk reads), never the session model.'
    )


if __name__ == "__main__":
    main()
