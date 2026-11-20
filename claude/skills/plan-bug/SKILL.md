---
name: plan-bug
description: Plan the fix for one defect: reproduce first, find the root cause and every caller, set the proof. Use for /plan-bug <ticket or symptom>.
engine: plan
params: {kind: bug}
---
## When
A defect with a symptom.
## Inputs
A ticket key or a symptom with how to see it. Ask for a missing reproduction once.
## Differs
Checklist `checklists/design.md` §0, §2; the verdict says whether the behaviour is real, fixed or intended. Locate: notes, `code-locator`, `caller-mapper` for every caller, `run-digest` for the failing run. First node is `tdd` and fails at base; the fix point is the shared function. Unknown cause: first node `investigate-first`. Ends early when it does not reproduce, is fixed on base or the premise is false. Fields: `roles` for permissions, `frames` for UI. On ship, root cause and fix go into the design note.
## Output
What fails, fix point, node table, the go question.
