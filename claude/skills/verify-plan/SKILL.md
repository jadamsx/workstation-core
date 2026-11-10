---
name: verify-plan
description: Attack a ticket, epic or written plan before anyone builds it: premises, approach, gaps, sequencing. Never edits the thing reviewed. Use for /verify-plan <ticket, epic or doc>.
engine: review
params: {mode: plan, intensity: medium, target: ticket-epic-or-doc}
---
## When
A plan or epic written by someone else, or a `plan-*` output you want challenged on its own. Judging code is `verify-change`. Writing the plan is a `plan-*` skill; every plan skill already runs a premise attack.

## Inputs
A ticket key, epic, design note or document.

## Differs
- Never modifies a ticket, epic or doc under review; the report is a local draft.
- Load `house-style` before writing the report; check it against `checklists/prose.md` §1-6.
- Stops early and says so first when `premise-attacker` finds the plan resting on something untrue.

## Output
Engine report for `plan`: the call, wrong premises, per-ticket verdicts, what is missing, sequencing, the dissenting case.
