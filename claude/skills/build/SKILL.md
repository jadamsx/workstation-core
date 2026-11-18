---
name: build
description: Execute an approved plan's node graph in a worktrees, dependency-driven, then hand to verify-self. Use for /build <plan note or ticket>. Refuses without an approved plan.
engine: build
params: {scope: wave}
---
## When
After a plan skill produced a plan and you said go. Anything without an approved plan goes to the matching `plan-*` skill first. Review of the result: `verify-self`.

## Inputs
A plan note, a ticket key with an approved design note, an epic piece, or a plan from this session. Routes: `engines/build.md` "Input".

## Differs
- In a coordinator this goes to the work tab (`engines/common.md` Delegation, Handoff).
- Every ready node starts at once, up to the concurrency cap; a named node or piece is built alone, else the next unbuilt wave (say which).
- Notes are written with `notes-write`.
- Nodes route to `builder-small` or `builder` by size, per `engines/build.md` "Node prompts"; `done-check` runs last before a done report.

## Output
The engine's node report, then `/verify-self`.
