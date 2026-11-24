---
name: verify-self
description: Review your own built work with fresh reviewers, fix everything, cut comments, describe the change, push through the gate and babysit it green. Use once the draft MR is pushed and green, before it is marked ready. Posts only a fix plan's replies.
engine: review
params: {mode: self, intensity: medium, target: branch}
---
## When
After `/build`, once the branch is pushed as a draft and CI is green. Someone else's change is `verify-change`; an epic is `verify-change`; other people's comments are `verify-comments`. It never expands scope: it fixes findings and proves acceptance.

## Inputs
The branch, and the design note or ticket it implements. Without a ticket it stops after the report.

## Differs
- Rounds follow `engines/review.md` "Round shapes": `medium` unless the owner says otherwise; the level follows the `self` rule in `engines/review.md` "Params".
- Fixes: grouped by edited file, one builder per group (`engines/build.md` "The graph").
- Pushing and CI: `engines/ship.md`. Description: `change-write`; diagrams as it asks.

- Fix plan: after a successful push, the agent that pushed posts each drafted reply with the reply verb in `engines/ship.md` and resolves only fixed threads, one at a time, never one an author is still discussing. No second OK.

- Pass: with no open Blocker, as the final step, mark the draft MR ready (`glab mr update --ready` or `gh pr ready`).

## Output
Engine report shape for `self` per `templates/review.md`, then the three lines for the owner. `/reflect` once if a procedure repeated or a correction came twice.
