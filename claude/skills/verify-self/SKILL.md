---
name: verify-self
description: Review your own built work with fresh reviewers, fix everything, cut comments, describe the change, push through the gate and babysit it green. Use before pushing. Posts nothing.
engine: review
params: {mode: self, intensity: light, target: branch}
---
## When
After `/build`, or on any branch of yours before it leaves the machine. Someone else's change is `verify-change`; an epic is `verify-change`; other people's comments are `verify-comments`. It never expands scope: it fixes findings and proves acceptance.

## Inputs
The branch, and the design note or ticket it implements. Without a ticket it stops after the report.

## Differs
- Rounds follow `engines/review.md` "Round shapes": `light` unless the owner says otherwise; a planned change reviews at the highest node `intensity`.
- Fixes: grouped by edited file, one builder per group (`engines/build.md` "The graph").
- Pushing and CI: `engines/ship.md`. Description: `change-write`; diagrams as it asks.

## Output
Engine report shape for `self` per `templates/review.md`, then the three lines for the owner. `/reflect` once if a procedure repeated or a correction came twice.
