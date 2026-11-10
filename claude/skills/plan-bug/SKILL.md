---
name: plan-bug
description: Plan the fix for one defect: reproduce first, find the root cause and every caller, set the proof. Use for /plan-bug <ticket or symptom> and any "this is broken" report.
engine: plan
params: {kind: bug, intensity: medium}
---
## When
A defect with a symptom. If the cause is unknown after the first look, the first node is `investigate-first`. A feasibility question is `plan-spike`.

## Inputs
A ticket key or a symptom with how to see it. A missing reproduction is asked for once, in the engine's interview.

## Differs
- Checklist: `checklists/design.md` §0, §2. The verdict says whether the behaviour is real, already fixed or intended.
- Locate: notes first (runbooks, gotchas, incident notes for the symptom), then `code-locator`, `caller-mapper` for every caller of the function to touch, `run-digest` for the failing run.
- The reproduce test is the first node, discipline `reproduce-first`, and must fail at base. The fix point is the shared function every caller routes through.
- Ends early when the bug does not reproduce, is fixed on base, or the premise is false; say which.
- Plan fields: `roles` for a permissions bug, `frames` for a UI bug.
- On ship, root cause and fix summary go into the design note via `notes-write`.

## Output
What fails, where the fix point is, the node table and the go question.
