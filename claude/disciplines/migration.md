---
extends: none
---
# Migration

When the plan picks this: schema, data, API, protocol, configuration or dependency transitions that need a rollback and proof that data survives.

## Rules
- Map current readers, writers, data shape, compatibility window and owners before editing.
- Define the forward path and the rollback path.
- Preserve existing data. Destructive steps are explicit and separately authorised.
- Keep mixed-version operation safe wherever a rollout can overlap.
- Sequence expand, migrate, verify, then contract. Contract is a later node.
- Retries are idempotent and partial failure is observable. `up` can run twice; `down` removes only what `up` created.
- Verify the old path and the new path at each transition stage. Search consumers on `origin/<base>`, not local checkouts.

## Proof
Run up, down and up again on a scratch database. Show old and new code both working in the middle state.

## Stop
The requested stage passes. Do not perform a later destructive contraction implicitly. Stop and report if rollback cannot be shown.

Process: engines/build.md
