# Plan engine

Planning: sizing, interview, the plan note, the node table. Epic mode: `engines/plan-epic.md`. Gates, git safety, delegation, report and refusals: `engines/common.md`. Plan review (reviewers, round shapes, caps, severity words): `engines/review.md` plan mode. Prose: `engines/write.md`. Tracker and source control host reads: `engines/ship.md`. Summary shape: `templates/plan-summary.md`.

## Params

| Param | Values | Effect |
|---|---|---|
| `kind` | `task`, `bug`, `spike`, `story`, `epic`, `fix` | spec depth and extra steps; never review depth; `fix` takes verified review comments and plans one node per fix or logical group |
| `intensity` | `light`, `medium`, `intense` | review depth of the plan and the default for its nodes; default `light`; see Intensity |

## Steps

1. Size (below). Say it in one line. Done when quick or full is stated.
2. Interview (below). Done when scope, done and next are answered or recorded as `none stated`.
3. Lookup (below): the vault and past corrections. Done when `vault` names the notes used or says `nothing relevant`, and each matching feedback file is quoted or `none matched`.
4. Verdict: the five answers (below). `don't` or `already exists` ends the run: no plan, no branch, no code. Done when each answer carries a `file:line`, `N/A` plus why, or `unknown` (which blocks).
5. Read and locate: the ticket and its comments, the notes, the code, every caller of anything exported. Epic: `engines/plan-epic.md`. Done when every file and caller the change touches is listed.
6. Shape and node table (below). Quick plans still write the table. Done when the Shape shows lines removed against added, each node has an acceptance sentence, a discipline and named needs, and every acceptance criterion has a verification node.
7. Review the plan: `engines/review.md` plan mode, at the plan's intensity, with the round shapes in `engines/review.md`. The review also checks every need for a false one. The last round brings yes/no suggestions to the owner; it never rewrites agreed decisions.
8. Plan note: write it (below), status `proposed`. Done when the note passes `notes-lint` and the owner has the summary.
9. Approve: the owner ticks Assumptions (yes/no) and the Not-building list, and says go. Only then set `status: approved` and `date:`, write the Progress checklist, stamp the `Decided:`, `Standing:` and `Not-building:` lines, and record the nodes with `node-index` (below). A keyless quick plan has no note; the go in the session is the approval. After the go, a build runs through `engines/build.md`, quick plans included: never dispatch a builder from the plan run, because the node gates and the review in the table's `review` column live only in the build.

Per kind, beyond what the skill for the kind lists:
- `bug`: acceptance names the test that fails now and passes after.
- `spike`: the box (hours or attempts), the cheapest experiment that can say no, and the next step if yes; a spike that informs no decision does not run.
- `fix`: every open human thread gets exactly one outcome (fix, follow-up or decline); every fix thread is covered by a node with an acceptance sentence; the table shows thread, author, outcome and drafted reply; nothing is built or posted before the owner's go. After the push, post one reply per thread (`checklists/prose.md` §7) via the reply verb in `engines/ship.md`, and resolve only fixed threads.

Ends early on `don't`, `already exists`, a false premise, or (quick) a second file or interface appearing: re-size to full and say so. A spike also ends when its box runs out or one attempt answers the question.

## Sizing

Triage first, silently, with minimal recon: enough to know which repo the work lands in. Do not read the code to form an opinion yet.

| Signal | Size |
|---|---|
| One file, one obvious command to verify, no interface change | quick |
| Anything else: several files, a new interface, config or infra, ambiguity, or the owner asked to be interviewed | full |

Offer `full` as an escape hatch only when quick was chosen. A spike is quick unless it needs another repo or a running stack. An epic is always full.

## Intensity

Review depth is the scale and round shapes in `engines/review.md` "Round shapes". The default is `light` for every `kind` and every node. A node touching auth, input, secrets or permissions is raised to `medium`; migrations, money and public contracts to `intense`; the plan's own level follows its highest node. The owner overrides by saying the level in the request; an override is recorded as given, never second-guessed and not raised by the auth, input, secrets or permissions rule.

## Interview

Open every plan with it, one question per message, then wait. Skip a question the input already answers.

1. Scope: for each scope word in the request, what is in and what is out.
2. Done: the command, test or observable result for each criterion.
3. Next: what comes after this and must not be blocked or pre-empted.

Never draft, guess or offer candidate answers. Challenge a vague answer once, then accept it. A skipped answer renders as `none stated`. A ticket key or URL is recorded verbatim. The answers become Assumptions (each stated so the owner can say yes or no) and the Not-building list.

## Lookup

