---
name: plan-epic
description: Design a whole epic before any ticket is built: premise attack, flow diagram, ticket table. Use for /plan-epic <key or brief> or "plan this whole thing".
disable-model-invocation: true
engine: plan
params: {kind: epic}
---
## When
A brief or epic key spanning several stories or repos.
## Inputs
An epic key, brief or description.
## Differs
Runs epic mode in `engines/plan.md` and `engines/plan-epic.md`, in the order they give. A false premise or a platform seam you must rule on stops the run. Diagrams use `diagrams`; ticket text uses `ticket-write`, kept as drafts; no story is created before approval. Notes lookup includes the `${NOTES_DIR:-~/notes}/areas/` index. The note is v2 in full with diagrams, ticket table and every plan field touched; each ticket row names the plan skill that expands it.
## Output
The engine's epic report, then the go question.
