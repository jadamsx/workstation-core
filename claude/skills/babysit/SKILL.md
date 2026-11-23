---
name: babysit
description: Drive a change to green: watch the pipeline and automated reviewers, fix what is valid, loop until clean. Use for /babysit <url> or after opening a change.
engine: ship
params: {phase: loop, target: current-branch}
---
## When
After a change is open, or the owner says babysit. Reviewing happens before the push (`engines/review.md`, mode `self`); human threads on the change are judged by mode `comments`.

## Inputs
A change URL or `<project> #<number>`. Absent: the change for the current branch. Optional `timeout=<minutes>`, default 120 minutes of wall-clock from when babysit begins. A non-numeric or zero value falls back to the default.

## Differs
- Never stops to ask; only reports.
- Rewrites the title and description once at the start, without being asked, via `change-write`.
- Human threads on our own change (the owner is the author): after judging, fixes valid ones, declines the rest with a one-line reason, and after the push the pushing agent posts the replies and resolves fixed threads (`/plan-fix`, no go gate). A rare follow-up is a `ticket-write` draft in the report. On anyone else's change nothing is fixed, posted or resolved; replies are drafted in the report. Replies follow `checklists/prose.md` §7.
- Records `date +%s` when it begins. Each wait is one `run_in_background` call of `timeout <N> <the change CLI's watch command>`, N the seconds remaining written as a literal number (never `$(...)` or `${...}`). A watch without `timeout`, a sleep or a loop is never used. A watch that returns while the pipeline is still pending is started again with the new remaining seconds. It says it hit the timeout only when `date +%s` shows the full minutes elapsed.
- At the timeout it stops waiting, starts no new step, never interrupts a push or commit already started, and reports the pipeline and review state as it stands. It never loops on.
- Never merges, approves or unapproves; green CI plus a clean review means stop and report.

## Output
`engines/ship.md` Report.
