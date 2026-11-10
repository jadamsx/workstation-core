# Build engine

Executes an approved plan's node graph in worktrees, wave by wave. Plan vocabulary (node, wave, owns, intensity, discipline): `engines/plan.md`. Review depth, rounds and caps: `engines/review.md` "Intensity". Gates, git safety, delegation, report and refusals: `engines/common.md`. Push, change and CI: `engines/ship.md`. Author checklist: `checklists/build.md`.

## Params

| Param | Values | Effect |
|---|---|---|
| `scope` | `node`, `wave`, `plan` | what to build. Default: the next unbuilt wave, and say which |

## Input

The plan is the spec; each form below still ends at an approved plan.

| Input | Route |
|---|---|
| A plan note, or a ticket key whose design note in `${NOTES_DIR:-~/notes}/projects/<slug>/designs/` has `status: approved` | build it |
| An epic design piece (a row of the epic's design note, or the epic design from this session) | plan a story for that piece, then build |
| A plan worked out in this session | write it as the design note and wait for the go |
| A ticket key with no plan, or a bare description | plan it first |

Never ask for a ticket, or for the input in a particular shape, when one of these is in front of you. A named node or piece is what gets built. Where the plan names an epic piece, that piece's "Done when" is its acceptance and every node traces to it. A ticket key anywhere in the plan settles branch naming and the change title; with none the work stays local and uncommitted, and the `self` review skips the change, the push and the CI loop.

## Steps

1. **Gate.** Done when the design note says `status: approved`, and its node table has agent, discipline, owns, wave, intensity, review and acceptance per node. For a `format: v2` note `notes-lint <note>` must report none of `fr-missing`, `fr-uncovered`, `covers-empty`, `covers-unknown`, `covers-column`, `trace-missing`, `trace-column`; refuse while any FR has no covering node or any node has no `covers`, and name the rows. A keyless quick plan has no note: the owner's go in this session and its table in chat are the gate. Otherwise stop and name the plan step to run. Never write a Progress list for an unapproved plan. A request that adds scope beyond the table goes back to plan as a decision node.
2. **Worktrees** (below). Move the ticket to in progress when there is a key and the tracker has the step (`engines/ship.md` Tracker). Done when every repo the plan touches has its worktree at fresh `origin/<base>` and no node runs in the owner's checkout.
3. **Build the waves** (below), after reading the plan's area index in the notes via `code-locator` notes mode. Done when every node's diff is reviewed at its node's `intensity`, whatever its size, and its own acceptance passes.
4. **Whole-repo gates, once**: a `verify-run` node, `run-digest`. Done when formatter, linter, typecheck, `pre-commit` and the suite ran once on the whole tree, before completion is claimed.
5. **Prove it** (below). Done when coverage gaps are closed and each stated behaviour ran against the real thing, or "no environment reachable" is said in those words.
6. **Hand over** to the `self` review. Done when the node report shows what each node cost and what its review found.

A false premise found mid-build, or work outside the plan, stops the run and goes back to plan as a decision node. A Blocker that survives its node's fix-round cap stops the whole run: report what is stuck and do not route around it. A blocked pre-push gate belongs to the `self` review (two fix-and-retry rounds, then stop and show the error).

## Worktrees

`EnterWorktree` for every repo the plan touches, local-only work included, after `git fetch origin` in that repo. Base is the repo's default branch (`git symbolic-ref refs/remotes/origin/HEAD`; never assume `main`). Location `<repo>/.claude/worktrees/<key>`, key = the ticket key, or `local-<plan-slug>` with none. Branch `<KEY>/<short-description>`; with no key `local/<plan-slug>`, never pushed. One ticket, one tree per repo: isolation is not permission to start a second ticket.

Every node agent works inside the tree it was given (the ticket worktree or its node worktree) and nowhere else. None runs `git checkout` in the owner's checkout and none pushes; the push is in the `self` review, from the main thread, through the gate.

## Waves

Walk the graph wave by wave. The next wave starts only when this one has closed. Parallelism comes from `owns` (`engines/plan.md` "Node vocabulary"): a node whose `owns` overlaps another's waits, or hands a patch to the integration owner the plan names. Lockfiles, generated files and shared config sit in exactly one node's `owns`. A node that needs a file outside its `owns` reports and stops.

A wave of one node works directly in the ticket worktree. A wave of two or more gives each node its own worktree branched from the ticket branch (Agent `isolation: "worktree"`, or `git worktree add` under `.claude/worktrees/<ticket>-<node>`), dispatched in one message, so a node's review and proof see only its own change. Reuse the shared caches so per-node setup stays cheap.

Node progress goes into the plan note as a one-line edit: `[~]` when the node starts and `[x]` when its review passes, in the same edit adding its Decisions and Traps lines, so a compaction loses nothing. Only current-wave nodes are `[~]`; a later-wave node stays `[ ]` until every earlier wave is `[x]`, and if work runs ahead, update the table's waves instead. A v2 node's own tests are named in its Traceability row's Test cell as it passes.

Wave close:
- Each node's review runs on `git diff -- <its owns>` in its worktree. If one node fails review while siblings run, the siblings finish and the failed node gets its fix rounds.
- After the wave settles, the main thread dispatches `run-digest` or `claim-prover` per node for its focused proof, in that node's worktree.
- When every node has passed, merge the node branches into the ticket branch in node order. A conflict means the plan's `owns` were wrong: stop and treat it as a planning error. Then remove the node worktrees and run the wave review on the combined diff, where "Intensity" calls for one.
- Append the decisions made during the wave to the note's Decisions, one dated line each; skip when none. This is the wave-end sweep only.
- A Blocker that survives the fix-round cap stops the run (Steps).

Discovered work that is not this ticket becomes a ticket draft under the note's `## Out`, never scope; the `self` review sends it with the rest at the end. Anything the build adds, drops or does differently from the plan is a decision node in the table before building.

## Node prompts

Each prompt gives the node spec (acceptance, `owns`, discipline, checklists) and the worktree path, and names the repo so the builder applies `checklists/build.md` before reporting done (`checklists/review-core.md` stays the reviewer's list). Each also carries:

- **Worktree safety**: never `git checkout --`, `restore` or `stash` in a worktree with uncommitted changes; mutation checks ("does the test fail if I break X") run on a scratch copy; a file an agent says it rebuilt is re-reviewed and re-proven.
- **For a v2 plan**, the FR ids the node delivers (its `covers` cell) with each FR's text, so the builder proves those lines and nothing else. A node that would add, drop or change an FR is a decision node, edited into Requirements with a dated Decision.
- **What already ran**: the real suite and numbers from the nodes that just finished. An agent told nothing re-runs all of it.

## Per-node gates

Run on every node before moving on:

1. The node's discipline: the file in `disciplines/` its row names, with its rules, proof and stop. A node with none is incomplete unless read-only.
2. The repo's own gates from its CLAUDE.md: a UI change is driven with playwright and the console is clean (`checklists/ui-verify.md`). The bugfix test rule is `disciplines/tdd.md`.
3. `checklists/build.md` killer items against the node's own diff, quoting the numbers.
4. The node review: the finders and rounds the node's `intensity` gives, run per `engines/review.md` "Intensity". Every node's diff is reviewed whatever its size. `clean-code` also runs on any structural node whatever its intensity. A spike node gets `cold-reviewer` on the experiment's diff and finding, one round. The follow-up list goes in the node report and on to the `self` review. Whole-diff rounds happen in the `self` review, not here.

**Node builders run only their focused proof plus lint and types on the files they touched.** The formatter, the project-wide suite and `pre-commit` run once, in the final `verify-run` node; every node running them is the same work N times for one answer.

The control plane stays free: the node's agent reads the files, runs the tests and reports; the main thread holds the table, the graph and the findings. A main thread reading source or running a suite means the run collapsed into one agent and the table is decoration.

## Author duties

The builder, main thread or node agent, before handing anything to review:

- Run `checklists/build.md` on its own diff; a failed item is fixed there, not left for the reviewer. What review catches most is `checklists/review-core.md` §3 to §6, applied first.
- Reuse before writing: this codebase, then stdlib, then an installed dependency.
- One logical change, small enough for one reviewer's domain. Discovered work is a follow-up ticket, not scope.
- Self-review the diff and the description against each other. Commit messages follow the repo's convention, imperative summary.
- Every review thread gets a fix or an answer; none is left unaddressed.
- Check the repo's decision records, if it keeps them, before writing code (`checklists/design.md` §5).
- Prove the piece's "Done when" or acceptance criterion before handoff.
- A UI change is checked against its linked design frame side by side; a state the frame omits is raised as a question, not invented (`checklists/design.md` §18).
- Security items follow the threat model (`checklists/design.md` §8, `checklists/review-core.md`).

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

The node table with actual cost and review findings per node, anything left open with a position on each, then the hand-off to the `self` review. Report shape: `engines/common.md`.
