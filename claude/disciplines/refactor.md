---
extends: none
---
# Refactor

When the plan picks this: extraction, consolidation, an ownership move or cleanup with no behaviour change.

## Rules
- Define the behaviour-preservation boundary and run its proof before any structural edit. If no proof exists, write characterisation tests first.
- Keep feature changes out. A needed behaviour change becomes its own node.
- Move one ownership boundary at a time.
- Preserve public interfaces, failure behaviour, ordering and compatibility unless the plan scopes the change.
- Every intermediate state builds and passes tests.
- No new dependency or configuration without a correctness reason.
- Before removing generality, find where its other users went.

## Proof
The same proof as before the change, run again with the same result.

## Stop
Behaviour matches and the requested structure exists. Stop and report if the proof changes meaning, since the boundary was wrong.

Process: engines/build.md
