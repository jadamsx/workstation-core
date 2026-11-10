# Plan engine

Concepts for planning: sizing, the plan note, the node vocabulary, the five answers, epic mode. Gates, git safety, delegation, report and refusals: `engines/common.md`. Review of the plan (reviewers, rounds, caps, severity words): `engines/review.md` plan mode. Prose: `engines/write.md`. Tracker and source control host reads: `engines/ship.md`.

## Params

| Param | Values | Effect |
|---|---|---|
| `kind` | `task`, `bug`, `spike`, `story`, `epic`, `fix` | spec depth and extra steps below; never review depth; `fix` takes verified review comments as input and plans a quick node table, one node per fix or logical group |
| `intensity` | `light`, `medium`, `intense` | review depth of the plan and the default for its nodes; default `medium`; see Intensity |

`kind` sizes the planning. `intensity` is separate and defaults to `medium` for every kind.

## Steps

1. Size (below). Say it in one line. Done when quick or full is stated.
2. Interview when the input is vague (below). Done when task, acceptance, guardrails and extra info are answered or recorded as `none stated`.
3. Vault lookup (below). Done when the `vault` field names the notes used or says `nothing relevant`.
4. Verdict: the five answers run (below). `don't` or `already exists` ends the run here: no plan, no branch, no code. Report and stop. Done when each answer carries a `file:line`, `N/A` plus why, or `unknown` (which blocks).
5. Read and locate: the ticket and its comments, the notes, the code, every caller of anything exported. Epic: epic mode. Done when every file and caller the change touches is listed.
6. Node graph: the table in "Node vocabulary". Quick plans still write it. Done when each node has an acceptance sentence and a discipline, every acceptance criterion has a verification node, and a quick plan still has its table.
7. Review the plan: `engines/review.md` plan mode, with this plan's size and kind. Done when a round returns no findings or the cap is hit.
8. Plan note: write it (below). Status `proposed`. Done when the note passes `notes-lint`, carries the plan fields the work touches, and the owner has the table.
9. Approve: after the owner says go and not before, set `status: approved`, `date:`, and write the Progress checklist. Record the nodes with `node-index` (below). Done when the frontmatter reads `status: approved` with `date:` set; a keyless quick plan has no note, so the go in the session is the approval.

Per kind, what step 5 and 6 must also show:
- `bug`: the reproduce node comes first and a command shows the failure; the fix point is the shared function every caller routes through; acceptance names the test that fails now and passes after.
- `spike`: the decision it informs and who makes it, the box (hours or attempts), the cheapest experiment that can say no, and the next step if yes. A spike that informs no decision does not run.
- `story`: description, comments, parent epic and links read; every acceptance criterion has a verification node.
- `epic`: epic mode "Done when" lines below.
- `fix`: every open human thread has exactly one outcome (fix, follow-up or decline) and every fix thread is covered by a node with an acceptance sentence; the table shows thread, author, outcome and drafted reply, and nothing is built or posted before the owner's go.

Ends on the go. Ends early on `don't`, `already exists`, a false premise, or (quick) a second file or interface appearing: re-size to full and say so. A spike also ends when its box runs out or one attempt answers the question.

## Sizing

Triage first, silently, with minimal recon: enough to know which repo the work lands in. Do not read the code to form an opinion yet.

| Signal | Size |
|---|---|
| One file, one obvious command to verify, no interface change | quick |
| Anything else: several files, a new interface, config or infra, ambiguity, or the owner asked to be interviewed | full |

Offer `full` as an escape hatch only when quick was chosen. A spike is quick unless it needs another repo or a running stack. An epic is always full.

## Intensity

Review depth is the scale in `engines/review.md` "Intensity" (`light | medium | intense`), default `medium` for every `kind`. The owner overrides by saying the level in the request; an override is recorded as given and never second-guessed. Each node row carries its own `intensity` (below).

## Interview first

When the input is vague (no checkable acceptance, no repo, no scope), ask before planning. One question per message, then stop and wait: Task (what changes and where), Acceptance (the command, test or observable result for each criterion), Guardrails (what must not change), Extra info (tickets, links, prior attempts).

Never draft, guess or offer candidate answers. Challenge a vague answer once, then accept it. A skipped section renders as `none stated`. A ticket key or URL is recorded verbatim.

## Vault lookup

