# Review engine

Review from the code, not the diff text. Verify every finding twice, once yourself and once by an agent that did not write it. Git safety, gates, delegation, model, report skeleton and agent refusals: `engines/common.md`. Every source control call: `engines/ship.md`. Checklists hold the items: `checklists/review-core.md`, `review-domain.md`, `design-review-shared.md`, `design.md` for plan mode, `ui-verify.md` for UI, plus any domain checklist the team registers.

The failure this engine prevents: a plausible finding, posted, that the code does not support. A wrong comment costs the author more than a missed one.

## Params

| Param | Values |
|---|---|
| `mode` | `self`, `change`, `epic`, `comments`, `plan` |
| `intensity` | `light`, `medium` (default), `intense`; `recheck` is a flag on `change` |
| `target` | branch, change URL, epic key, list of URLs, pasted comments, ticket or doc |

## Modes

| Mode | Subject | Findings go to |
|---|---|---|
| `self` | your own branch; diff `git diff origin/HEAD...HEAD` plus uncommitted; no pin, no size check | fixed in the code, every severity in round 1; posts nothing |
| `change` | someone else's change, pinned | drafts, cut, shown to the owner, posted after their OK |
| `epic` | each change of an epic, as `change` | as `change`, then the cross-change pass |
| `comments` | other people's review comments, pinned as `change` | chat only |
| `plan` | a ticket, epic or plan before anyone builds, against the code off `origin/<base>` | a local draft; never edits the thing reviewed |

### Mode `self`

Tick the design note's Progress lines as steps pass. Without a ticket the run stops after the report: no description, no push, no CI loop.

0. For a `format: v2` note, fill each Traceability row's Status from real runs via `run-digest`; flag every FR without a passing test, test with no FR, and node whose diff left its `owns`.
1. Area index, a final pass over the whole diff per "Intensity", then the merge-time rows of "Post-completion checks" for each plan field that is set.
2. Gates through `run-digest`; `comment-cutter` over the branch diff.
3. Out: change description (`engines/write.md`), open it, CI loop; ticket drafts are one list, asked once.
4. Record the design note (`status: shipped`, change link, Decisions as built) and project index; report each FR's Status for a v2 note.

Any source change after the final pass goes back through this mode before the push.

### Mode `change`

Optional review note `${NOTES_DIR:-~/notes}/projects/reviews/<repo>-<number>.md` with `reviewed_sha`, `verdict` and one line per posted thread.

`medium`: `cold-reviewer` with `description.md`, then the findings filter. `light`: one finder, no filter. Both skip the area index, ledger, approach pass, merge-time checks and `comprehension-cutter`. Read the cited code yourself for anything Blocker or Refuse. A control missing from this repo may live in the caller, gateway or shared library.

`intense` adds those steps; it costs 50 to 100 times `medium`: use it when the owner asks, or offer it for auth, migrations, money or public contracts. Its approach pass: read the whole ticket and description; does the premise hold and the bug reproduce by the path a caller takes; does the control run or is it only declared; does the work already exist in a sibling repo. Name approach-level findings in the report.

Recheck runs only on the owner's request, for a note with a `reviewed_sha`. Same head: report thread state only. Otherwise `diff.patch` is `reviewed_sha..head`, one hunt round, and `finding-refuter` in fix-check mode rules each open thread of yours. Propose per thread: resolve, edit my note, reply (only when someone wrote after my last note), or leave.

### Mode `epic`

`change-reader` for the epic and children. Each change through `change` in parallel, one `finding-refuter` over all findings. Seam pass: `approach-reviewer`, `design-gap-finder`, `caller-mapper`, `claim-prover`; each seam names its owner change, a safe merge order, and what is inert until another change lands. Show the owner the three lines, drafts and epic table; post per change after their go. After every change merges, run the epic column of "Post-completion checks" on merged main.

### Mode `comments`

A reviewer's comment is a claim about the code, checked like a finding. It hunts nothing new.
1. Collect the comments, pinned head, description, ticket and linked designs. Write `decisions.md`: the plan's `Decided:` lines, the description, the author's earlier replies.
2. `finding-refuter` gets the comments as drafts in `comments.md` with `brief.md`, `decisions.md` and `diff.patch`, and no opinion of yours.
3. Confirm every verdict in the code yourself; `claim-prover` runs what needs a run. True is not the same as belongs here: scope creep and pre-existing issues become a follow-up ticket; a comment against a decision is declined citing it, unless it brings evidence the decision lacked.
4. Report per comment: verdict with `file:line`, severity, outcome (fix, follow-up, or decline with a reason) and a drafted reply per `checklists/prose.md` §7. 

### Mode `plan`

Judges whether work should be built at all and whether the plan survives contact with the code. Output is a draft for a human to send; never modify the ticket, epic or doc under review.

