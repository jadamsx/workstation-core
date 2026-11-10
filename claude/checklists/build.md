# Build checklist

What the author runs on its own diff before review, so review stops catching the same things twice. The reviewer's list is `checklists/review-core.md`. Sources: `checklists/review-core.md`, `~/.claude/CLAUDE.md`, and the research cited inline in §3.

## Killer items

Run these on your own diff before handing a node or change to review. Quote the numbers you checked.
1. "Done" has tool output, a test run or a screenshot from the same turn. "The tests would confirm this" is not a run (§3).
2. No test weakened, deleted or special-cased to make a failure go away, and the test fails when the code it targets is broken (§3 Tests).
3. Nothing changed that was not asked for; a discovered improvement is a new ticket, not scope (§3 Scope).
4. No broad `except` or silent fallback added to make a failing path look like success (§3 Code).
5. No secret hardcoded or logged, input at a trust boundary validated, and no sibling endpoint left without the authz check (§3 Security).
6. Reuse before writing: this codebase, then stdlib, then an installed dependency (`engines/build.md` Author duties).
7. Rebased on latest base branch before work started; no `git checkout --`, `restore`, `stash` or force-push in a dirty tree (§3 Scope, Context).
8. Every `file:line` in a claim resolves in the actual diff, and no URL or package was cited unopened (§3 Honesty).

## Reference

## 3. AI failure modes

The one shared source; review, design and the other checklists point here.

### Honesty and verification
- A claim of "done" with no tool output, test run or screenshot in the same turn is unverified.
  Show the run. (simonwillison.net/2025/Aug/29/the-perils-of-vibe-coding)
- "The tests would confirm this" is not a test run. Run it or say you didn't.
- Every file:line in a claim resolves in the actual diff, not from memory. (`engines/review.md`
  "Reviewer conduct", applied to the author first)
- No fabricated URL, package, or citation: a suggested dependency is checked against the lockfile
  before it's used. (arxiv.org/abs/2406.10279)

### Tests
- No test weakened, deleted, or loosened to make a failure go away instead of fixing the cause.
  (metr.org/blog/2025-06-05-recent-reward-hacking)
- No test special-cased to the exact input under test rather than the behaviour.
- No mock stands in for the thing the test is meant to prove; the test fails if the mock is
  removed.
- The test fails when the code it targets is deliberately broken. A test that can't fail is
  asserting the harness, not the fix. (CLAUDE.md Testing)

### Code
- No broad `except` or silent fallback (`[]`, `None`, `{}`) added just to make a failing path look
  like success.
- No duplicated helper where one already exists in this codebase. → review-core §3
- No dead code left behind: unused imports, unreachable branches, stale flags.

### Security
- No sibling endpoint left without the authz check the one under review has. (review §8 IDOR)
- No secret, key or token hardcoded or logged, including in a debug statement.
- Input at a trust boundary (route, integration layer, event consumer) is validated, not passed straight
  into a query or template.

### Scope and instructions
- Nothing changed that wasn't asked for; state what you did **not** change even though you could
  have.
- The diff matches the plan or ticket; a discovered improvement is a new ticket, not a scope
  expansion.
- No `git checkout --`, `restore`, `stash`, or force-push in a dirty tree. (settings deny stash, restore and
  checkout --)

### Context
- No constraint from the original task dropped after a compaction or long session; re-check
  against the ticket before finishing.
- Checked out and rebased onto latest `main` (or the repo's base branch) before this session
  started work, not against a stale local copy. (the repo's `CLAUDE.md`, if it has one)

Process: engines/build.md