Resolve the project with `current-project` and read `projects/<slug>/index.md` first. Then search `${NOTES_DIR:-~/notes}` for the ticket key, each service or repo touched and the decision records in play: `grepai search` from the vault first, then `rg`. Read the matching lines of `index.md` before opening notes. A note marked stale or last verified over 60 days ago is a lead, not a fact; check it against the code. The plan cites each note used by path in its `vault` header field, or says `vault: nothing relevant`.

## The five answers run

The questions are `checklists/design.md` §0. `premise-attacker` takes the ticket and nothing else; the main thread then answers all five, each with a `file:line`, `N/A` plus why, or `unknown` (which blocks). When the owner has already decided the what, the brief passes it as a `Decided:` item: "attack how, never whether". Every finding and every investigation result is sorted per `engines/review.md` "Resolve findings" before use.

## Plan note

The plan is one vault note per ticket: `${NOTES_DIR:-~/notes}/projects/<slug>/designs/<KEY>-<slug>.md` (top-level `designs/` when there is no project), linked from `projects/<slug>/index.md`. Copy `templates/design.md` (frontmatter `format: v2`), fill its sections in order, and write it to the vault as a refactor, never an append. The verdict, approach and diagrams go in Design; the old Why is Alternatives considered; the old Acceptance is Requirements plus Traceability. Review rounds, handoffs and rendered images stay in `${DRAFTS_DIR:-~/drafts}/projects/<slug>/<key-or-slug>/`, linked from the note by path.

- Status is the note's frontmatter `status`, never a body line. New is `proposed`. Building refuses a note that is not `approved`. A change of approach after approval goes back to `proposed`. The `self` review sets `shipped`; a replaced design is `superseded` and linked both ways.
- `## Progress` is one `- [ ] N1 <title>` line per node, then `- [ ] review`, `- [ ] change`, `- [ ] CI green`.
- Each `## Decisions` entry records the question asked and why, not just the outcome. A standing instruction from the owner ("never do X") goes in as a bullet starting `Standing:` the moment it is said; every scope decision as `Decided:` the same way. `notes-lint` requires the template's fixed headings, so no new section.
- A quick plan with no ticket key is not written down: the owner's go in the session is the approval and the build takes the table from the chat.
- The project hub: when `projects/<slug>/index.md` still holds the template placeholders, fill "What this stream is" and "Current state" first, from the ticket and the vault lookup.
- A proposal for a yes from people who will not build it uses `templates/proposal.md` (`format: proposal`, 3 pages at most) and links the design note.
- Before asking for the go, `notes-lint <note>` passes.

### Plan header

One field per line. Empty means the check that reads it is skipped (`engines/review.md` "Post-completion checks").

| Field | Holds | Drives |
|---|---|---|
| size, repos, plan kind | as stated | routing |
| `vault` | paths of the notes used, or `nothing relevant` | the lookup is on record |
| `risk_flows` | named end-to-end flows, each with start state and expected end state | flows, edge cases |
| `roles` | roles and the actions each may and may not do | `role-tester` |
| `hot_path` | endpoint or flow, target p95, error budget, expected load | `perf-tester` thresholds |
| `migrations` | yes or no, reversible yes or no, expected row scale | `migration-verifier`, rollback check |
| `frames` | design frame URLs with node ids, and which are shared platform components | frame diff, a11y states |
| `flags` | flag names and defaults | on/off test, rollback |
| `signals` | metrics, alerts and events the change must emit | `ops-readiness-auditor` |
| `deps_added` | filled by the builder, never the planner | dependency and licence scan |

### Spec and coverage

Two halves, one note. Section length follows importance; a known mess gets a few lines.

| Part | Sections | Written by |
|---|---|---|
| Team review | Context and scope, Goals and non-goals, Design, Alternatives considered, Cross-cutting concerns | epic and story in full; task and bug may drop them (minimal v2) |
| Spec | User Scenarios & Testing (prioritised stories, Given/When/Then), Requirements (`FR-001: System MUST ...`), Success Criteria (`SC-001`) | epic and story in full; task and bug need Requirements only; a spike has one FR for the finding it must produce |
| Build | Plan header, Node table with `covers`, Progress, Traceability, Decisions, Traps, Out, Links | every plan |

