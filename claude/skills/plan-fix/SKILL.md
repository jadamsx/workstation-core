---
name: plan-fix
description: Plan the response to every human review comment on your change after /verify-comments. Use for /plan-fix <change url>.
engine: plan
params: {kind: fix}
---
## When
Only when the owner asks. Human comments on your change, after `/verify-comments`. Automated comments and pipeline failures are `babysit`.
## Inputs
A change URL or `<project> #<number>`. Verdicts are in `${DRAFTS_DIR:-~/drafts}/reviews/<repo>-<number>/`; none: run `/verify-comments` first.
## Differs
Every open human thread gets one outcome, nits included: fix, follow-up (ticket drafted with `ticket-write`, not created) or decline (one-line reason). Fixes are a quick node table, one node per fix or group, tied to a thread id; build via `/build`, or `/verify-self` for one small fix. One table: thread, author, outcome, node or draft or reason, drafted reply. Nothing is built, created, pushed or posted before the OK. Replies per `checklists/prose.md` §7, after the push: "Fixed in <short sha>: <what>", the follow-up link, or the decline reason. Resolve only fixed threads, one at a time, never one an author is still discussing.
## Output
The thread table, then the go question.
