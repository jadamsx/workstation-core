---
name: plan-epic
description: Design a whole epic before any ticket is built: premise attack, flow diagram, adversarial rounds, ticket table. Use for /plan-epic <key or brief> or "plan this whole thing".
engine: plan
params: {kind: epic, intensity: medium}
---
## When
A product brief or epic key spanning several stories or repos. One story is `plan-story`, one task `plan-task`, one defect `plan-bug`, one feasibility question `plan-spike`. Reviewing a plan someone else wrote is `verify-plan`.

## Inputs
An epic key, a brief or a description. A vague brief starts the interview; a missing key is asked for once.

## Differs
- Runs epic mode in `engines/plan.md` in order: read, attack, platform questions, decision records, flow, converge, cut, report. A false premise or a platform seam you must rule on stops the run; say which.
- Diagrams use `diagrams`. New ticket text uses `ticket-write`, kept as drafts in the note; no story is created before approval.
- Notes lookup includes the relevant `${NOTES_DIR:-~/notes}/areas/` index.
- The note is v2 in full, with the diagrams and ticket table in it, and every plan field the epic touches. Each ticket row names the plan skill that expands it.
- Notes are written with `notes-write`.

## Output
The engine's epic report, then the go question.