- Requirements come from the ticket's acceptance criteria: one FR per criterion, behaviour a tester drives also as a Given/When/Then scenario. A bug's FR-001 is the symptom no longer occurring, plus the unchanged behaviour. An unanswered question stays `[NEEDS CLARIFICATION: ...]`; none may remain at approval.
- The node table has the seven columns plus `covers`. Every FR is covered by at least one node and every node covers at least one FR; a verification node lists the FRs it proves.
- Traceability: one row per FR and per SC (Req, Nodes, Test, Status `open`), filled from real test runs at the `self` review. An SC with a number (latency, load, error rate, a11y) also sets the plan field whose agent proves it (`hot_path` for perf, `frames` for a11y) and its row names that agent.
- Design lens, while drafting Design and Cross-cutting concerns: run the approach past SOLID, DRY, KISS, YAGNI, ports and adapters, 12-factor, testability, observability, idempotency and versioning. Write up only the ones that change the design or name a real risk; never list them as a checklist or fill one with N/A. YAGNI and KISS win ties: no adapter or abstraction a current caller does not need.
- Design shape: the plan shows its blast radius with the three lines from `engines/write.md` when it moves a boundary.

## Node vocabulary

A plan is a graph of nodes. A Mermaid graph is drawn when the work crosses more than two repos, changes a database schema, or breaks an external API contract. Under that bar there is no graph, but the table is still written, even for a quick plan: the build accepts nothing else. Per node:

| Column | Holds |
|---|---|
| **agent** | `code-locator`, `caller-mapper` or another digest agent for mechanical location and bulk reads. `builder` for edits (scope `one-file` for 1 to 2 files, `node` across more). `user` for a `decision` node. self only where judgement cannot be written into a prompt; "faster if I just do it" is not that reason |
| **discipline** | the file in `disciplines/` the node works under (table below); `none` for read-only nodes (`code-locator`, `claim-prover`). A node with neither is incomplete |
| **owns** | files and directories the node writes, including lockfiles, generated files and shared config it changes; each of those sits in exactly one node. Empty for read-only nodes |
| **wave** | dependency depth. Wave *k* holds nodes whose deps all sit below *k* |
| **intensity** | `light`, `medium` or `intense`, default `medium`: how hard the node is reviewed (`engines/review.md` "Intensity"). Raise to `intense` for auth, migrations, money and public contracts; lower to `light` for docs or config-only nodes |
| **review** | every node, at its boundary: `cold-reviewer`, plus `clean-code` when structural (new function, moved or duplicated code, interface change). No exceptions, renames and quick plans included |
| **acceptance** | one sentence saying how we know it is done |

The plan names, per node, what it must prove (`checklists/design.md` §15); `test-gap-auditor` checks each change proves it.

- **Parallelism is computed from `owns`, never by eye.** Two nodes are disjoint when no path in one equals or is a prefix of a path in the other; a directory overlaps every file under it. Overlapping nodes serialise, or one is named integration owner for that file and the others hand it a patch.
- **Titles name the work, not the file.** `update callers to consume session`, not `update handler.ts to consume .token`. Filenames belong in `owns`; a title carrying one makes the node's signature unique forever, so repeated work is never spotted.
- A node whose acceptance needs more than one sentence is too big: split it. A node that cannot fail is not a node: fold it into its neighbour.
- Draw the boundary where a reviewer could reject one node and keep its neighbour; fold setup, config and docs into the node whose deliverable needs them. Review runs at node boundaries, not after every edit.
- Every acceptance criterion in the ticket is covered by at least one verification node; if not, the graph is incomplete, not the ticket.
- A node that changes an exported symbol is followed by a `migrate-callsites` node, sourced from `lsp references`, not memory or grep alone.
- `decision` nodes block their dependents: a question for the owner or anyone else is a node with `actor: user`, drawn in the graph, gating whatever waits on it.
- `kind` comes from a fixed taxonomy: `node-index kinds` prints it. Never invent one, or counts stop being comparable.

Record the nodes once the table is approved. Idempotent per task slug, so a re-run replaces that task's contribution.

```bash
node-index record --task <YYYY-MM-DD>-<slug> --repo <repo> <<'JSON'
[{"kind": "recon", "title": "map auth callsites", "actor": "code-locator"}]
JSON
```

