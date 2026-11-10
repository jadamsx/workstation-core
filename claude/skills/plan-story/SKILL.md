---
name: plan-story
description: Plan one story before building: verdict, premise attack, approach review, node graph. Use for /plan-story <ticket or description> and any change touching several files or an interface.
engine: plan
params: {kind: story, intensity: medium}
---
## When
One story, or any change larger than quick. Under a story: `plan-task` or `plan-bug`. Above it: `plan-epic`.

## Inputs
A ticket key, epic design piece, description or plan note. A vague input starts the interview in `engines/plan.md`.

## Differs
- Sizes quick: follow `plan-task`.
- Reads the ticket as in epic mode "Read what was asked for", scoped to this story, plus the design frames if the project has them.
- Epic-mode "Draw the flow" only when the story moves a boundary (`diagrams`).
- The note is v2 in full; domain checklists your team registers join `checklists/design.md`.
- Notes are written with `notes-write`; prose with `house-style`.

## Output
Verdict, node table, decisions and "To check", then the go question.
