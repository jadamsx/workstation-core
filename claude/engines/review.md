# Review engine

Review from the code, not the diff text. A finding stands only when it is proved. Git safety, gates, delegation and the report skeleton: `engines/common.md`. Agent rules: `engines/agent-core.md`. Every source control call: `engines/ship.md`. Checklists hold the items: `checklists/review-core.md`, `review-domain.md`, `design-review-shared.md`, `design.md` for plan mode, `ui-verify.md` for UI, plus any domain checklist the team registers.

The failure this engine prevents: a plausible finding, posted, that the code does not support. A wrong comment costs the author more than a missed one.

The bar in the brief is the whole bar: reviewers add no checks or rounds the plan did not set, flag bolt-ons (additions outside the brief or Owns) and deviations from the Decided and Not-building lines, and report older problems in one line.

## Params

| Param | Values |
|---|---|
| `mode` | `self`, `change`, `epic`, `comments`, `plan` |
| `intensity` | `light` (default), `medium`, `intense` |
| `target` | branch, change URL, epic key, list of URLs, pasted comments, ticket or doc |

The owner's argument wins. A node reviews at the `intensity` in the plan's node table (`engines/plan.md`); `self` uses the highest of them; no plan means `light`. Auth, input, secrets or permissions in the diff raise the review to at least `medium`.

## Round shapes

Plans and code alike; nothing else decides depth.

| Intensity | Round 1 | Round 2 | Round 3 |
|---|---|---|---|
| `light` | one finder | fix-check only if round 1 found a Blocker | none |
| `medium` | `cold-reviewer`; plus `security-reviewer` when auth, input, secrets or permissions are touched | `finding-refuter` fix-check on the fix delta: FIXED, NOT FIXED or REGRESSED | quick confirmation of open findings against the delta |
| `intense` | in parallel `cold-reviewer`, `clean-code`, `test-gap-auditor`, plus `security-reviewer` as above; plan reviews add `approach-reviewer` in both modes | as `medium` | as `medium` |

Plan finders: `light` `premise-attacker`; `medium` adds `approach-reviewer`; `intense` adds `approach-reviewer` gap mode and a `researcher` decision-record sweep. `comments`: `finding-refuter` only; `intense` adds `claim-prover` runs.

Rules for every round:
- The findings file starts with `Round: n of 3`, written from the spawn prompt. A round with n > 3 is refused: no agent is spawned and the report says so.
- An open Blocker after round 3 stops the run and goes to the owner with each finding and your position. There is never a round 4.
- Stop after any round with zero Blocker and zero Should-fix.
- `comment-cutter` runs at `medium` and above over the branch diff. `comprehension-cutter` runs on posted comments at `intense`.
- A rebase that leaves `git patch-id --stable` unchanged skips re-review only when CI is green and the base diff does not touch the patch's files.
- Prove or drop. A code finding needs a rerun or a quoted `file:line`; a plan finding a quoted `file:line` that contradicts the claim. A read-only security finding with a quoted line may still block. Anything else is listed as Dropped with why. `claim-prover` reruns without a browser when the claim needs none.
- Round 1 fixes every severity in `self`. Rounds 2 and 3: a new finding counts only if it is a Blocker or Should-fix inside the fix delta or its callers; the rest is listed. `clean-code` runs in round 1 only.
- Findings per agent per round, most severe first: `cold-reviewer` 10, `clean-code` 5, the others 8.

## Modes

| Mode | Subject | Findings go to |
|---|---|---|
| `self` | your own branch; diff `git diff origin/HEAD...HEAD` plus uncommitted; no pin, no size check | fixed in the code; posts nothing |
| `change` | someone else's change, pinned | drafts, cut, shown to the owner, posted after their OK |
| `epic` | each change of an epic, as `change`, then the epic checks | as `change` |
| `comments` | other people's review comments, pinned as `change` | chat only |
| `plan` | a ticket, epic or plan before anyone builds, against the code off `origin/<base>` | a local draft; never edits the thing reviewed |

### Mode `self`

Tick the design note's Progress lines as steps pass. Without a ticket the run stops after the report: no description, no push, no CI loop.

0. For a `format: v2` note, fill each Traceability row's Status from real runs via `run-digest`; flag every FR without a passing test, test with no FR, and node whose diff left its `owns`.
1. The rounds above over the whole diff, then the merge-time rows of "Post-completion checks" for each plan field that is set. `self` exits with zero Blocker and zero Should-fix, fix-check all FIXED and tests green in that round; at round 3 with open findings, give the owner each with your position and do not push.
2. Gates through `run-digest`; `comment-cutter` at `medium` and above.
3. Out: change description (`engines/write.md`), open it, CI loop; ticket drafts are one list, asked once.
4. Record the design note (`status: shipped`, change link, Decisions as built) and project index; report each FR's Status for a v2 note.

