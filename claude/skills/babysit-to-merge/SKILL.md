---
name: babysit-to-merge
description: Keep each MR green, conflict-free and re-reviewed until approved, and report only when it needs the owner. Use for /babysit-to-merge <MR links>, run in a /loop by the lead.
---
## When
The lead, after the work tab says `done`. The owner invoking it is the OK for the re-request calls below. Never merge, approve or mark ready.
## Inputs
MR links.
## Differs
Reads go through `change-reader`; messages go through `herdr agent prompt <work pane>`. Per MR, each wake:
- Red CI or a conflict: one line to the work tab naming the MR and the failure.
- New human threads: `/verify-comments`, then `/plan-fix`, and hand the plan to the work tab.
- Re-request review from every non-approver once per new head sha.
- Stop and report only on a Blocker, a `blocked` from the work tab, or all MRs approved, green and conflict-free.
## Output
One line per MR (state, open threads, next); on stop, the stop report.
