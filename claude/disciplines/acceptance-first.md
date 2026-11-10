---
extends: none
---
# Acceptance first

When the plan picks this: new behaviour, a product slice or an integration, where the risk is building more than was asked.

## Rules
- Write the observable acceptance and the explicit non-goals from the ticket and the repo before touching code.
- Trace the entry point through every layer that owns an invariant. Deliver one coherent end-to-end path across those layers; do not force it into one file or a local patch.
- Reuse the fitting seam. Refactor when patching would duplicate behaviour, weaken ownership or hide the root cause.
- No modes, providers, config, extensibility or polish unless acceptance needs them.
- Add a surface, dependency, service, config or migration only for the lifecycle design or acceptance, and state the trade-off in the report.
- Keep the work runnable at every step. Safety rules from the build ladder still hold.

## Proof
Exercise the path for real (the route, the node, the screen) and run the focused tests.

## Stop
Acceptance passes. Report only material omissions and the trigger that would add them. Stop and ask when acceptance and non-goals conflict.

Process: engines/build.md