Any source change after the final pass goes back through this mode before the push.

### Mode `change`

Optional review note `${NOTES_DIR:-~/notes}/projects/reviews/<repo>-<number>.md` per `templates/review.md`, with `reviewed_sha`, `verdict` and one line per posted thread.

`light` and `medium` skip the area index, ledger, approach pass and merge-time checks. Read the cited code yourself for anything Blocker or Refuse. A control missing from this repo may live in the caller, gateway or shared library.

`intense` adds the ledger and an approach pass; it costs 50 to 100 times `medium`: use it when the owner asks, or offer it for auth, migrations, money or public contracts. The approach pass: read the whole ticket and description; does the premise hold and the bug reproduce by the path a caller takes; does the control run or is it only declared; does the work already exist in a sibling repo. Name approach-level findings in the report.

Recheck runs only on the owner's request, for a note with a `reviewed_sha`. Same head: report thread state only. Otherwise `diff.patch` is `reviewed_sha..head`, and `finding-refuter` fix-check rules each open thread of yours (`PARTIAL` when only partly addressed). Propose per thread: resolve, edit my note, reply (only when someone wrote after my last note), or leave.

### Mode `epic`

`change-reader` for the epic and children. Each change through `change` in parallel, one `finding-refuter` over all findings. Seam pass: `approach-reviewer` in gap mode, `caller-mapper`, `claim-prover`; each seam names its owner change, a safe merge order, and what is inert until another change lands. Show the owner the three lines, drafts and epic table; post per change after their go. After every change merges, run the epic column of "Post-completion checks" on merged main.

Delivery check (after merge): `approach-reviewer` gets the epic, its stories and the designs, not any story's ticket text, and reads the merged code on `origin/<base>`. Per story `delivered`, `partial` or `missing` with `file:line`, then anything built that nobody asked for.

### Mode `comments`

A reviewer's comment is a claim about the code, checked like a finding. It hunts nothing new.
1. Collect the comments, pinned head, description, ticket and linked designs. Write `decisions.md`: the plan's `Decided:` lines, the description, the author's earlier replies.
2. `finding-refuter` gets the comments as drafts in `comments.md` with `brief.md`, `decisions.md` and `diff.patch`, and no opinion of yours. It also says whether each belongs in this change.
3. Confirm every verdict in the code yourself; `claim-prover` runs what needs a run. True is not the same as belongs here: scope creep and pre-existing issues become a follow-up ticket; a comment against a decision is declined citing it, unless it brings evidence the decision lacked.
4. Report per comment: verdict with `file:line`, severity, outcome (fix, follow-up, or decline with a reason) and a drafted reply per `checklists/prose.md` §7.

### Mode `plan`

Judges whether work should be built at all and whether the plan survives contact with the code. Output is a draft for a human to send; never modify the ticket, epic or doc under review. Rounds per "Round shapes".

