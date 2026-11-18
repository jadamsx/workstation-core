---
name: plan-story
description: Plan before building, by kind: story, task, bug, epic, fix, spike. Use for /plan-story <ticket or description> [kind] and any change touching several files or an interface.
engine: plan
params: {kind: story, intensity: medium}
---
## When
Any plan before a build. `kind` is story (default), task, bug, epic, fix or spike; pick it from the input, or take it as the owner gave it. Reviewing a plan someone else wrote is `verify-plan`.

## Inputs
A ticket key, epic brief, description, plan note, symptom, change URL or question. A vague input starts the interview in `engines/plan.md`; ask for a missing key or reproduction once.

## Differs
All kinds: notes are written with `notes-write`, prose with `house-style`, and the build is handed off per Handoff in `engines/common.md`.

- story: reads the ticket as in epic mode "Read what was asked for", scoped to this story, plus design frames if the project has them. "Draw the flow" only when a boundary moves (`diagrams`). The note is v2 in full; domain checklists your team registers join `checklists/design.md`. Sizes quick: follow task.
- task: a bounded change that is not a defect. Quick when it sizes quick: a table of one or a few rows. Disciplines `tdd`, `acceptance-first`, `refactor` or `migration` on every node. Minimal v2 note: Requirements, node table with `covers`, Traceability, the back half.
- bug: checklist `checklists/design.md` §0, §2; the verdict says whether the behaviour is real, fixed or intended. Locate: notes, `code-locator`, `caller-mapper` for every caller, `run-digest` for the failing run. First node is `reproduce-first` and fails at base; the fix point is the shared function. Unknown cause: first node `investigate-first`. Ends early when it does not reproduce, is fixed on base or the premise is false. Fields: `roles` for permissions, `frames` for UI. On ship, root cause and fix go into the design note.
- epic: runs epic mode in `engines/plan.md` and `engines/plan-epic.md`, in the order they give. A false premise or a platform seam you must rule on stops the run. Diagrams use `diagrams`; ticket text uses `ticket-write`, kept as drafts; no story is created before approval. Notes lookup includes the `${NOTES_DIR:-~/notes}/areas/` index. The note is v2 in full with diagrams, ticket table and every plan field touched; each ticket row names the kind that expands it.
- fix: only when the owner asks; human review comments on your change after `/verify-comments` (verdicts in `${DRAFTS_DIR:-~/drafts}/reviews/<repo>-<number>/`; none: run it first). Automated comments and pipeline failures are `babysit`. Every open human thread gets one outcome, nits included: fix, follow-up (ticket drafted with `ticket-write`, not created) or decline (one-line reason). Fixes are a quick node table, one node per fix or group, tied to a thread id; build via `/build`, or `/verify-self` for one small fix. One table: thread, author, outcome, node or draft or reason, drafted reply. Nothing is built, created, pushed or posted before the OK. Replies per `checklists/prose.md` §7, after the push: "Fixed in <short sha>: <what>", the follow-up link, or the decline reason. Resolve only fixed threads, one at a time.
- spike: discipline `spike`; the answer matters more than the code. The verdict names the decision it informs and who makes it; none, no run. Prior art: notes, then `researcher` and `code-locator`. One to three `spike` nodes; `owns` is a scratch branch or copy; nothing merges. Review is one `premise-attacker` round. Findings go to `projects/<slug>/research/` via `notes-write`, linked from the index and the decision.

## Output
Story and task: verdict, node table, decisions and open questions, the go question. Bug: what fails, fix point, node table, go. Epic: the engine's epic report, go. Fix: the thread table, go. Spike: question, decision, box, experiment, node row, go.