- Vault: resolve the project with `current-project`, read `projects/<slug>/index.md`, then search `${NOTES_DIR:-~/notes}` for the ticket key, each service or repo touched and the decision records in play (`grepai search` from the vault, then `rg`); read the matching lines of `index.md` before opening notes. A note marked stale or last verified over 60 days ago is a lead, not a fact; check it against the code.
- Past corrections: `run-digest` returns the memory feedback files that match the plan's topic. Quote each match in the plan; the plan obeys it or names the `Decided:` line that overrides it.

## The five answers

The questions are `checklists/design.md` §0. `premise-attacker` takes the ticket and nothing else; the main thread then answers all five. When the owner has already decided the what, the brief passes it as a `Decided:` item: "attack how, never whether". Every finding is sorted per `engines/review.md` "Resolve findings" before use.

## Plan note

One vault note per ticket: `${NOTES_DIR:-~/notes}/projects/<slug>/designs/<KEY>-<slug>.md` (top-level `designs/` when there is no project), linked from `projects/<slug>/index.md`. Copy `templates/design.md` (`format: v2`), fill its sections in order, write it as a refactor, never an append. Review rounds, handoffs and images stay in `${DRAFTS_DIR:-~/drafts}/projects/<slug>/<key-or-slug>/`, linked by path.

- Where the interview goes: Assumptions under Context and scope, the Not-building list under Goals and non-goals, Shape and the verdict in Design, the past-corrections quotes in Decisions. `notes-lint` fixes the headings, so no new section.
- Shape: the design after the change, with the three lines from `engines/write.md` when a boundary moves, and the expected lines removed against added. A plan that only adds says why nothing goes.
- Status is the note's frontmatter `status`. New is `proposed`. Building refuses a note that is not `approved`. A change of approach after approval goes back to `proposed`. The `self` review sets `shipped`; a replaced design is `superseded` and linked both ways.
- `## Progress` is one `- [ ] N1 <title>` line per node, then `- [ ] review`, `- [ ] change`, `- [ ] CI green`.
- Each `## Decisions` entry records the question and why, not just the outcome. A standing instruction from the owner goes in as `Standing:` the moment it is said; every scope decision as `Decided:`.
- The node table is the decision log: a cleared work tab must be able to resume from the note and the table alone, so every row carries what it needs without chat history.
- A quick plan with no ticket key is not written down; the build takes the table from the chat.
- When `projects/<slug>/index.md` still holds the template placeholders, fill "What this stream is" and "Current state" first.
- A proposal for people who will not build it is the design note with `status: proposed`.
- Before asking for the go, `notes-lint <note>` passes.

### Plan header

One field per line. Empty means the check that reads it is skipped (`engines/review.md` "Post-completion checks").

| Field | Holds | Drives |
|---|---|---|
| size, repos, plan kind | as stated | routing |
| `vault` | paths of the notes used, or `nothing relevant` | the lookup is on record |
| `concurrency_cap` | `build_concurrency_cap` from `claude/resource-policy.json` (default 6), copied at planning | how many nodes the build runs at once |
| `risk_flows` | named end-to-end flows, each with start and expected end state | flows, edge cases |
| `roles` | roles and the actions each may and may not do | `role-tester` |
| `hot_path` | endpoint or flow, target p95, error budget, expected load | `perf-tester` |
| `migrations` | yes or no, reversible yes or no, expected row scale | `migration-verifier`, rollback |
| `frames` | design frame URLs with node ids, and which are shared platform components | frame diff, a11y states |
| `flags` | flag names and defaults | on/off test, rollback |
| `signals` | metrics, alerts and events the change must emit | `ops-readiness-auditor` |
| `deps_added` | filled by the builder, never the planner | dependency and licence scan |

### Spec and coverage

| Part | Sections | Written by |
|---|---|---|
| Team review | Context and scope, Goals and non-goals, Design, Alternatives considered, Cross-cutting concerns | epic and story in full; task and bug may drop them |
| Spec | User Scenarios & Testing (Given/When/Then), Requirements (`FR-001: System MUST ...`), Success Criteria (`SC-001`) | epic and story in full; task and bug need Requirements only; a spike has one FR for the finding it must produce |
| Build | Plan header, Node table with `covers`, Progress, Traceability, Decisions, Traps, Out, Links | every plan |

