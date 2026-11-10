---
name: change-write
description: Write or rewrite a change title and description in the team's style, filling the repo template and saying only what the diff cannot. Use when opening or tidying a change.
engine: write
params: {target: change}
---

## When
Opening or tidying a change. Diagrams: `diagrams`. Posting or updating on the source control host: `engines/ship.md`.

## Inputs
The finished branch and its diff. The tracker key from the branch name, commit bodies or the source issue; never invented. No tracker means no key.

## Differs
- Title: `<tracker key if any> <imperative summary>`, in the repo's own convention (recent merged titles show it). Register: `checklists/prose.md` §7 "Change title".
- Template: the change template (see `engines/ship.md`), filled per `engines/write.md` "Template handling".
- Budget: `engines/write.md` "Description budget".
- A change that moves a boundary adds three lines above its diagram, from the answers the plan already produced, about 35 words in all, and no second design doc:
  ```
  Breaks if wrong: <what the owner sees>.
  Replaces: <what it replaces>.
  Read by: <who consumes it>.
  ```
- Write it last, from the finished branch. Rewrite from the current diff, never append a paragraph per review round.

## Output
Title, description, the three lines from `engines/write.md`, and the suites run and not run with the reason.
