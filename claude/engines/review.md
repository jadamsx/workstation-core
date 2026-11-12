# Review engine

Review from the code, not from the diff text. Verify every finding twice, once yourself and once by an agent that did not write it. Post only what survives. Git safety, gates, delegation, model, report skeleton and agent refusals: `engines/common.md`. Every source control call: `engines/ship.md`. Checklists hold the items: `checklists/review-core.md`, `review-domain.md`, `design-review-shared.md`, `design.md` for plan mode, `ui-verify.md` for UI, plus any domain checklist the team registers.

The failure this engine prevents: a plausible finding, posted, that the code does not support. A wrong comment costs the author more than a missed one. The failure that costs more and hides better: a claim in the ticket or description that nobody checked because it read like background.

## Params

| Param | Values | Effect |
|---|---|---|
| `mode` | `self`, `change`, `epic`, `comments`, `plan` | the table below |
| `intensity` | `light`, `medium`, `intense` (default `medium`); `recheck` is a flag on `change`, not a level | finders, refute and rounds, "Intensity" |
| `target` | branch, change URL, epic key, list of URLs, pasted comments, ticket or doc | the subject |

## Modes

| Mode | Subject | Checkout | Findings go to |
|---|---|---|---|
| `self` | your own branch | the branch or worktree you built in; diff `git diff origin/HEAD...HEAD` plus uncommitted; skip the pin and the size check | fixed in the code, every severity in round 1, re-reviewed; posts nothing |
| `change` | someone else's change | "Pin a real checkout", detached worktrees | drafts, cut, shown to the owner, posted only after their OK |
| `epic` | each change of an epic | as `change`, once per change | as `change`, then the cross-change pass |
| `comments` | other people's review comments | pinned as `change` | chat only; runs only refute and confirm |
| `plan` | a ticket, epic or written plan, before anyone builds | the code the plan describes, off `origin/<base>` | a local draft; never edits the thing reviewed |

### Mode `self`

Tick the design note's Progress lines (one-line edits, `engines/write.md` note register) as each step passes: review after step 1, change opened after step 4, CI green when the loop reports green. Without a ticket the run stops after the report: no description, no push, no CI loop.

0. v2 traceability, only for a design note with `format: v2`. Fill each Traceability row's Status (`pass`, `fail`, `open`) from real runs of the tests in its Test cell, via `run-digest`. A success-criterion row takes the named agent's real result (measured p95 against target); an agent that reported `skipped` leaves the row `open` with the reason. Flag every FR without a passing test, every test with no FR, and every node whose diff touched paths outside its `owns`. Each flag is a finding for step 1. Done when no FR is `open` or `fail` and no node breached `owns`, or the gap is fixed or listed in the report.
1. Read the relevant area index first (`code-locator` notes mode). Final pass over the whole diff, not just the last node: node reviews saw nodes, this sees the change. Rounds per "Intensity". Then the merge-time rows of "Post-completion checks" for each plan field that is set; stop at the first failure that invalidates the later ones, fix, re-run; an empty field is skipped and the report says which.
2. Project gates through `run-digest`: tests, lint, typecheck, pre-commit pass after the last change.
3. Cut comments: `comment-cutter` over the branch diff, before anything is written up. Done when no ticket reference, decision-record number, attribution or restating comment remains in the diff.
4. Out: write the change description (`engines/write.md`, target `change`; UI screenshots by `ui-verifier`), then open it and run the CI loop (`engines/ship.md`). Any ticket drafts from the design note's `## Out` are one Out list, asked once: send all, pick, or skip. The ticket move to review needs no OK (`engines/ship.md` Tracker).
5. Record: update the design note (`status: shipped`, the change link, Decisions brought up to what was built, Traps filled; the same traps into the area note if one exists), the project index "Current state" with the change link, and for an outage or ops fix an incident note or runbook line. Done when every Progress line is `[x]`; an open line blocks the report. A keyless quick plan has no note, so no step.
6. Report. Done when it is given; for a v2 note it states each FR's Status and any `owns` breach.

Any source change after the final pass goes back through this mode before the push: a fix round, a performance round, a follow-up the owner asked for. A reviewer briefed on "correctness only" is not a substitute. Before it ends: tests, lint, typecheck and pre-commit re-run by `run-digest`; a bugfix test follows `disciplines/tdd.md`; a UI change is driven, screenshotted, console clean (`checklists/ui-verify.md`).

### Mode `change`

Optional state across chats: a review note at `${NOTES_DIR:-~/notes}/projects/reviews/<repo>-<number>.md`, one per change in a batch. Frontmatter `url`, `title`, `author`, `reviewed_sha` (empty until a review finishes), `verdict`, `state` (`reviewing`, `open`, `done`). After posting, write `reviewed_sha` and `verdict`, and under `## Threads` one line per posted thread (id, `path:line`, resolved or not).

Steps (`intense`): read the area index, run the claims ledger, pin, size check, read, approach pass, hunt and triage, merge-time checks, cut the drafts with `comprehension-cutter` (given drafts and ticket only; done when every comment's first sentence says what breaks in the author's words), anchor, show the owner the three lines and the drafts, post on their go, report.

`medium` (default): `cold-reviewer` with `description.md`, then `finding-refuter` on its findings; rounds per "Intensity". `light`: one finder, no refuter. Both skip: the area index, the ledger, `clean-code`, `test-gap-auditor`, `miss-hunter`, the approach pass, merge-time checks, `comprehension-cutter` (the main thread applies "Comprehension test" and "Comment style" itself). Read the cited code yourself for anything Blocker or Refuse. A control missing from this repo is not proof it is absent: check the caller, gateway or shared library before keeping "no auth", "no validation" or "no limit". From anchoring on, unchanged. `intense` costs roughly 50 to 100 times more than `medium`: use it when the owner asks, or offer it in one line when the diff touches auth, a migration, money or a public contract.

