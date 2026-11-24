# Build engine

Executes an approved plan's node graph in worktrees, dependency-driven. Plan vocabulary (node, wave, needs, owns, intensity, discipline): `engines/plan.md`. Review depth and rounds: `engines/review.md`. Gates, git safety, delegation, report and refusals: `engines/common.md`. Push, change and CI: `engines/ship.md`. Author checklist: `checklists/build.md`.

## Params

| Param | Values | Effect |
|---|---|---|
| `scope` | `node`, `wave`, `plan` | what to build. Default: the whole ready graph, every node whose needs are done. `node` builds one node |

## Input

The plan is the spec. Without an approved plan, refuse and name the plan step.

| Input | Route |
|---|---|
| A plan note, or a ticket key whose design note in `${NOTES_DIR:-~/notes}/projects/<slug>/designs/` has `status: approved` | build it |
| An epic design piece (a row of the epic's design note, or the epic design from this session) | plan a story for that piece, then build |

Never ask for a ticket, or for the input in a particular shape, when one of these is in front of you. A named node or piece is what gets built. Where the plan names an epic piece, that piece's "Done when" is its acceptance and every node traces to it. A ticket key anywhere in the plan settles branch naming and the change title; with none the work stays local and uncommitted, and the `self` review skips the change, the push and the CI loop.

## Steps

1. **Gate.** Done when the design note says `status: approved`, and its node table has agent, discipline, owns, wave, intensity, review and acceptance per node. For a `format: v2` note `notes-lint <note>` must report none of `fr-missing`, `fr-uncovered`, `covers-empty`, `covers-unknown`, `covers-column`, `trace-missing`, `trace-column`; refuse while any FR has no covering node or any node has no `covers`, and name the rows. A keyless quick plan has no note: the owner's go in this session and its table in chat are the gate. Otherwise stop and name the plan step to run. Never write a Progress list for an unapproved plan. A request that adds scope beyond the table goes back to plan as a decision node.
2. **Worktrees** (below). Move the ticket to in progress when there is a key and the tracker has the step (`engines/ship.md` Tracker). Done when every repo the plan touches has its worktree at fresh `origin/<base>` and no node runs in the owner's checkout.
3. **Build the graph** (below), after reading the plan's area index in the notes via `code-locator` notes mode. Done when every node passed its gates and its own acceptance.
4. **Whole-repo gates, once**: a `verify-run` node, `run-digest`. Done when formatter, linter, typecheck, `pre-commit` and the suite ran once on the whole tree, before completion is claimed.
5. **Prove it** (below). Done when coverage gaps are closed and each stated behaviour ran against the real thing, or "no environment reachable" is said in those words.
6. **Hand over** to the `self` review, once, at medium, after the draft change is pushed and green. Done when the report shows the parallelism and each node's done-check.

A false premise found mid-build, or work outside the plan, stops the run and goes back to plan as a decision node. A Blocker open at round 3 stops the whole run (`engines/review.md`): report what is stuck and do not route around it. A blocked pre-push gate belongs to the `self` review (two fix-and-retry rounds, then stop and show the error).

## Worktrees

`EnterWorktree` for every repo the plan touches, local-only work included, after `git fetch origin` in that repo. Base is the repo's default branch (`git symbolic-ref refs/remotes/origin/HEAD`; never assume `main`). Location `<repo>/.claude/worktrees/<key>`, key = the ticket key, or `local-<plan-slug>` with none. Branch `<KEY>/<short-description>`; with no key `local/<plan-slug>`, never pushed. One ticket, one tree per repo: isolation is not permission to start a second ticket.

The work tab builds nodes itself by default. Builder agents are only for independent nodes that run in parallel; each parallel node gets its own worktree `<ticket>-<node>` and agent, and parallel nodes never share either. A node branches from its parent branch: the ticket branch, or the branch of the need that finished last, with its other needs merged in first, so changes stack and the next node starts without waiting for approval.

## The graph

No wave barriers. Whenever a node's needs are all done, start it, up to `build_concurrency_cap` in `claude/resource-policy.json` (6 when the file is absent). A slow node blocks only its dependents, and a failed node does not stop its siblings. A fix round's fixes are grouped by the file they edit; each group goes to its own builder in its own worktree, all in one dispatch up to the cap (never one builder carrying several groups), and the group branches merge after. The node report line is `Fix groups: <n>, builders: <n>`.

- The work tab never idle-waits while a ready node exists. When nothing is ready, the `/loop` wakes it to check the running gate, retry or review.
- One gate per app runs at a time, never a second suite in another worktree while one runs (`engines/common.md`); the others queue and their nodes keep building. Each app keeps its own worker cap from the resource policy, and no browser gate is shared across apps.
- A wave is only the commit and rebuild grouping. When all its nodes are done the main thread lands their branches onto the plan's ticket branch in node order as one commit group per repo trailed `Wave: Wn`, removes the node worktrees, then rebuilds the stack with the plan's stack file. A conflict means the Owns were wrong: stop, a planning error. Whole-diff rounds belong to the `self` review.
- Node builders run only their focused proof plus lint and types on touched files, and share the repo's caches so setup stays cheap. The formatter, the suite and `pre-commit` run once, in the final `verify-run` node.
- Overlapping `owns` is a need, or the node hands a patch to the integration owner the plan names; lockfiles, generated files and shared config sit in exactly one node's `owns`. A node that needs a file outside its `owns` reports `scope-grew` and stops. A merge conflict means the plan's `owns` or needs were wrong: stop and treat it as a planning error.
- Progress is a one-line plan-note edit: `[~]` when the node starts, `[x]` when it is done, in the same edit adding its Decisions and Traps lines, so a compaction loses nothing. A v2 node's own tests go in its Traceability row's Test cell. Wave decisions are appended to the note's Decisions, one dated line each.

Discovered work that is not this ticket becomes a ticket draft under the note's `## Out`, never scope. Anything the build adds, drops or does differently from the plan is a decision node in the table before building.

## Node prompts

Each agent prompt gives the node spec (acceptance, `owns`, discipline, checklists), the worktree path and the repo, and says to apply `checklists/build.md` before reporting done. Each also carries:

- **Plan lines**: the node's `owns` paths and the plan's `Decided:`, `Standing:` and `Not-building:` lines, carried verbatim.
- **Size routing**: an agent node that is low risk, touches one or two files and is mechanical goes to `builder-small`; every other agent node to `builder`. If a small agent fails, or its work fails review, rerun on the larger agent without asking.
- **Open findings**: the work tab reports its open Blocker and Should-fix findings in the node's done report, not as a lead decision before the change opens.
- **Agent rules**: `engines/agent-core.md` applies; a file an agent says it rebuilt is re-reviewed and re-proven.
- **For a v2 plan**, the FR ids the node delivers (its `covers` cell) with each FR's text. A node that would add, drop or change an FR is a decision node.
- **What already ran**: the real suite and numbers from the nodes that just finished.

## Per-node gates

In this order, per node:

1. The node's discipline: the file in `disciplines/` its row names. A node with none is incomplete unless read-only.
2. The repo's own gates from its CLAUDE.md; a UI change is driven with playwright and the console is clean (`checklists/ui-verify.md`). The bugfix test rule is `disciplines/tdd.md`.
3. `checklists/build.md` killer items against the node's own diff, quoting the numbers.
4. **Pre-check gate.** `run-digest` runs lint, types and the targeted tests in the node's worktree, once, before its done-check. A failure goes back to the builder, for two fix attempts, then stop and show the error. A failure that already exists at the node's parent stops the work tab and asks the lead; no done-check starts until the owner answers. It starts on a green result. The node's focused proof runs through `run-digest` or `claim-prover` in the node's worktree.
5. **Done check**, last before the node counts as done, in place of a node review (the one review is the `self` review of the whole build). Git computes the Owns diff (`git diff <parent> -- <owns>`); `done-check`, an agent or inline, checks the node's acceptance and the plan's `Decided:` and `Not-building:` lines against it, quoting the line for each deviation. The report carries `Done-check: pass` or `Done-check: deviation <sha>`, the sha being the commit checked; a job with no diff (an ops job) carries `Done-check: n/a (no diff)`. `done-check` reruns after any commit that follows the check. A deviation goes to the lead as a question.

The main thread holds the table, the graph and the findings.

## Author duties

Reuse before writing: this codebase, then stdlib, then an installed dependency. One logical change, self-review the diff, the commit convention and proving the Done-when are in `checklists/build.md`. Check the repo's decision records before writing code (`checklists/design.md` §5), check a UI change against its linked frame and raise a state the frame omits (§18), and follow the threat model for security items (§8). Every review thread gets a fix or an answer.

## Prove it against something real

`test-gap-auditor` on the whole change, before the final review, closes gaps through `builder`; then `claim-prover` on each stated behaviour, and `ui-verifier` for a changed UI flow (`checklists/ui-verify.md`). None of them delegates; their definitions withhold every dispatch tool.

`claim-prover` runs the real thing wherever one is reachable:

| Change touches | Run it against |
|---|---|
| Logic with no service dependency | the repo's own suite, in the worktree |
| One service and its deps | that service with its dependencies running locally |
| Two or more services, a contract, a schema | the full local stack, end to end |
| Something already merged | the deployed environment |

Reasoning about a response shape is not verification, and "the tests would confirm" has confirmed nothing. Where no environment is reachable, say so in those words. Name what already ran in the dispatch prompt and ask for a spot-check or a targeted reproduction of specific claims. **A test result that contradicts the expectation means the code is the suspect, not the test:** investigate before touching the test.

## Output

The node table with start times, actual cost and done-check per node; the nodes run in parallel against the plan's maximum; anything left open with a position on each; then the hand-off to the `self` review. Report shape: `engines/common.md`.
