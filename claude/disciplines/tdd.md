---
extends: none
---
# TDD

When the plan picks this: new behaviour with a clear input and output (a function, a route, a node handler) where the test can be written before the code exists.

## Rules
- Write the failing test first, at the level the behaviour lives: unit for logic, integration for a route or query.
- Run it and read the failure. It must fail at an assertion on the new behaviour, not in setup, an import or an `AttributeError`.
- A bugfix test fails at base, at an assertion, and passes with the fix. A test that passes without the source change proves nothing.
- Delete any test that would pass against a do-nothing implementation.
- Write the least code that turns it green. Do not add a branch no test demands.
- Refactor only on green, with the same tests as the bracket.
- Fixtures behave like the real thing where it matters: duplicate keys, error envelopes, pagination.
- Prefer one extra case in an existing test file over a new file.

## Proof
Every new test fails against a do-nothing implementation. A bugfix test fails on the base commit and passes on the fix. Prove it on a scratch copy by breaking the code, never in the worktree.

## Stop
The acceptance tests pass and the repo's gates pass. Stop on a test you cannot make fail for the right reason, and report it.

Process: engines/build.md
