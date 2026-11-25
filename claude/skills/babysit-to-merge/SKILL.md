---
name: babysit-to-merge
description: Keep each change green, conflict-free and re-reviewed until approved, and report only when it needs the owner. Use for /babysit-to-merge <change links>, run in a /loop by the lead.
---
## When
The lead, after the work tab says `done`, on the owner's own changes only. The owner starting it is the OK for its re-request calls. Never merge, approve or mark ready.
## Inputs
Change links.
## Differs
Reads go through `change-reader`; a failed read is `blocked`, never nothing new. Messages go to the work tab's pane via `herdr agent prompt`. Per change, each wake:
- Red CI or a conflict: one line to the work tab naming the change and the failure.
- New human threads: `/verify-comments`, then `/plan-fix`, and hand the plan to the work tab.
- Re-request review from non-approvers other than the owner, only when the head sha differs from the one last re-requested.
- Stop and report only on a Blocker, a `blocked` from the work tab, or all changes approved, green and conflict-free.
## Output
One line per change (state, open threads, next, last re-requested sha); on stop, the stop report.