| Node | Discipline |
|---|---|
| Unknown cause, intermittent, performance | `disciplines/investigate-first.md` |
| Bug or small behaviour change | `disciplines/reproduce-first.md` |
| New behaviour with a clear input and output | `disciplines/tdd.md` |
| New behaviour, product slice, integration | `disciplines/acceptance-first.md` |
| Behaviour-preserving restructure | `disciplines/refactor.md` |
| Schema, API, protocol, config, dependency | `disciplines/migration.md` |
| Time-boxed feasibility question | `disciplines/spike.md` (nodes of kind `spike`, one to three, `owns` a scratch branch or copy, nothing merges; the plan writes the box, the cheapest experiment that can say no, and the next step if yes) |
| Validation only, last-mile proof | none: a `claim-prover` node |
| Locate code | none: `code-locator` |

**The table is a contract.** Once the owner says go, every row dispatches to the agent and discipline it names. A row the main thread builds itself is the run failing silently.

### Verification nodes

A branch that fans out gets one node that exists only to check the branch landed together: a `claim-prover` node depending on every node in the branch, proving acceptance without touching product code. Per-node review catches a node; nothing else catches three correct nodes that disagree at the seam. One fan-out, one verification node; a straight line gets none.

### Teams instead of subagents

Escalate from subagents to agent teams (separate sessions, own context, direct messaging, a shared task list) only for competing hypotheses to test in parallel, separate modules with no shared files, or cross-layer ownership. The order is one agent, then subagents, then teams, and each step needs the failure the previous one had. Teams cost more tokens, `/resume` does not restore them and teammates source control hostt to mark tasks complete. Stay on subagents for sequential work and same-file edits.

## Epic mode

The output is a diagram and a table, not a document: an epic design that gets skimmed has failed at its only job.

### Read what was asked for

The epic, every child ticket and **the comments as a separate fetch**: a thread is where scope changes and the body rarely catches up. `change-reader` returns each ticket's description and comments verbatim; the main thread reads that text, not the summary, and says where the two disagree. Then every ticket those link or name, in full with comments: the earlier attempt, the security bug and the rollout gate are where the constraints live. Then every design page and frame group, not only the frames the ticket links; the last frame or a prototype page holds the state nobody mentioned. Then the code: pin worktrees at fresh `origin/<base>`, detached, under `<repo>/.claude/worktrees/<epic-key>` for every repo it touches.

Answer product questions from the epic, its stories and the designs before asking anyone. Only a real gap goes to product.

### Attack the premise

Shape each change against `checklists/design.md`, `checklists/review-core.md`, `review-domain.md` and `design-review-shared.md` so the plan answers what reviewers will ask. `premise-attacker` takes the epic and nothing else, plus every `Decided:` item. It looks for the premise the code contradicts, the sibling repo that already does this, the measurement a constant beats, and inputs built for an output nobody validated. **A false premise at epic level is the most expensive thing in this workflow:** every ticket underneath inherits it and no code review reaches it. If the epic rests on something untrue, stop and say so; do not design around it.

### Nothing here is gospel

Not the epic, the child tickets, product's framing or the platform as it stands. Answer three questions out loud before any diagram:

- **Is the platform the right shape to receive this?** Where a seam does not exist, the options are to build the seam first as its own piece of work, or to hang the feature off something never meant to carry it (how platforms rot, invisible once shipped). Name the seam, say which option the epic takes, and say it in the summary.
- **Should something else be done first?** A missing abstraction three epics work around, a misplaced service boundary, a migration everyone avoids. If it exists, say: *this epic is doable now, and this other thing would make it and the next two smaller.* The owner judges; do not resolve it by proceeding.
- **Does product's reasoning hold?** Which claims about users, frequency and value are measured and which assumed, and what is the cheapest test of the biggest assumption. Building the whole epic to find out is the expensive version.

### Decision records

If the repo keeps decision records, read all of them, not a search: split the directory across several `researcher` agents in one message, each given the design summary and returning one line per record (`NONE`, `AFFECTS` with constraint and quote, or `CONFLICT`). One `researcher` or `code-locator` is enough for a single targeted question. Check every claimed conflict against the record's text yourself; readers misread. Name any deviation.

**A conflict with a decision record stops the design.** Do not resolve it, design around it, or note it and continue. Say which record and which part of the epic, and hand it back. Where the epic needs something no record covers and later work must follow, say so: it is a new architectural decision wearing a feature's clothes and should be written down as one.

### Draw the flow

A `sequenceDiagram` is almost always the shape: an epic is things calling each other over time. Which type, how to draw it and the render check: `engines/write.md` diagram decision. What makes one carry the design:

