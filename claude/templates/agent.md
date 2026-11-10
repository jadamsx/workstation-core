---
name: agent-name
description: One job in 20 words or fewer, then when to call it.
model: haiku
tools: Read, Grep, Glob
---

Question: the single question this agent answers.

What the caller hands over, and what it must not (rationale, plan, other findings). How to work, in a few lines.

## Modes
Optional. One line per mode the caller can name.

## Output
Exact shape and word cap. Example: `path:line - symbol - note`, up to 15 rows, then a total line. Zero hits: `No match.`

Common rules (read-only, refusals, findings file, report shape): `~/.claude/engines/common.md`.
