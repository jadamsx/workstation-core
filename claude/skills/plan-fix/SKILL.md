---
name: plan-fix
description: Plan the response to every human review comment on your change after /verify-comments: fixes, follow-ups and replies, approved by you before building or posting. Use for /plan-fix <change url>.
engine: plan
params: {kind: fix, intensity: medium}
---
## When
Human reviewer comments on your change, after `/verify-comments` has judged them. Automated reviewer comments and pipeline failures are `babysit`.

## Inputs
A change URL or `<project> #<number>`. Verdicts are read from `${DRAFTS_DIR:-~/drafts}/reviews/<repo>-<number>/`; with none, run `/verify-comments` first.

## Differs
- Every open human thread gets exactly one outcome, nits included, silence never: fix (valid, in scope), follow-up (valid, out of scope: a ticket drafted with `ticket-write`, not created), or decline (one-line reason).
- Fixes are a quick node table, one node per fix or logical group, each tied to its thread id. Build via `/build`, or `/verify-self` for one small fix.
- Show one table: thread, author, outcome, node or draft or reason, drafted reply. Nothing is built, created, pushed or posted before your OK; any row may change.
- Replies: load `house-style`, follow `checklists/prose.md` §7, post after the push, one per thread: "Fixed in <short sha>: <what changed>", the follow-up link once created, or the decline reason. Resolve only fixed threads, one at a time, never one an author is still discussing.

## Output
The thread table, then the go question.