- `autonumber`, so a ticket can say "step 6".
- Self-calls for work inside a service (`A->>A: enqueue two jobs`); that is where most decisions live.
- Dashed returns (`-->>`) so a reply is visibly a reply.
- `Note over` for what a box cannot say: the threshold, algorithm or rule, two or three lines, numbers included.
- Participants are services or processes, never a sentence.

A second diagram, what owns what, whenever the epic moves a boundary (a new service or store, a responsibility changing hands, a call crossing a new line): a component `flowchart TB` with one subgraph per service, the epic's additions styled. An `erDiagram` replaces it for a pure schema epic. Never more than two diagrams. Render both with `mmdc` and look at the images before anyone else does. A `;` inside a sequence note or message breaks the parse.

### Converge

Rounds, lanes, caps and the stop rule: `engines/review.md` plan mode, epic. What each lane must cover here:

- `design-gap-finder`: product coverage, decision records and platform fit. For every "rendered from X", "mounted in Y" or "called via Z", find the code that produces it at that spot with a `file:line`; find the real dispatch path rather than assuming it. Search the frontend and sibling repos for an existing client before choosing a transport.
- Mechanism audit, once the change plan exists: `premise-attacker` checks the mechanism every planned change relies on (a precondition, event, stream, hook point) against the code and returns change / mechanism / exists-false-unverified.
- `approach-reviewer`: authority, spoofing, races, duplicates, partial-failure exposure.
- `clean-code`: cut what is not `Decided:`.

Every prompt carries every `Decided:` item and states that "no code exists yet" is not a finding. Triage each round yourself into verified, housekeeping, drop and unverified, and show the owner that split, never the raw list. Verify every load-bearing claim before folding it in. A real fork (push vs poll, generic vs single-producer) goes to the owner with the long-term trade-off; never pick the cheaper option to save effort.

### Cut it into tickets

One table; each row is a ticket someone could pick up. If stories already exist, map pieces onto them, grouped by ticket key; only prerequisites no story covers become new tickets, and stale story text gets a short comment, not a rewrite.

| Column | Holds |
|---|---|
| **title** | imperative, names the work not the file |
| **steps** | which numbered diagram steps it implements |
| **repo** | where it lands |
| **depends on** | other rows by title, real dependencies only |
| **acceptance** | one sentence; more than one means two tickets |
| **decision** | a question for a person, with a name against it; blocks its dependents |

A ticket nobody could reject independently of its neighbour is not a ticket. **Validate the output before building its inputs:** if the end deliverable has never been seen to work, the first ticket proves it. Where several tickets feed one deliverable, say which single ticket would be the whole thing at a smaller scale; that is usually the one to do first.

### Report back

Chat, short: the verdict and what it found; **Platform** (the seam, whether it exists, the option taken); **Do first** (or nothing); the diagrams; the table; **For the owner to check**, one line per question the plan could not settle, with who or what would settle it (a decision record that might apply, a product claim assumed not measured, a service whose owner should see this first); the one thing that would make the epic unnecessary, if it exists. Never fold a question into an assumption: at epic scale it surfaces as rework three tickets in.

Create no stories yet: the ticket table stays as drafts in the note, and after approval one Out ask: "create N stories, optional wiki page".

### Where the artifact lives

The epic's plan note holds the diagrams as Mermaid blocks and the ticket table. `seq.mmd`, `owners.mmd` and their PNGs sit in `${DRAFTS_DIR:-~/drafts}/projects/<slug>/<epic-key>/` and the note links them by path. A wiki page only if the team will work from it, and only after the owner says so.

To show the team, publish one private page with the Artifact tool: where things stand today; both diagrams as native `<pre class="mermaid">` blocks with `<` `>` `&` escaped; the design screens as a click-to-enlarge gallery uploaded through `files`; the build table grouped by tracker story, prerequisites first; the decisions and risks carried forward. Keep the HTML as a template in the same folder with `{{SEQ}}` / `{{OWNERS}}` placeholders and republish with `url` to keep the link. The scratchpad is wiped on restart; recover a lost copy with `Artifact read`.

Changes built from the epic carry its two diagrams unchanged in Screenshots: same source, same colours, no per-change recolouring. Render with `mmdc -c ${DRAFTS_DIR:-~/drafts}/projects/<slug>/<epic-key>/artifact-theme.json -b '#f5f7fa'` and put the change's own slice beside them.

## Output

The plan note path, the verdict, the node table, and a "For the owner to check" line for every question the plan could not settle. Then ask for the go.
