---
name: plan-story
description: Plan one story before building: verdict, premise attack, approach review, node graph. Use for /plan-story <ticket or description> and any change touching several files or an interface.
engine: plan
params: {kind: story}
---
## When
A story, or any change touching several files or an interface. Task, defect, epic, spike and review-comment plans have their own skills.
## Inputs
A ticket key, description, plan note or question.
## Differs
Reads the ticket as in `engines/plan-epic.md` "Read what was asked for", scoped to this story, plus design frames if the project has them. The plan note carries the diagram set in `engines/plan.md` "Diagrams"; a change's own diagram only when a boundary moves (`diagrams`). The note is v2 in full; domain checklists your team registers join `checklists/design.md`. Sizes quick: a table of one or a few rows.
## Output
Filled `templates/plan-summary.md`: verdict, node table, decisions and open questions, the go question.
