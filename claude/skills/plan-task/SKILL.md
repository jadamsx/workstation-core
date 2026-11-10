---
name: plan-task
description: Plan one bounded task, a change with a known shape, before building. Quick path for one file with an obvious check. Use for /plan-task <description> and small features or refactors.
engine: plan
params: {kind: task, intensity: medium}
---
## When
A bounded change that is not a defect. A defect is `plan-bug`; a question with no code to ship is `plan-spike`; several stories are `plan-epic`.

## Inputs
A description or ticket key. A vague input starts the interview in `engines/plan.md`.

## Differs
- Quick when it sizes quick: a table of one or a few rows with all columns.
- Disciplines: `tdd`, `acceptance-first`, `refactor` or `migration`, set on every node.
- Minimal v2 note: Requirements, node table with `covers`, Traceability and the back half.
- Notes are written with `notes-write`; prose with `house-style`.

## Output
Verdict, the node table, open questions, then the go question.
