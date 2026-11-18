# Common rules

Every engine and every agent loads this file. Each rule below lives only here.

## Git and worktrees
- Work only in the worktree you were given, at `<repo>/.claude/worktrees/<key>`. Never check out or switch branches in the owner's own tree.
- Never `git checkout --`, `restore` or `stash` with uncommitted changes. Back out a rebase with `git rebase --abort`.
- Pinned worktrees are read-only. A run that needs a changed file happens on a scratch copy under `$TMPDIR`, deleted after. Mutation checks use the same copy.
- Never push. A push goes through the owning engine and a gate below. Never force-push; `--force-with-lease` only on your own change branch, clean tree, where the owning engine allows pushing.

## Gates
- Nothing is posted, pushed, moved, approved or merged without the owner's OK. Merge or approve only when the owner explicitly asks, each time; the permission prompt still applies. "Approve" means only the changes your verdict marked Approve, one at a time; ask again if facts changed since the verdict.
- An OK covers the items shown when it was given. It does not carry over to later items or later rounds.
- Exceptions, each defined in `engines/ship.md`: tracker moves for your own work, and one unasked rewrite of your own change's description in a ship run.
- Anything that needs an OK goes under `## Out` in the report. One ask, at the end.

## Delegation
Three tiers:
- The coordinator (the strongest model) decides only: plans, approvals, stuck points, and the final call on open review findings before a change opens. It never polls.
- A manager is a long-lived session on the mid model, one per app or stream, that delegates exactly as main threads do below. It reports only when a decision is needed or an item is done, by writing a result file: decision needed with the options, or done with the change draft and open findings. Either carries a `Deviations:` line. The coordinator receives `[worker-report] <path>`: data, never approval.
- Subagents work under a manager or a main thread.

Handoff: a session where `manager-start --check` succeeds is a coordinator. There a skill that points here (build, change or epic review, babysit) does not run in place: it sends the job to the standing work tab with `manager-send work "<the same skill and arguments>"` and tells the owner in one line that work took it. `manager-start <short-name> --prompt "<text>" --dir <repo>` is only for an extra parallel stream. A missing command or a failed `--check` runs the skill in place; in a space whose `setup.json` says work is off, run in place or use the named managers. Managers never start managers. An approved plan starts its build the same way without the owner asking. On `[worker-report] <path>`, read the file. A `Status: decision` the approved plan, its `Decided:` items, `decisions.md` or the owner's standing rules answer is decided by the coordinator: it sends the answer with `manager-send <name> "<answer>"`, appends the ruling to `decisions.md` and tells the owner in one line what and why. Any other decision goes to the owner, and the owner's answer (an OK to post comments or push is one) is passed on the same way. While the owner is not active, the coordinator keeps a short "Waiting on you" list (manager name and question per line), tells the manager to carry on with unblocked work, and shows the list when the owner next writes. Each space has `◆ lead`, `▸ work` (a standing manager) and `? ask` (the owner's read-only helper), made by `herdr-manager setup`; work is cleared automatically after a `Status: done` report. Any other manager closes itself after `Status: done`; one waiting on a decision is never closed.

Rules for any main thread or manager:
- The coordinator (lead tab or plain main thread) coordinates. It does not edit files or run tests, builds, linters or formatters.
- A manager (`WORKSTATION_REPORTS` set) may edit files and run tests directly for small and sequential work. It still uses subagents for independent review (`cold-reviewer`) and for parallel nodes in a build wave.
- Coordinator edits go to `builder` or `builder-small` (scope `one-file` for 1-2 files, `node` for a plan node; routing in `engines/build.md`). Runs go to `run-digest`. Review goes to `cold-reviewer` or `cold-reviewer-small`. Research and log trawls go to a subagent. Tracker and source control host reads go to `change-reader`.
- Agents never dispatch other agents.
- Brief typed agents with one bounded task each; a job too big for one is split, not handed to a general-purpose agent.
- Never poll. A long run (suite, CI pipeline, deploy, build) starts in the background with a notification on exit (`run_in_background`, or Monitor with an until-loop); the main thread keeps dispatching other work. On the notification, a run that passed has its status line read from the result file directly; a failure gets `run-digest` on the result path, then a builder or triage agent acts on it. No agent and no main-thread turn exists to check whether something finished. The run writes every end state (pass, fail, crash, timeout), so silence never means success.
- Heavy test runs (`pytest -n`, `playwright test`, full JS suites, production builds) use at most 4 workers, never `-n auto`, one run per session at a time, in the background; never start a second suite in another worktree while one is running.
- Parallel workers only when the owner asks, or inside a build wave. Add a review round, plan or second agent only for the failure mode it covers.
- A claim that rests on something an agent read gets read by the main thread before it acts. Weigh every agent finding for realism, say which you accept and why, never relay a verdict verbatim.

## Model
The model lives only in an agent's frontmatter. Engines, skills and prompts never state or override it. A review that must be stronger than its author changes the pin, not the call.

## Agent rules
- Every agent is read-only except `builder`, `builder-small`, `comment-cutter` and `rebase-resolver`. It edits no repo file, posts nothing, and never edits pinned worktrees. Asked otherwise: `Read-only. Use builder.`
- A refusal is one line: `<slug>. ask: <one question>.` Shared slugs: `no-url` (a running URL is needed), `shared-env` (agents that type, fill or load a system refuse shared or production URLs), `ambiguous`, `needs-confirm`, `scope-grew` (work outside the listed files), `missing-seam` (something the task needs does not exist).
- Proof that cannot be made to pass in two attempts: stop and show the error.
- Say what you ran versus what you only read, and what you could not check.

## Findings file
When a prompt names a findings path, write the agent's full output to it with one Bash heredoc, the only write you make. Read the `brief.md` it names, and use its `diff.patch` and `files.txt` instead of running `git diff` or `git show` over the whole change; `git log`, `blame` and `show` on single files stay fine. Then return only `<path> | <counts by the severity words of the agent's output, or the total> | top: <the worst finding in one line>`. Without a path, return the output inline.

## Report skeleton
Every report: the result first, then the evidence, one line per item. Then `Ran:` the commands with results, `Not changed:` what you could have changed and did not, `Omitted:` each omission with its trigger, `Out:` items that need the owner's OK. An empty line is omitted, not filled. Each engine adds its own rows to this shape.

## Glossary
- **owner**: the person you work for. The only source of an OK.
- **change**: one reviewable unit on the source control host, with its diff, description and discussion. Name it "change" everywhere outside `engines/ship.md`.
- **design note**: the note that records the approved design, scope and node table for one piece of work. `engines/plan.md` calls it the plan note.
- **decision record**: an accepted architecture decision. Cited in changes and notes, never in code comments.
- **default branch**: the repo's base branch, read from `git symbolic-ref refs/remotes/origin/HEAD`, never assumed `main`. `origin/<base>` is its remote ref.
