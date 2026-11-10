---
name: verify-change
description: Review someone else's change on a pinned checkout; post confirmed findings after your OK. Medium by default, `light` or `intense` on request, `recheck` to re-review. Use for /verify-change <url>.
engine: review
params: {mode: change, intensity: medium, target: url}
---
## When
Someone else's change, or one whose findings should be commented on it. Your own branch is `verify-self`; a group is `verify-epic`; judging comments already there is `verify-comments`.

## Inputs
The change URL (or number and project); a batch or a chain of dependent changes: all the URLs. A trailing `light`, `medium` or `intense` sets `intensity`; `recheck` is a flag.

## Differs
- `medium` is the default: `cold-reviewer`, then `finding-refuter`. Offer `intense` in one line when the diff touches auth, a migration, money or a public contract.
- Comments follow the engine's "Posting rules".
- Never approves or merges. Posting never starts before the owner's go.
- Ends early at "split first" when the change is too big to review.

## Output
Engine report: verdict (Approve, Don't approve, Split first), claims ledger, what was not checked, a missing tracker key in the title.
