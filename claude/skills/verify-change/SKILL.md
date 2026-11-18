---
name: verify-change
description: Review someone else's change on a pinned checkout; post confirmed findings after your OK. Light by default; `medium`, `intense`, `epic` or `recheck` on request. Use for /verify-change <url or epic>.
engine: review
params: {mode: change, intensity: light, target: url}
---
## When
Someone else's change, or one whose findings should be commented on it. Your own branch is `verify-self`; an epic or a group of changes is epic mode here; judging comments already there is `verify-comments`.

## Inputs
The change URL (or number and project); a batch or a chain of dependent changes: all the URLs. An epic key, or a trailing `epic`, sets mode `epic`: every change of the epic through the engine, then the seams and, after merge, the delivery check. A trailing `light`, `medium` or `intense` sets `intensity`; `recheck` is a flag.

## Differs
- A coordinator hands this review to the work tab per Handoff in `engines/common.md`.
- Rounds follow the engine's "Round shapes", `light` by default; auth, input, secrets or permissions raise it to `medium`. Offer `intense` in one line when the diff touches a migration, money or a public contract.
- Comments follow the engine's "Posting rules".
- Never approves or merges. Posting never starts before the owner's go.
- Ends early at "split first" when the change is too big to review.

## Output
Engine report per `templates/review.md`: verdict (Approve, Don't approve, Split first), claims ledger, what was not checked, a missing tracker key in the title. Epic mode adds one line per change, the seam table and delivered, partial or missing per story.