1. The five answers (`checklists/design.md` §0) by the main thread; `unknown` blocks.
2. `premise-attacker`, fresh, given the ticket only.
3. At `medium` and above `approach-reviewer`, and at `intense` independently its gap mode; neither sees the other's findings.
4. Prove every finding against the code yourself; one without a quoted `file:line` is Dropped.
5. Report shorter than the plan: the call (build, build reduced, don't); wrong premises first; per-ticket rollup; what is missing; sequencing; the dissenting case.

Fresh agents each round, given the ticket, the plan and every `Decided:` item, "attack how, never whether". Each prompt carries the bar: a citation read, a change to the design, not a `Decided:` item, at most five findings or exactly `CONVERGED`. Triage into verified, housekeeping, drop and unverified; a real fork goes to the owner.

## Vocabulary

| Label | Conventional Comments | Covers | `self` | `change` |
|---|---|---|---|---|
| Blocker | `issue (blocking)` | wrong behaviour, security hole, data loss, broken contract, a test that proves nothing about the fix, a comment the change made false | fix before push | blocking thread |
| Refuse | | too big to review, or mechanical churn burying the change | split before push | ask for a split |
| Should-fix | `suggestion (blocking)` | quality a senior engineer would stop at | fix before push | non-blocking |
| Nit | `nitpick` | style, naming, wording | round 1 fix | non-blocking, batched |

No praise label. Quality findings are never dropped on someone else's change, only labelled non-blocking.

Claim marks: **verified**, **false**, **unverified because X**. Refuter rulings: CONFIRMED, REFUTED, PARTIAL; fix-check FIXED, NOT FIXED, REGRESSED. Triage: CONTEST, ESCALATE, FIX, DECLINE. Verdict (the owner's call): **Approve**, **Don't approve**, **Split first**. A finding line: `file:line - what breaks - fix`.

## Claims

Before reading the diff, write down every load-bearing assertion from the ticket, description and docstrings, one line each, marked verified (you found the code), false (code contradicts it) or unverified (say why). A false premise is reportable on its own. A control is followed to the object that enforces it: a declaration is not enforcement. The ledger goes in the report; an agent handed it gives a verdict on every line.

## Pin a real checkout

Never review off the local branch or an unfetched base.

```bash
R=<repo>; WT=<scratchpad>/wt; git -C $R fetch origin
BASE=$(git -C $R symbolic-ref --short refs/remotes/origin/HEAD)
git -C $R worktree add -q --detach $WT/head <head_sha>
git -C $R worktree add -q --detach $WT/base $BASE
git -C $WT/head rev-parse HEAD   # MUST equal the head SHA
```

- Read the change's discussions now (`engines/ship.md`); they are for triage and never go to an agent.
- Size first (`git diff --stat`); too big is a refusal: ask for a split.

## Agents

| Step | Agent |
|---|---|
| Ticket and links | `change-reader` |
| Hunt | `cold-reviewer`, `clean-code`, `test-gap-auditor`; `security-reviewer` when routes, auth, input, secrets or permissions are touched |
| Approach | `approach-reviewer`; `premise-attacker` when the change produces a number |
| Refute, fix-check | `finding-refuter`: round 2 fix-check, and reproduces draft Blocker and Should-fix findings, the main thread's own included |
| Cross-change, claims, pipeline | `approach-reviewer` gap mode, `caller-mapper`, `claim-prover`, `run-digest` |

Hunt lanes follow `checklists/review-core.md` numbers: `cold-reviewer` §0, 1 (not proportional abstraction), 2, 8, 9, 10-15, 17; `clean-code` §3-6; `test-gap-auditor` §7, 16.

On others' changes `test-gap-auditor` trusts a green CI run and runs nothing; mutation only for trust-boundary guards, at most 5 mutants and 10 minutes, on a scratch copy. `finding-refuter` may run one targeted test, capped at 5 minutes; otherwise its ruling is partial. In `self`, mutation and tests stay. One exchange per disagreement, then it goes to the coordinator in the report with both positions.

## Briefing

Every agent gets the diff, the full ticket, repo path, its `CLAUDE.md`, any decision record that applies and, on a change, the pinned worktree paths and SHAs, all as files in the scratch dir. Never the author's or main thread's reasoning, the plan, earlier rounds' findings, other agents' findings, or the change's threads. `cold-reviewer`, `clean-code` and `test-gap-auditor` also get the claims ledger and description. `finding-refuter` gets the findings to refute and the ledger; in fix-check mode the previous confirmed findings and the fix delta.

Decisions: code reviewers of our own work (`self`, node review, a change of ours) also get `decisions.md`, the plan's `Decided:` lines only, no reasoning. A finding that contradicts a listed decision is dropped unless it states a fact the decision did not know; such a finding goes to the coordinator once as "decision X may be wrong because Y". Each ruling the coordinator or owner makes on a finding is appended to `decisions.md`, so later rounds cannot raise it again. Reviews of other people's changes get no plan.

## Scratch dir

`${DRAFTS_DIR:-~/drafts}/reviews/<repo>-<iid>/`, never committed: `diff.patch`, `files.txt`, `ticket.md` verbatim, `description.md`, `ledger.md`, `main-drafts.md`, `decisions.md`, `brief.md` (goal, repo path, SHAs, worktree paths, those files, and the rules: never edit pinned worktrees, never post, write findings to your path), and `<agent>[-<angle>]-<round>.md`, each opening with `Round: n of 3`. Self round 1 diffs `origin/HEAD...HEAD` plus uncommitted, later rounds from the last reviewed sha.

Spawn prompt: `Read <dir>/brief.md. Round: n of 3. Your findings path is <dir>/<agent>-<round>.md.` Agents return only the path, counts by severity and the top finding.

## Resolve findings

The main thread sorts every finding after reading the cited code.

| Triage | Meaning | Then |
|---|---|---|
| CONTEST | wrong, with evidence the agent could read | dropped |
| ESCALATE | wrong, but the proof is outside what the agent could read | to the owner |
| FIX | valid | fixed |
| DECLINE | a nit | recorded, skipped |

- A contest must be checkable; "this was intentional" is not evidence. A comprehension gap is a FIX to the doc.
- A finding that reverses an owner decision goes to the owner as one question with your verdict; one that would remove or shrink a `Decided:` item is never applied.
- A cut is valid only with: already exists (`file:line`), the code contradicts the premise, an ordering blocker, or a named concrete risk.
- Check investigator claims against their cited `file:line`; a mismatch is a CONTEST.
- Record rulings in the plan note Decisions or review notes and append each to `decisions.md`. Never relay an agent's verdict verbatim.

On `change` and `epic`, compare every draft against existing discussions; same point means same defect, not same line.
- Never reply in a thread someone else started or open a second thread on a raised point. Same point open by a person: drop the draft, react ➕. Resolved, answered or automated: drop.
- The last note decides. Yours last: never reply. Open or partly fixed: edit your note, prefixed `Updated at <short sha>:`. Fixed: resolve silently. Reply only when someone wrote since.
- Drop findings the description documents. Cross the ticket's testing notes against the tests: a named scenario no test covers is the highest-value finding. The ticket is a suspect, not a ruler.

### Node review

Round 1: the node's finders on `git diff -- <owns>`; every severity is fixed. Later rounds follow "Round shapes": reviewers see the diff since the reviewed sha plus callers, and a new finding that is not a Blocker or Should-fix in the fix delta goes to a follow-up list carried into `self`. The node passes with zero open Blockers, fix-check all FIXED and its acceptance or FR tests green. A Blocker open after round 3 stops the run: ask the owner.

### Post-completion checks

Cheap first; stop at the first failure that invalidates the later ones. Y runs, P only when the plan field is set. In `self`: none at `light`, at `medium` when the plan field is set and the story touches UI, permissions or data, at `intense` per set field. `epic`: none at `light`, Y rows at `medium`, Y rows plus every set P row at `intense`.

| Check | Agent | Plan field | Epic | UI | Perms | Data | Perf | Bug |
|---|---|---|---|---|---|---|---|---|
| Regression on merged main | `run-digest` (merged-main mode) | none | Y | - | - | - | - | - |
| Premise vs epic and designs | `approach-reviewer` (delivery check, mode `epic`) | `frames` | Y | P | - | - | - | - |
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

Story columns are UI, permissions, data, perf. Merge-time checks (all but regression, premise, bug re-check and the epic column) run in `self` and `change` on the branch or a local stack; the rest run in `epic` on merged main. `role-tester`, `edge-case-explorer` and `ui-verifier` write, so they run only on a local or ephemeral stack (`claude/hooks/shared-env-guard.py` blocks browser writes on hosts in `claude/hooks/shared-envs.txt`). `perf-tester` needs a stable local stack; with none it reports `skipped: no stable stack`.

## Reviewer conduct

- No author rationale to the reviewer.
- Every finding gives the file and line, what breaks, what it costs now, and the fix. A finding that could go two ways is not one yet: run it, or label the branch you believe unverified. One whose `file:line` does not resolve in the pinned tree is dropped.
- Say what you ran and what you only read. Agreement between reviewers is not evidence.
- Confirm: the main thread checks every survivor in the code. A runtime claim is confirmed only by running it on a scratch copy, never in the pinned worktree; settled by reading is partial at best.

## Posting rules

`change` and `epic` only. Nothing posts before the owner's OK; never approve or merge. The owner is shown the three lines (`engines/write.md`), the drafts, the anchors and per item: `new thread`, `edit my note`, `reply in my thread`, `react ➕`, `resolve` or `dropped: already raised by <author>`.

Anchor on lines the change adds, on the line that causes the finding; every anchor is a post-image line of an added hunk line, checked against:

```bash
git -C $WT/head diff <base_sha>..<head_sha> -U0 -- <paths>
```

Before posting, re-read the discussions and re-run the triage comparison. One thread per finding, worst first. A claim one command can prove is run before it is posted; one that cannot be run is cut. A clean change gets no comment: say "clean" in chat.

Comprehension test: read each comment as the author will. The first sentence says what breaks in words they already have; evidence goes underneath. A finding you would not defend out loud is not posted. At `intense`, `comprehension-cutter` gets the drafts and the ticket only and is told that deleting a true finding is the expected outcome.

Comment style: register and caps in `checklists/prose.md` §7 "Review comment", labels per "Vocabulary". Hedge the judgement, never the fact; cite `path:line`; offer the fix as a possibility. Never defend prose the author deleted: removing a ticket ID, decision-record number, attribution or tutorial comment is correct every time; a change that adds one is a finding.

## Report shape

The summary follows `templates/review.md` (`Review: <change or plan>, <intensity>, round <n> of 3`). Per `engines/common.md`: the verdict or call first, one line per change or comment (`self`: per-round findings, tests, node table with cost). Then the claims ledger, approach-level findings apart, disagreements left open after the refuter exchange, decisions that may be wrong, what was not checked, anything open with your position. `epic` adds the seam table. Before anything ships under the owner's name: the three lines.