- One FR per ticket acceptance criterion; behaviour a tester drives is also a scenario. A bug's FR-001 is the symptom gone plus the unchanged behaviour. An unanswered question stays `[NEEDS CLARIFICATION: ...]`; none may remain at approval.
- Every FR is covered by at least one node and every node covers at least one FR; a verification node lists the FRs it proves.
- Traceability: one row per FR and SC (Req, Nodes, Test, Status `open`), filled from real runs at the `self` review. An SC with a number also sets the plan field whose agent proves it (`hot_path`, `frames`).
- Design lens: run the approach past SOLID, DRY, KISS, YAGNI, ports and adapters, 12-factor, testability, observability, idempotency and versioning; write up only those that change the design or name a real risk. YAGNI and KISS win ties.

## Node table

A plan is a graph of nodes. A Mermaid graph is drawn when the work crosses more than two repos, changes a schema, or breaks an external contract. The table is always written; the build accepts nothing else. Build it for maximum parallelism. Per node:

| Column | Holds |
|---|---|
| **agent** | a digest agent (`code-locator`, `caller-mapper`) for location and bulk reads; `builder` for edits (scope `one-file` for 1 to 2 files, `node` across more); `user` for a `decision` node. Self only where judgement cannot be written into a prompt; "faster if I just do it" is not that reason |
| **discipline** | the file in `disciplines/` (table below); `none` for read-only nodes; a node with neither agent nor discipline is incomplete |
| **owns** | files and directories the node writes, including lockfiles, generated files and shared config; each sits in exactly one node. Then, in the same cell, `lives:` where the thing the node changes lives and who owns it, and `preflight:` the resources it needs (service, port, credentials, data, server) and whether they are available. A node that cannot answer preflight is not ready to build |
| **wave** | derived, never chosen: 1 plus the highest wave among its needs. Each need is written as `needs N<k>'s <data or file>` |
| **intensity** | `light` by default; see Intensity |
| **review** | `cold-reviewer` at the node boundary, never after every edit, plus `clean-code` when structural (new function, moved or duplicated code, interface change); no exceptions for renames or quick plans. The intensity decides the rounds |
| **acceptance** | one sentence saying how we know it is done |

The plan names what each node must prove (`checklists/design.md` §15); `test-gap-auditor` checks it.

- **A need is real only if a node reads the other's output.** Otherwise stub, draft or run in parallel. A shared owned file is a need. Two nodes are disjoint when no path in one equals or is a prefix of one in the other; overlapping nodes serialise, or one is the integration owner and the others hand it a patch. The plan review checks every need and removes the false ones.
- **No wave barriers.** The wave is the commit grouping; the build starts a node as soon as its needs are done, each in its own worktree and agent, up to `concurrency_cap`.
- Titles name the work, not the file; filenames belong in `owns`.
- A node whose acceptance needs more than one sentence is too big: split it. A node that cannot fail is not a node: fold it into its neighbour. Draw the boundary where a reviewer could reject one node and keep its neighbour; fold setup, config and docs into the node whose deliverable needs them.
- Every acceptance criterion is covered by a verification node; if not, the graph is incomplete.
- A node that changes an exported symbol is followed by a `migrate-callsites` node sourced from `lsp references`.
- A question for the owner or anyone else is a node with `actor: user`, gating whatever waits on it.
- A branch that fans out gets one `claim-prover` node depending on every node in it, proving acceptance without touching product code. A straight line gets none.
- `kind` comes from `node-index kinds`; never invent one.

**The table is a contract.** Once the owner says go, every row dispatches to the agent and discipline it names. A row the main thread builds itself is the run failing silently.

Record the nodes once approved; idempotent per task slug.

```bash
node-index record --task <YYYY-MM-DD>-<slug> --repo <repo> <<'JSON'
[{"kind": "recon", "title": "map auth callsites", "actor": "code-locator"}]
JSON
```

| Node | Discipline |
|---|---|
| Unknown cause, intermittent, performance | `disciplines/investigate-first.md` |
| New behaviour with a clear input and output, or a bug or small behaviour change | `disciplines/tdd.md` |
| New behaviour, product slice, integration | `disciplines/acceptance-first.md` |
| Behaviour-preserving restructure | `disciplines/refactor.md` |
| Schema, API, protocol, config, dependency | `disciplines/migration.md` |
| Time-boxed feasibility question | `disciplines/spike.md` (one to three `spike` nodes owning a scratch branch or copy; the plan writes the box, the cheapest experiment that can say no, and the next step if yes) |
| Validation only, last-mile proof | none: a `claim-prover` node |
| Locate code | none: `code-locator` |

Hand a build to the standing `work` tab (`engines/common.md` "Delegation"); an extra manager session is for a parallel stream such as a second app. A single node or a short plan needs no manager.

## Output

Fill `templates/plan-summary.md`: the plan note path, the verdict, Shape, the two lists, the Assumptions to confirm, the node table, and a "For the owner to check" line for every question the plan could not settle. Then ask for the go.
