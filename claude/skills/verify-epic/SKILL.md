---
name: verify-epic
description: Review every change of an epic through the review engine, then check the seams: merge order, shared contracts and schemas, epic coverage. Use for /verify-epic <epic key or change list>.
engine: review
params: {mode: epic, intensity: medium, target: epic-key}
---
## When
An epic with several open changes, before any merges; the post-completion step runs again once they have merged. One change is `verify-change`. A plan with no changes yet is `verify-plan`.

## Inputs
The epic key (its changes are found through the tickets) or the list of change URLs, plus the epic's design note if one exists.

## Differs
- Nothing is posted before the owner's go; per-change posting follows the `change` rules.
- Load `house-style` before writing drafts.

## Output
Engine report for `epic`: one line per change with its verdict, then the epic table.
