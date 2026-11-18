---
name: babysit
description: Drive a change to green: watch the pipeline and automated reviewers, fix what is valid, loop until clean. Use for /babysit <url> or after opening a change.
engine: ship
params: {phase: loop, target: current-branch}
---
## When
After a change is open, or the owner says babysit. Reviewing happens before the push (`engines/review.md`, mode `self`); human comments are judged by mode `comments`.

## Inputs
A change URL or `<project> #<number>`. Absent: the change for the current branch. Optional `timeout=<minutes>`, default 120 minutes of wall-clock from the start.

## Differs
- A coordinator hands the loop to the work tab per Handoff in `engines/common.md`.
- Never stops to ask; only reports.
- Rewrites the title and description once at the start, without being asked, per `engines/write.md` target `change` and the repo template.
- Any reply drafted to a review comment follows `checklists/prose.md` §7.
- At the timeout, finishes the step in flight, starts no new one, and reports the pipeline and review state as it stands. It never loops on.
- Never merges, approves or unapproves; green CI plus a clean review means stop and report.

## Output
`engines/ship.md` Report.
