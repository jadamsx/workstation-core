---
name: plan-fix
description: Plan the response to every human review comment on your change after /verify-comments. Use for /plan-fix <change url>.
engine: plan
params: {kind: fix}
---
## When
Human comments on your change, after `/verify-comments`; `babysit` runs it unasked. Automated comments and pipeline failures are `babysit`.
## Inputs
A change URL or `<project> #<number>`. Verdicts are in `${DRAFTS_DIR:-~/drafts}/reviews/<repo>-<number>/`; none: run `/verify-comments` first.
## Differs
Every open human thread gets one outcome, nits included: fix (the default), decline (one-line reason) or, rarely, follow-up: a `ticket-write` draft, not created, only when the fix goes beyond the change's ticket, needs a product or design call, or is too large for the change. Fixes are a quick node table, one node per fix or group, tied to a thread id; build via `/build`, or `/verify-self` for one small fix. After the push, the agent that pushed posts the drafted reply per `checklists/prose.md` §7 ("Fixed in <short sha>: <what>" or the decline reason) and resolves fixed threads one at a time, never one an author is still discussing. No go gate; only follow-up drafts wait for the owner.
## Output
The thread table (thread, author, outcome, node or reason), then any follow-up drafts.
