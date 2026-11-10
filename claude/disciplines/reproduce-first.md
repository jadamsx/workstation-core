---
extends: tdd
---
# Reproduce first

When the plan picks this: a bug or a small behaviour change where the failure can be shown before the fix. Not for unknown causes; that is investigate-first.

## Rules
- Reproduce the failure first when it is economical. Otherwise capture the strongest evidence available (log line, request, stack) and say why a test was not possible.
- The reproduce test follows the bugfix rule in `disciplines/tdd.md`.
- Trace the symptom to the mechanism, then change the narrowest layer that owns the wrong behaviour. Grep every caller of the function first; fix it once where all callers route through.
- Preserve unrelated behaviour and any changes already in the tree.
- No cleanup, renaming or abstraction outside the fix.
- Add only the regression proof the bug needs.

## Proof
The `disciplines/tdd.md` proof, plus the nearest affected gate (the suite for that module, then lint and types).

## Stop
The failure is fixed and the regression proof passes. Do not widen. Stop and report if the reproduce test cannot be made to fail, since the cause is then not understood.

Process: engines/build.md
