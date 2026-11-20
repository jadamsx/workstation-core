---
name: plan-task
description: Plan one bounded task, a change with a known shape, before building. Use for /plan-task <description> and small features or refactors.
disable-model-invocation: true
engine: plan
params: {kind: task}
---
## When
A bounded change that is not a defect.
## Inputs
A description or ticket key.
## Differs
Quick when it sizes quick: a table of one or a few rows. Disciplines `tdd`, `acceptance-first`, `refactor` or `migration` on every node. Minimal v2 note: Requirements, node table with `covers`, Traceability, the back half.
## Output
Verdict, node table, open questions, the go question.