1. The five answers (`checklists/design.md` §0) by the main thread; `unknown` blocks.
2. `premise-attacker`, fresh, given the ticket only.
3. `approach-reviewer` and, independently, `design-gap-finder`; neither sees the other's findings.
4. Verify every finding against the code yourself; one without a file and line is dropped.
5. Report shorter than the plan: the call (build, build reduced, don't); wrong premises first; per-ticket rollup; what is missing; sequencing; the dissenting case.

Rounds per "Intensity", up to 3, stopping on `CONVERGED`. Fresh agents each round, given the ticket, the plan and every `Decided:` item, "attack how, never whether"; each prompt carries the bar: a citation read, a change to the design, not a `Decided:` item, at most five findings or exactly `CONVERGED`. Triage each round into verified, housekeeping, drop and unverified; a real fork goes to the owner. Lanes: `engines/plan.md` "Converge".

## Vocabulary

| Label | Covers | `self` | `change` |
|---|---|---|---|
| Blocker | wrong behaviour, security hole, data loss, broken contract, a test that proves nothing about the fix, a comment the change made false | fix before push | blocking thread |
| Refuse | too big to review, or mechanical churn burying the change | split before push | ask for a split |
| Should-fix | quality a senior engineer would stop at | fix before push | non-blocking |
| Nit | style, naming, wording | round 1 fix | non-blocking, batched |

Quality findings are never dropped on someone else's change, only labelled non-blocking.

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
| Hunt | `cold-reviewer`, `clean-code`, `test-gap-auditor`, `miss-hunter` (one round only); `security-reviewer` when routes, auth, input, secrets or permissions are touched |
| Approach | `approach-reviewer`; `premise-attacker` when the change produces a number |
| Score, refute | `finding-scorer` per findings file, `finding-refuter` per change |
| Cross-change, claims, pipeline | `design-gap-finder`, `caller-mapper`, `claim-prover`, `run-digest` |

Hunt lanes follow `checklists/review-core.md` numbers: `cold-reviewer` §0, 1 (not proportional abstraction), 2, 8, 9, 10-15, 17; `clean-code` §3-6; `test-gap-auditor` §7, 16; `miss-hunter` the whole checklist, independently.

On others' changes `test-gap-auditor` trusts a green CI run and runs nothing; mutation only for trust-boundary guards, at most 5 mutants and 10 minutes, on a scratch copy. `finding-refuter` may run one targeted test, capped at 5 minutes; otherwise its ruling is partial. In `self`, mutation and tests stay.

### Findings filter

1. `finding-scorer` scores each finding 0 to 100 for confidence that it is real and in scope. Under 80 is dropped. A finding proven by running code skips scoring.
2. `finding-refuter` runs only on Blocker and Should-fix survivors, the main thread's own drafts included.
3. One exchange per disagreement, then it goes to the coordinator in the report with both positions.

## Briefing

Every agent gets the diff, the full ticket, repo path, its `CLAUDE.md`, any decision record that applies and, on a change, the pinned worktree paths and SHAs, all as files in the scratch dir. Never the author's or main thread's reasoning, the plan, earlier rounds' findings, other agents' findings, or the change's threads.

| Agent | On top of the base | Withheld |
|---|---|---|
| `cold-reviewer`, `clean-code`, `test-gap-auditor` | claims ledger, description | none |
| `miss-hunter` | none | description and ledger |
| `finding-scorer` | one findings file | everything else |
| `finding-refuter` | findings to refute, the ledger; in fix-check mode the previous confirmed findings and the fix delta | none |

Decisions: code reviewers of our own work (`self`, node review, a change of ours) also get `decisions.md`, the plan's `Decided:` lines only, no reasoning. A finding that contradicts a listed decision is dropped unless it states a fact the decision did not know; such a finding goes to the coordinator once as "decision X may be wrong because Y". Each ruling the coordinator or owner makes on a finding is appended to `decisions.md`, so later rounds cannot raise it again. Reviews of other people's changes get no plan.

## Scratch dir

`${DRAFTS_DIR:-~/drafts}/reviews/<repo>-<iid>/`, never committed: `diff.patch`, `files.txt`, `ticket.md` verbatim, `description.md`, `ledger.md`, `main-drafts.md`, `decisions.md`, `brief.md` (goal, repo path, SHAs, worktree paths, those files except description and ledger, and the rules: never edit pinned worktrees, never post, write findings to your path), and `<agent>[-<angle>]-<round>.md`. Self round 1 diffs `origin/HEAD...HEAD` plus uncommitted, later rounds from the last reviewed sha.

Spawn prompt: `Read <dir>/brief.md. Your findings path is <dir>/<agent>-<round>.md.` Agents return only the path, counts by severity and the top finding. 

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

## Intensity

One scale for every mode, node review and skill; nothing else decides depth.

| Level | Finders | Filter | Rounds |
|---|---|---|---|
| `light` | one finder | none; the main thread reads the cited code for anything Blocker | 1 |
| `medium` | `cold-reviewer` | scorer, then refuter | up to 3 |
| `intense` | in parallel `cold-reviewer`, `clean-code`, `test-gap-auditor`, `miss-hunter`, plus `security-reviewer` when auth, input, secrets or permissions are touched | scorer, refuter; `comprehension-cutter` on posted comments | up to 3, all finders each round |

Plan finders: `light` `premise-attacker`; `medium` plus `approach-reviewer`; `intense` adds `design-gap-finder` and a `researcher` decision-record sweep. `comments`: `finding-refuter` only; `intense` adds `claim-prover` runs.

Round 1 is the full review; round 2 a fix-check on the fix delta; round 3 a final scan of the whole diff. Stop after any round with zero Blocker and zero Should-fix. In `change` and `epic` round 1 is the review.

The owner's argument wins. Otherwise a node reviews at the `intensity` in the plan's node table (`engines/plan.md`) and the `self` review uses the highest; no plan means `medium`. Post-completion in `self`: none at `light`, at `medium` when the plan field is set and the story touches UI, permissions or data, at `intense` per set field. `epic`: none at `light`, Y rows at `medium`, Y rows plus every set P row at `intense`.

### Rounds and caps

- Findings per agent per round, most severe first: `cold-reviewer` 10, `clean-code` 5, the others 8.
- Round 1 fixes every severity in `self`. Rounds 2+: a new finding counts only if a Blocker or Should-fix inside the fix delta; the rest is listed. Reviewers hunt in the fix delta and its callers; `miss-hunter` and `clean-code` run in round 1 only, except the `intense` round-3 scan.
- `self` exit: zero Blocker and zero Should-fix, fix-check all FIXED, tests green in that round. At the cap with open findings, give the owner each with your position and do not push.

### Node review

Round 1: the node's finders on `git diff -- <owns>`; every severity is fixed. At `light` the node stops after round 1 unless it found a Blocker. Fix rounds: reviewers see the diff since the reviewed sha plus callers, and a fix-check `finding-refuter` rules each earlier finding; a new finding counts only if a Blocker or Should-fix in the fix delta, the rest goes to a follow-up list carried into `self`. The node passes with zero open Blockers, fix-check all FIXED and its acceptance or FR tests green. A Blocker that survives the fix-round cap stops the run: ask the owner.

### Post-completion checks

Cheap first; stop at the first failure that invalidates the later ones. Y runs, P only when the plan field is set.

| Check | Agent | Plan field | Epic | UI | Perms | Data | Perf | Bug |
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

Story columns are UI, permissions, data, perf. Merge-time checks (all but regression, premise, bug re-check and the epic column) run in `self` and `change` on the branch or a local stack; the rest run in `epic` on merged main. `role-tester`, `edge-case-explorer` and `ui-verifier` write, so they run only on a local or ephemeral stack (`claude/hooks/shared-env-guard.py` blocks browser writes on hosts in `claude/hooks/shared-envs.txt`). `perf-tester` needs a stable local stack; with none it reports `skipped: no stable stack`.

## Reviewer conduct

- No author rationale to the reviewer.
- Every finding gives the file and line, what breaks, what it costs now, and the fix. A finding that could go two ways is not one yet: run it, or label the branch you believe unverified. One whose `file:line` does not resolve in the pinned tree is dropped.
- Say what you ran and what you only read.
- Agreement between reviewers is not evidence.
- Confirm: the main thread checks every survivor in the code. A runtime claim is confirmed only by running it on a scratch copy, never in the pinned worktree; settled by reading is partial at best.

## Posting rules

`change` and `epic` only. Nothing posts before the owner's OK; never approve or merge. The owner is shown the three lines (`engines/write.md`), the drafts, the anchors and per item: `new thread`, `edit my note`, `reply in my thread`, `react ➕`, `resolve` or `dropped: already raised by <author>`.

Anchor on lines the change adds, on the line that causes the finding; compute post-image numbers from the diff:

```bash
git -C $WT/head diff <base_sha>..<head_sha> -U0 -- <paths>
```

Every anchor is a post-image line of an added hunk line; check it against that output.

Before posting, re-read the discussions and re-run the triage comparison. One thread per finding, worst first. A claim one command can prove is run before it is posted; one that cannot be run is cut. A clean change gets no comment: say "clean" in chat.

Comprehension test: read each comment as the author will. The first sentence says what breaks in words they already have; evidence goes underneath. A finding you would not defend out loud is not posted. In `intense`, `comprehension-cutter` gets the drafts and the ticket only and is told that deleting a true finding is the expected outcome.

### Comment style

Register and caps: `checklists/prose.md` §7 "Review comment". Open with the observation in plain words; prefix a non-blocking point with `Nit:`. Hedge the judgement, never the fact; cite `path:line`; offer the fix as a possibility. Never defend prose the author deleted: removing a ticket ID, decision-record number, attribution or tutorial comment is correct every time; a change that adds one is a finding.

## Report shape

Per `engines/common.md`: the verdict or call first, one line per change or comment (`self`: per-round findings, tests, node table with cost). Then the claims ledger, approach-level findings apart, disagreements left open after the refuter exchange, decisions that may be wrong, what was not checked, anything open with your position. `epic` adds the seam table. Before anything ships under the owner's name: the three lines.