`recheck`, for a change whose note has a `reviewed_sha` (without one it is a normal review):
1. Same head as `reviewed_sha`: say so and report thread state only.
2. Pin the new head; `diff.patch` is `reviewed_sha..head`; one hunt round; findings files are `<agent>-recheck.md`.
3. List your threads from the note with resolved state. A `finding-refuter` in fix-check mode rules each open thread of yours `FIXED`, `NOT FIXED` or `PARTIAL` with a `file:line`. Done when every open thread of yours has a ruling. The ruling is the proposal: resolve (fixed, wrong, or in a follow-up), edit my note (not fixed and mine is last), reply to <author> (only when someone wrote after my last note), or leave. Never reply under your own last note, never bulk-resolve.
4. Show proposals and new drafts; post after the owner's OK. Write the note: new `reviewed_sha`, `verdict`, new thread ids, one `## Recheck log` line.

### Mode `epic`

1. Read the project index and the area index. `change-reader` for the epic and children (text verbatim, read by the main thread) and per-change status. Done when every change has head SHA, pipeline, open threads, and dependent chains are marked.
2. Each change through that sequence in parallel, nothing posted, own scratch dir each. Print the cost line first when the fan-out exceeds 10 agents. One `finding-refuter` over all changes' findings. Done when every change has confirmed findings and a ledger.
3. Cross-change pass, briefed from `${DRAFTS_DIR:-~/drafts}/projects/<slug>/<epic-key>/brief.md`: `approach-reviewer` (seams, merge order, shared contracts and schemas), `design-gap-finder` (epic coverage against the plan and every child ticket's acceptance), `caller-mapper` (consumers of each shared symbol, off the remote base branch), `claim-prover` (a contract run across the stack where reachable). Done when each seam says which change owns it, what order is safe, and whether anything is inert until another change lands.
4. Per-change drafts via `comprehension-cutter`; epic-level findings listed apart with their owner. Done when each change has its cut drafts and the epic-level findings are listed with an owner.
5. Show the owner the three lines, the drafts and the epic table; post per change by the `change` rules after their go. Done when the owner has the table and has decided what to post.
6. Post-completion, only after every change has merged (before that, skip and say so): the epic column of "Post-completion checks", plan fields from the epic's design note. Y rows always run, P rows when the field is set and did not already run in a story's self review, `perf-tester` last. Stop at the first failure that invalidates the later ones. Local stack on merged main only. Done when each check has a line: run with result, or skipped because its field is empty.

After the report: update the project index "Current state" with the outcome and merge order; add seams and traps to the epic design note (`status: shipped` once all merged); incidents to the incident notes. Rounds and screenshots stay in the scratch dir, linked by path. The epic stops early when a change is too big ("split first") or the seam pass finds a child ticket's acceptance uncovered: say so before per-change detail.

### Mode `comments`

A reviewer's comment is a claim about the code, checked like a finding. It hunts nothing new.
1. Collect (done when every comment has its file, line and author): the comments (pasted, or the change's unresolved threads with file, line, author), the pinned head, the description, the full ticket and every linked design doc. Some comments are answered by the plan already. `change-reader` for threads and ticket.
2. Refute: `finding-refuter` gets the comments as drafts in `comments.md` of the scratch dir, with `brief.md` and `diff.patch` and no opinion of yours. CONFIRMED, REFUTED or PARTIAL with the shortest decisive quote.
3. Confirm every verdict in the code yourself, not from the agent's quote. `claim-prover` runs any behaviour that needs a run; label each verdict run, read or judgement.
4. Report in chat. Per comment: valid, not valid or partly valid with `file:line`; severity and whether the reviewer's own label matches; fixed, covered by the plan, or new work; an outcome (fix with the commit, follow-up with the ticket, or decline with a one-line reason) and a drafted reply, nits included. No outcome means not done: done when every comment has a verdict, an outcome and a drafted reply. Then what must change before merge, what is follow-up, what to leave.

Drafted replies follow `checklists/prose.md` §7. The owner sees the three lines before any reply is posted. Nothing is changed, replied to or resolved unprompted; on request, resolve only fixed threads, one at a time, and say which.

### Mode `plan`

Judges whether work should be built at all and whether the plan survives contact with the code, before work starts. Output is a draft for a human to send, never an edit to anyone's ticket.

- Never modify a ticket, epic or doc under review: no status change, comment, edit or new ticket. Findings are a conversation with the author, written so a person who agrees can paste them.
- Separate what you verified from what you reasoned about. A design review that overclaims gets ignored faster than a code review that does. No strengths section.

How it runs. A single ticket runs steps 1, 2 and 5; an epic or a set runs every step.
1. The five answers (`checklists/design.md` §0), answered by the main thread in full before anything else. Each has a `file:line`, `N/A` with reason, or `unknown`; `unknown` blocks. The owner overrules the verdict, nothing else. Done when each answer has a `file:line`, `N/A` with reason, or `unknown`.
2. Attack: `premise-attacker` owns §0 (should it exist), §2, §3, §16 and §17's "validated before the inputs that feed it get built". Fresh, given the ticket and nothing else: not your answers, the plan or why anyone wants it. Its job is the reason not to build: a premise the code contradicts, a sibling repo that already does it, the trivial input that beats the metric, a result the environment gives anyway, an ordering that builds this before the thing that validates it. It returns `file:line` findings or `no findings` (done when it does). Where it disagrees with your answers, the report gives both, marked.
3. Approach: `approach-reviewer` owns §1, 4, 5, the shared concerns (§6-12), 13, 14, 15, the rest of §17 and 18. Gaps: `design-gap-finder`, dispatched independently, looks across every section for what the set misses. Different territory, neither sees the other's findings; tell them not to pad. Done when both report.
4. Verify every finding against the code yourself (`code-locator` notes mode first, `caller-mapper` to trace). A finding without a file and line is dropped. Check neighbouring repos: work is often done elsewhere. Agents are confidently wrong too. Done when every finding carries a file and line or is dropped.
5. Report as a local draft, shorter than the plan it reviews: the call (build, build a reduced version, or don't; decisive); wrong premises first; per-ticket rollup (sound, rework, wrong premise, merge, drop) and the decision each informs, where a ticket informing no decision is the one to cut; what is missing; sequencing and collisions; the dissenting case at full strength. Done when the report is shorter than the plan it reviews.

Lenses, each owned by a checklist section: engineering §2, 4, 13, 14 (name the simpler alternative concretely, or say it is sound); measurement §16 for any score, metric, benchmark or gate; product §1 and 17; consequence §9. A Mermaid graph only when the work touches more than two repos, alters a schema or changes an external contract (`engines/write.md` "Diagram decision"). Shipped to consumers (a lint rule, shared config): name them, say pinned or unpinned; unpinned gets a count per consumer measured off the base branch on the remote.

Reviewers and rounds per "Intensity" (finders by mode: `plan` row), until `CONVERGED`. Every round uses fresh agents given the ticket and the plan note plus every `Decided:` item, with the instruction "attack how, never whether", and the statement that "no code exists yet" is not a finding. Plan size (`kind`) does not change them; domain checklists the team adds join at `intense`.

- A round that returns no findings ends the loop. At the cap, the open findings go to the owner with a position on each.
- Lanes in an `intense` plan round (an epic plan is not `intense` unless set), one message, different territory: `design-gap-finder` (product coverage, decision records, platform fit), `premise-attacker` (the mechanism every planned change relies on, returned as change, mechanism, exists, false or unverified), `approach-reviewer` (authority, spoofing, races, duplicates, partial-failure exposure), `clean-code` (cut what is not `Decided:`, so the loop never grows the design). `engines/plan.md` "Converge" says what each must cover.
- The finding bar every plan-round prompt carries: (1) a citation read (`file:line`, decision-record clause, ticket quote); (2) a change to the design, not an implementation detail; (3) not a `Decided:` item; (4) at most five findings, or exactly `CONVERGED`.
- Triage each round yourself into verified, housekeeping, drop and unverified; show the owner that split, never the raw list. Verify every load-bearing claim before folding it in. A real fork (push or poll, generic or single-producer) goes to the owner with the long-term trade-off; never pick the cheaper option to save effort.

AI failure modes at design time: an invented mechanism needs a `file:line`; no citation that was not opened; test the framing handed over instead of adopting it; no confident sizing without reading the code. Shared core: `checklists/build.md` §3.

## Vocabulary

One set. The first four are the finding severities in every mode.

| Label | Covers | `self` | `change` | `plan` reads it as |
|---|---|---|---|---|
| Blocker | wrong behaviour, security hole, data loss, broken contract, a test that proves nothing about the fix, a comment the change made false | fix before push | blocking thread; comment findings are non-blocking except a comment the change made false | wrong premise (kills or rescopes, goes first) or blocks approval |
| Refuse | too big to review, or mechanical churn burying the behaviour change | split before push | ask for a split before reviewing | n/a |
| Should-fix | quality a senior engineer would stop at | fix before push; blocks exit | posted as `Consider:`, non-blocking | should change |
| Nit | style, naming, wording | round 1 fix; later fix if trivial, else list; never blocks exit | non-blocking, batched | note |

Quality findings are never dropped on someone else's change, only labelled non-blocking. Google's standard applies: approve once the change improves the overall health of the code. Don't block on preference.

The other words each belong to one step, not to severity:
- Claim marks: **verified**, **false**, **unverified because X**.
- Refuter rulings: CONFIRMED, REFUTED, PARTIAL; fix-check FIXED, NOT FIXED, REGRESSED (recheck threads: PARTIAL for FIXED-in-part).
- Triage actions ("Resolve findings"): CONTEST, ESCALATE, FIX, DECLINE.
- Posting verdict, a recommendation, approving stays the owner's call each time: **Approve** (no findings, or only `Nit:` and `Consider:`), **Don't approve** (at least one Blocker posted; name it in five words), **Split first** (Refuse).
- Plan rollup per ticket: sound, rework, wrong premise, merge, drop.

A finding line: `file:line - what breaks - fix`.

## Claims

Before reading the diff, write the claims down: every load-bearing assertion from the ticket, the description and the code's own docstrings, one line each. "This endpoint needs no auth", "nothing clears this on the way out", "inert until the follow-up lands": each has a file and a line behind it, and a review that repeats one back has laundered it into fact. Each ends marked verified (you found the code), false (code contradicts it) or unverified (say why). A false premise is reportable on its own even when the diff is fine, because the scope was derived from it. Anything asserted about a control (a permission gates a tool, a guard catches a class, a caller cannot reach a path) is followed to the object that enforces it and read there: a declaration is not enforcement. A test that contradicts the ticket makes the code the suspect, not the test. The ledger goes in the report. Where a briefing hands an agent the ledger, it must give a verdict on every line (confirmed, contradicted, could not tell); asked which claims it confirmed, an agent answers with the ones it happened to touch.

## Pin a real checkout

Never review off whatever branch the local repo is on. Never trust a local `origin/<base>` without fetching. `<base>` is the repo's default branch (`git symbolic-ref refs/remotes/origin/HEAD`), never assumed `main`.

```bash
R=<local repo dir>; WT=<scratchpad>/wt; mkdir -p $WT
git -C $R fetch origin
BASE=$(git -C $R symbolic-ref --short refs/remotes/origin/HEAD)
git -C $R worktree add -q --detach $WT/head <head_sha>   # SHAs from the source control adapter
git -C $R worktree add -q --detach $WT/base $BASE
git -C $WT/head rev-parse HEAD   # MUST equal the head SHA: print it, check it
```

- Detached worktrees; the owner's own checkouts and branches are untouched.
- Read the change's discussions now (`engines/ship.md`), who raised each and whether resolved. They are for triage and never go to an agent: a hunter that read other reviewers' threads anchors on them.
- Reviewed this change before: pin your last reviewed head too and review the diff from it. Read the whole change again only when that diff touches what the earlier review relied on.
- A chain of dependent changes: pin every link. "Inert until the other lands" is checkable only with both heads on disk.
- Fetch every repo whose code the review reasons about and say which were stale. Check consumers off the default branch's `origin/<base>`, never a local branch:
```bash
for r in <repos>; do
  b=$(git -C $r symbolic-ref --short refs/remotes/origin/HEAD)
  before=$(git -C $r rev-parse $b | cut -c1-8); git -C $r fetch -q origin
  after=$(git -C $r rev-parse $b | cut -c1-8)
  [ "$before" = "$after" ] || echo "$r: $before -> $after WAS STALE"
done
```

## Is it reviewable at all

Size it first: `git diff --stat`, commit count, the fraction that is mechanical. Too big to review is a refusal, not a non-blocking note: ask the author to split and say it in the report rather than reviewing badly. Mechanical churn burying the lines that change behaviour is the same finding in disguise. Where the ticket spans two repos, read both changes before commenting on either: the strongest finding is often invisible from inside one (two changes that each improve their file and together fork a shared abstraction), and say it was invisible from inside.

## Read the diff, then the files

Write `diff.patch`, `files.txt`, `change.json`, `ticket.md`, `description.md`, `ledger.md` and `brief.md` once (next section). The diff comes from the pinned worktree, not the API, so a large file is never empty; read it in ranges. Then read the changed files whole from the worktree: a large block move can hide a few real edits.

## Approach pass

Code review asks whether it is built right. The cheaper half. The other half is whether it should exist and is built the right way round. Do this before delegating, with the ticket and diff in front of you.

- Read the whole ticket yourself: description, acceptance, testing notes, comments fetched as a separate call, parent epic, linked issues. Then the change description in full, and everything it links or embeds (design docs, diagrams, artifact links): the approach is judged against the design it claims, and a diagram is a claim. Where ticket description and thread disagree, say which the change implements. A subagent's quoted line is not a check.
- Does the ticket's premise hold? Premises are written before the work and go stale.
- Does the bug reproduce by the path a caller takes? Trace the real entry point and see what it already does to the input the description calls trusted. A fix can be right while its stated reason is wrong; say both: the premise fails, the change stands, here is what justifies it.
- Does the control run, or is it only declared? A decorator, a policy flag, a gate in report-only mode: follow each to the object that executes it.
- What does a new guard not match? Hunt the siblings with the same flaw under another spelling (`owner_id` or `user_id`, a ternary fallback, a dynamically keyed store), then ask whether what it catches was already covered upstream.
- Does the work already exist in a sibling repo or the workspace? Duplicated measurement is worse than none.
- Is the sequencing right? Do not build every input to an unvalidated deliverable.
- When the change produces a number (score, metric, benchmark, threshold): does it measure what it claims (find the trivial strategy that beats it; a rate over a handful of fixtures moves in coarse steps); would the environment produce this anyway (what if the subject were replaced by a competent one); who reads it and what happens when it is wrong in the likeliest direction (confident, stable and wrong is worse than noisy)?

Approach findings are posted like code findings, inline when a changed line carries the claim, else as one general note. Say which are approach-level in the report.

## Agents

| Step | Agent |
|---|---|
| Ticket and links | `change-reader`, verbatim; the main thread reads the text itself and the ledger comes from it, not the summary |
| Hunt | `cold-reviewer`, `clean-code`, `test-gap-auditor`, `miss-hunter`; `security-reviewer` when routes, auth, input, secrets or permissions are touched |
| Approach | `approach-reviewer`; with `premise-attacker` when the change produces a number (it owns `checklists/design.md` §16) |
| Refute | `finding-refuter`, one per change, all in one message, each reading only that change's findings files and scratch dir |
| Cross-change and seams | `approach-reviewer`, `design-gap-finder`, `caller-mapper` |
| Run a claim | `claim-prover` |
| Pipeline and status | `change-reader`, `run-digest` |

Hunt lanes (`checklists/review-core.md` numbers): `cold-reviewer` §0, 1 except proportional abstraction, 2, 8, 9 production error paths, 10-15, 17. `clean-code` §3-6 and §1 proportional abstraction. `test-gap-auditor` §7, 16, §9 tests of error paths. `miss-hunter` works the whole checklist independently, never reading others' findings, aiming where things hide: response-shape refactors, permission predicates, error strings, anything the diff calls "inert" or "pure move". A second `miss-hunter` round runs only when the first found Blockers. `finding-refuter` refutes everything that comes back, the main thread's own drafts included. Hunt the AI failure modes of `checklists/build.md` §3 in every lane. None gets your rationale or the session's history.

If the pipeline is green on the pinned head and a job in it actually runs the tests (`engines/ship.md` CI loop), tell `test-gap-auditor` to name that run and not rerun. On others' changes the auditor reads tests against the diff and runs nothing by default; it trusts CI and says so when CI is red or skips tests. Exception: mutation only for guards at trust boundaries (path traversal or prefix, auth or permission checks, delete or write scope, gate direction), at most 5 mutants and 10 minutes, on a scratch copy; skip it when tests take over 1 minute to start, need live backends, or are contract or integration suites, and write `not run: <reason>`. `finding-refuter` on others' changes may run one targeted test or script, capped at 5 minutes; otherwise it reads only and marks the ruling partial. In `self` mode, mutation and tests stay.

## Briefing

Every agent gets the same base and nothing else: the diff, the full ticket, repo name and path, its `CLAUDE.md`, any decision record that applies; on a change, the pinned worktree paths and SHAs. All of it travels as files in the scratch dir. Never the author's or main thread's reasoning, the plan, earlier rounds' findings, other agents' findings, or the change's existing threads.

| Agent | On top of the base | Withheld |
|---|---|---|
| `cold-reviewer`, `clean-code`, `test-gap-auditor` | claims ledger, change description; the threat model when auth is touched | none |
| `miss-hunter` | none | description and ledger; it builds its own claims from the ticket (author framing such as "pure move" or "inert" cuts what a reviewer finds) |
| `finding-refuter` | the findings to refute, the ledger; in fix-check mode the previous round's confirmed findings and the fix delta | none |

## Scratch dir, one diff, findings in files

Every run has `${DRAFTS_DIR:-~/drafts}/reviews/<repo>-<iid>/` (`self`: `<repo>-self-<branch>`; the cross-change pass: `reviews/batch-<YYYYMMDD-HHMM>/`, or `<epic-key>/` for an epic). Agent scratch, never committed.

| File | Written by | Holds |
|---|---|---|
| `diff.patch` | main thread, once per change (`self`: each round) | `git -C <head worktree> diff <base_sha>..<head_sha>`; recheck `<reviewed_sha>..<head_sha>`; self round 1 `git diff origin/HEAD...HEAD` plus uncommitted, round n>1 `<sha reviewed in round n-1>..HEAD` plus uncommitted |
| `rounds.txt` | main thread, `self` | each round's reviewed sha |
| `files.txt` | main thread | `git diff --name-status` of the same range |
| `change.json` | main thread | metadata with `diff_refs`, title, author, branches, url; description removed |
| `ticket.md` | main thread | ticket text verbatim: description, acceptance, comments, parent epic, linked issues |
| `description.md`, `ledger.md`, `main-drafts.md` | main thread | the description; the claims ledger; the main thread's own drafts, so the refuter gets paths |
| `brief.md` | main thread, once per change | goal in one line, change url, repo and path, head and base SHAs, worktree paths, the files above except `description.md` and `ledger.md`, and the rules: never edit pinned worktrees, never post, write findings to your path |
| `<agent>[-<angle>]-<round>.md` | the agent | its full output; round is a number or `recheck`, e.g. `cold-reviewer-1.md`, `finding-refuter-fixcheck-2.md` |

Spawn prompt: `Read <dir>/brief.md. Your findings path is <dir>/<agent>-<round>.md.` plus the files that agent gets per "Briefing", its angle (`dependency`, `after-build`, `fixcheck`) and which tests it may run. Agents read `diff.patch` and `files.txt` instead of running `git diff` over the whole change; `git log`, `blame` and `show` on single files stay allowed. Agents return only the path, counts by severity and the top finding in one line. The main thread opens a file for detail and passes paths, never pasted findings.

Time budget: about 15 minutes for a review, 20 to 25 for a big batch. Stages run in waves: all reviewers for all changes, then all refuters, then the seams. When a stage would exceed its share, add parallel agents, not sequential passes.

Cost line, before a fan-out over 10 agents: `Fan-out: <N> agents (<n> per model), ~<tokens>k tokens`, then carry on without a prompt. Each agent's model is its frontmatter; estimate ~15k first-turn tokens plus its work (diff readers: `diff.patch` bytes / 4).

## Resolve findings

Every finding any agent returns is sorted by the main thread, after reading the cited code, before it acts or relays.

| Triage | Meaning | Then |
|---|---|---|
| CONTEST | wrong, with evidence the agent could read (file and symbol, or a decision in the plan note's Decisions) | dropped |
| ESCALATE | wrong, but the proof is outside what the agent could read (a verbal decision, team convention) | goes to the owner, not fixed |
| FIX | valid; changes how the work is done | fixed |
| DECLINE | a nit | recorded, skipped |

- A contest must be checkable. "This was intentional" is not evidence; neither is wanting to contest because you wrote the code.
- A comprehension gap (the doc lacks context) is a FIX to the doc, never a contest.
- A finding that holds and reverses an owner decision goes to the owner as one question with your verdict; the plan is not rewritten around it. One that would remove or shrink a `Decided:` item is never applied, same question.
- A cut or scope reduction is valid only with: already exists (`file:line`), the code contradicts the premise (`file:line`), an ordering or dependency blocker, or a named concrete risk. "Simpler", "YAGNI", "smaller", "could ship later" alone is DECLINE.
- Investigator claims are checked against their cited `file:line` before use; a mismatch is a CONTEST.
- Record the sorted list in the plan note Decisions (plans) or the review notes (reviews), not in chat. Never relay an agent's verdict verbatim.

A finding closes in exactly two ways: you change the code, or you produce evidence the reviewer can check itself (a `file:line`, a command, a test that already covers it). Arguing a reviewer down turns a loop into agreement with yourself.

### Triage of what comes back (change, epic)

- Compare every draft against every existing discussion, from the pin step: open or resolved, human or automated, inline or general. Same point means same defect, not same line.
- Never reply in a thread someone else started.
- Same point, thread open, raised by a person: drop the draft and react ➕ to that thread's first note, unless you already reacted.
- Same defect at a place that thread does not cover: a new thread of your own on that place.
- Thread resolved, answered by the author, or raised by an automated reviewer: drop it.
- Never a second thread on a point already raised.
- The last note decides reply or edit. Yours last: never reply. Still open or partly fixed: edit your note to the current state only, prefixed `Updated at <short sha>:`. Fixed: resolve with no comment. Reply only when someone wrote since your last note. A genuinely new defect is a new thread. "Fixed in <sha>" replies belong to your own changes only.
- Drop findings the description already documents ("inert until X lands" and the code agrees).
- Separate a security hole from a weak test. Overclaiming is the fastest way to be ignored.
- Downgrade races with idempotent effects: duplicate work is not corruption.
- Say when a finding contradicts the author's stated rationale: quote their claim and the code beside it.
- A test that proves nothing about the fix is a Blocker (asserting a call returned, a key exists, a list is a list). Other test-quality findings are non-blocking.
- Then re-read the ticket against the tests: cross its testing notes against the tests in the diff; a scenario the ticket names that no test covers is the highest-value finding available (verify the gap in the test file). An unmet acceptance criterion is a scope question, resolved against the description first: named as a sibling change's job, it is the plan.
- The ticket is a suspect, not a ruler. Say which artifact disagrees with which.

## Intensity

One scale for every mode, node review and skill: `light | medium | intense`, default `medium`. It is separate from plan size: a plan's `kind` (task, bug, spike, story, epic, fix) sizes the work and never sets review depth. This section defines the scale; `build`, the skills and the docs point here and nothing else decides depth.

| Level | Finders | Refute | Rounds |
|---|---|---|---|
| `light` | one finder | none; the main thread reads the cited code for anything Blocker | 1 |
| `medium` | `cold-reviewer` | `finding-refuter` | up to 3 |
| `intense` | in parallel: `cold-reviewer`, `clean-code`, `test-gap-auditor`, `miss-hunter`, plus `security-reviewer` when auth, input, secrets or permissions are touched | `finding-refuter`; `comprehension-cutter` on posted comments | up to 3, all finders each round |

Medium and intense rounds: round 1 is the full review; round 2 is a fix-check on the fix delta; round 3 is a quick final scan of the whole diff. Stop early after any round with zero Blocker and zero Should-fix. In `change` and `epic` the reviewer fixes nothing, so round 1 is the review and a later round is a `recheck`.

Finders by level and mode:

| Mode | `light` | `medium` | `intense` |
|---|---|---|---|
| `self`, `change`, `epic` (each change), node review | `cold-reviewer` | `cold-reviewer`, then `finding-refuter` | all finders above, then `finding-refuter` |
| `plan` | `premise-attacker` | `premise-attacker` and `approach-reviewer`, then refute | adds `design-gap-finder` and a decision-record sweep by `researcher` |
| `comments` | `finding-refuter` only | `finding-refuter`, and the main thread confirms each verdict in code | adds `claim-prover` runs |

`recheck` is a separate flag on `change` (re-review after the author's fixes), not a level.

Who sets it:
- The owner's argument (`light`, `medium`, `intense`) wins and is recorded as given.
- Otherwise the plan's node table carries an `intensity` column per build node, chosen by the planner (`engines/plan.md`): default `medium`, raised to `intense` for auth, migrations, money and public contracts, lowered to `light` for docs or config-only nodes. A node reviews at its own intensity; the `self` review of a planned change uses the highest in the table.
- An entry point without a plan defaults to `medium`.

| | `light` | `medium` | `intense` |
|---|---|---|---|
| Node review | one round on the node's diff | rounds above on the node's diff | rounds above on the node's diff |
| Wave review | none | none | `cold-reviewer` on the wave diff, `test-gap-auditor` |
| Post-completion subset in `self` | none | only when the plan field is set and the story touches UI, permissions or data | per set field |
| `epic` post-completion | none | Y rows of "Post-completion checks" | Y rows, plus every set P row |

### Rounds and caps

The one set of numbers. Skills pass intensity; nobody restates these.

| Unit | Rounds | Refute |
|---|---|---|
| `self` | per "Intensity" | none at `light`; fix-check from round 2 |
| `change` | 1 review at the chosen level | per "Intensity"; 1 per change, in parallel |
| `change` recheck | 1 hunt on the delta | fix-check on open threads |
| `epic` | each change once as `change` at the epic's level, then 1 seam pass, 1 post-completion | 1 over all changes |
| `comments` | 1 | per "Intensity" |
| `plan`, reviewing a plan | per "Intensity", until `CONVERGED` | main thread verifies |
| `plan`, judging someone else's ticket or epic | 1, finders per "Intensity" | main thread verifies |
| node review | per "Intensity"; fix rounds 2 by default | fix-check agent |
| CI fix rounds | 10, `engines/ship.md` | n/a |
| push-gate repairs | 2, `engines/ship.md` | n/a |

- Findings cap per agent per round, most severe first:

| Agent | Findings |
|---|---|
| `cold-reviewer` | 10 |
| `clean-code` | 5 |
| `miss-hunter` | 8 |
| `test-gap-auditor` | 8 |
| `security-reviewer` | 8 |

- Nits: at most three per reviewer at `light`, five otherwise, the most useful, per round.
- Posted comments: three or four the author acts on beat eight they skim.
- Every round spawns new agents with no memory of the last: a reviewer that remembers its findings defends them. Never re-dispatch a reviewer on code that has not changed since its last run.
- Round 1 fixes every severity in `self`, nits included. Rounds 2+: a new finding counts only if a Blocker or a Should-fix inside the fix delta; the rest is listed.

`self` rounds 2+: reviewers read the whole branch but hunt in the fix delta and its callers only. A fix-check agent, `finding-refuter` in fix-check mode (its own spawn, never a reviewer, never the main thread), gets the previous round's confirmed findings and rules each FIXED, NOT FIXED or REGRESSED with a `file:line`. `miss-hunter` and `clean-code` run in round 1 only, except in the round-3 final scan at `intense`, where every finder runs on the whole diff. A whole-branch pass with all of them reruns when a fix restructured code (a new function, moved or duplicated code) or the delta exceeds 50 changed lines. Mechanical quality gates run every round that changed source.

`self` exit: a round with zero Blocker and zero Should-fix, fix-check all FIXED, tests green in that same round. A round that fixes something and stops there has not converged. Record each round separately: what it found, what changed, whether tests passed. Stop after the last allowed round with open findings: give the owner each with your position and do not push.

### Node review

Round 1: the finders the node's `intensity` gives, on the node's diff (`git diff -- <owns>`); every severity is fixed. At `light` the node stops after round 1: the builder's own focused test confirms each fix, with no second reviewer, unless round 1 found a Blocker, which gets fix rounds for that Blocker only. Fix rounds: reviewers see only the diff since the reviewed sha plus its callers, and a fix-check `finding-refuter` rules each earlier finding. A new finding counts only if a Blocker or a Should-fix in the fix delta; the rest goes to a follow-up list in the node report, carried into the `self` review, and never fails the node. The node passes with zero open Blockers, fix-check all FIXED, and its acceptance or FR tests green. A Blocker that survives the fix-round cap stops the run: ask the owner. A node at `intense` also gets the post-completion check its plan field names; an empty field skips it.

### Post-completion checks

Cheap first; stop at the first failure that invalidates the later ones. Y runs, P runs only when the plan field is set.

| Check | Agent | Plan field | Epic | Story: UI | Story: permissions | Story: data | Story: perf | Bug |
|---|---|---|---|---|---|---|---|---|
| Regression on merged main | `run-digest` (merged-main mode) | none | Y | - | - | - | - | - |
| Premise vs epic and designs | `premise-attacker` (after-build mode) | `frames` | Y | P | - | - | - | - |
| Bug re-check | `claim-prover` (bug-list mode) | none | Y | P | P | P | P | Y |
| Risk flows end to end | `ui-verifier`, `claim-prover` | `risk_flows` | Y | Y | P | P | P | P |
| Role matrix | `role-tester` | `roles` | P | - | Y | - | - | P |
| Edge cases | `edge-case-explorer` | `risk_flows` | Y | Y | P | Y | P | - |
| Accessibility | `a11y-auditor` | `frames` | P | Y | - | - | - | P |
| Frame vs build | `ui-verifier` (frame mode) | `frames` | P | Y | - | - | - | P |
| Migration | `migration-verifier` | `migrations` | P | - | - | Y | - | P |
| Ops readiness | `ops-readiness-auditor` | `signals`, `flags` | Y | - | - | P | P | - |
| Dependency and licence | `security-reviewer` (dependency mode) | `deps_added` | P | P | P | P | P | P |
| Perf | `perf-tester` | `hot_path` | P | - | - | - | Y | - |

Placement: merge-time checks (migration, ops readiness, role, accessibility, frame, risk flows, edge cases, perf for perf stories, dependency) run in `self` and `change` on the branch or a local stack; risk flows go to `ui-verifier` for UI and `claim-prover` for API. Regression, premise, bug re-check and the epic column of every other row run in `epic` on merged main. The alert-exists check runs after deploy.

Shared environments: `role-tester`, `edge-case-explorer` and `ui-verifier` write (type, fill, create records), so they run only on a local or ephemeral stack. A team can add a read-only smoke agent for shared environments, with no typing, form filling, evaluate, upload or Bash. `claude/hooks/shared-env-guard.py` blocks browser writes on hosts in `claude/hooks/shared-envs.txt` as a second line. `perf-tester` needs a stable stack, a local one on merged main; with none it reports `skipped: no stable stack` and never falls back to shared dev. The lens fan-out is the existing hunt agents.

## Reviewer conduct

- No author rationale to the reviewer. Reviewer strength is set by the agent's pin, not the call (`engines/common.md`).
- Every finding gives the file and line, what breaks, what it costs now, and the fix in prose. A finding that could go two ways is not one yet: run it. A decision rather than an implementation has no fix; say so. If it cannot be run, say which branch you believe and label it unverified. A hard error on every request is a broken endpoint, not a silent wrong write: different severity.
- A finding whose `file:line` does not resolve in the pinned tree is dropped.
- Say what you ran and what you only read; name the changed files you did not read and the parts you skimmed. Review every line you were asked to review.
- Mention what is done well, briefly: it calibrates the rest (not in `plan` mode).
- Cap the list at what matters. A report padded with style findings while a real bug sits open is a failed review: state the bug first.
- Agreeing with the author's or another reviewer's framing without checking the code is sycophancy. Agreement between reviewers is not evidence: models share blind spots, so several agents endorsing one finding count as one.
- Confirm: the main thread checks every survivor in the code itself, and how many agents reported it never raises its verdict. A finding about runtime behaviour is confirmed only by running it, on a scratch copy and never in the pinned worktree; one settled by reading is partial at best. Hunt what makes a finding weaker: a sweeper that recovers the state called unrecoverable, a validator upstream of the field called unvalidated, an idempotent write behind the race called corruption.
- Entry-point threat model: who can reach this code and what do they control? Reach it the way a caller does and report what the entry point already does to the input before the diff sees it.

## Posting rules

Mode `change` and `epic` only. Nothing posts before the owner's OK (`engines/common.md`); never approve or merge. Before the OK the owner is shown the three lines (`engines/write.md`), the drafts, the anchors, and per item: `new thread`, `edit my note on path:line`, `reply in my thread on path:line`, `react ➕ on <author>'s thread on path:line`, `resolve` or `dropped: already raised by <author>`.

Anchor on lines the change adds; a context line is fragile. Compute post-image line numbers from the diff, do not guess:

```bash
git -C $WT/head diff <base_sha>..<head_sha> -U0 -- <paths> | awk '
/^\+\+\+ b\// {f=$2; sub(/^b\//,"",f)}
/^@@/ {match($0,/\+[0-9]+/); n=substr($0,RSTART+1,RLENGTH-1)+0; next}
/^\+/ && !/^\+\+\+/ {print f":"n; n++; next}
/^-/ {next}
{n++}'
```

Every anchor appears in that output (`grep -n` the head file, confirm it is in the added set). Put a finding on the line that causes it; for a mismatch between two places anchor on the new code and cite the other by `path:line`. A finding that belongs to the ticket or description rather than one line is one general note, not forced onto an unrelated line.

Immediately before posting, re-read the discussions (`engines/ship.md`) and re-run the triage comparison on anything new. One thread per `new thread`, worst first; post one and check it lands before the rest. Replies in your own threads go in the existing discussion, never as a new thread, only when someone wrote after your last note. Reactions go after the threads and after the OK, re-checked against the re-read discussions, and skipped if your reaction is already there. Skip a summary note unless asked: the inline threads are the review.

### Comprehension test

Read each comment as the author will: someone who knows this repo, not the subject the finding rests on, being told their work has a problem. The first sentence says what breaks in words they already have, no jargon, no identifiers; evidence goes underneath. If a paragraph of background comes before the problem, the background is the comment. Then cut: a finding you would not defend out loud is not posted; two unrelated nits do not share a thread. In `intense`, run it as `comprehension-cutter`, given the drafts and the ticket only, told that deleting a true finding is the expected outcome. It asks whether the author can act on this (true, small and unactionable gets cut), and sends a finding the author does not own to whoever does, not into a thread where it dies. The measure is whether the author, reading it alone, knows what to change.

### Comment style

A colleague leaving a note, not a report. Register and caps: `checklists/prose.md` §7 "Review comment"; framing is the bullets below.
- Open with the observation in plain words, not a heading or a severity label. Prefix a non-blocking point with `Nit:` and a blank line.
- Hedge the judgement, never the fact. Ask when the author may know something you do not. Deflate your own nits. Say when something is good, briefly.
- Cite evidence inline as `path:line` or a permalink. Offer the fix as a possibility; a `suggestion` block when it is a line or two.
- Interfaces and contracts get harder scrutiny than implementation: an interface is the hardest thing to walk back once things depend on it. Mark anything non-blocking explicitly so the author can decline; offer code marked untested; say what is out of scope ("worth doing in this change, or as a follow-up?"); lead the summary with what is right.
- Write what you did ("I checked for a retry and there is none"). Say in one parenthetical if you corrected your own reading mid-review. Concede in the same comment where you overreach.
- Survives the compression: the defect first and concrete, the shortest decisive evidence with `path:line`, the consequence for whom, one fix.
- Never defend prose the author deleted. Removing a ticket ID, decision-record number, attribution or tutorial comment is correct every time, and the diff needs no justification. Do not ask for it back or use "it used to say" as evidence. A rule the deleted prose carried is argued in its own words on the code as it stands, saying the ticket ref is not wanted. A change that adds a ticket ID, a decision-record number or a "This function..." preamble to a comment is a finding.

## Report shape

Per `engines/common.md`. The result first, one line per change or comment before any detail: the verdict (`change`, `epic`), the call (`plan`), or per-round findings (`self`: what each round found and what changed, tests passed or not, the node table with what each cost). Then the claims ledger, approach-level findings named apart from code-level ones, what was not checked, anything open with your position, and a missing tracker key in the title. `epic` adds the table: seam, owner change, safe merge order, coverage gap; after merge, one line per post-completion check, result with evidence or skipped and why. `comments` per comment as above. `plan` draft per its step 5. Before anything ships under the owner's name: the three lines.
