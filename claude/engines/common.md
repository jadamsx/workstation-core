# Common rules

Engines and main threads load this file. Agents load `agent-core.md`. The shell rules, the findings file and the report skeleton are defined there and apply to engines too.

## Gates
- Nothing is posted, pushed, moved, approved or merged without the owner's OK. Merge only when the owner explicitly asks, each time; a yes to the review's post-and-approve question covers approving, never merging; the permission prompt still applies. "Approve" means only the changes your verdict marked `approve`, one at a time; ask again if facts changed since the verdict.
- An OK covers the items shown when it was given. It does not carry over to later items or later rounds.
- Exceptions, each defined in `engines/ship.md`: tracker moves for your own work, and one unasked rewrite of your own change's description in a ship run.
- Anything that needs an OK goes under `## Out` in the report. One ask, at the end.

## Delegation
Two roles:
- The lead (the strongest model) plans, answers the work tab's questions, and owns the final whole-change self-review. It never polls.
- The work tab (the mid model) owns the plan, builds it and delegates exactly as main threads do below. It asks the lead only for a decision beyond the plan, with `herdr agent prompt $WORKSTATION_LEAD_PANE "question: ..."`, and sends `done, check <plan path>` when every node is green.

In a lead, a skill that points here (build, change or epic review, comment review, babysit) does not run in place: the lead clears the work tab and hands it the plan with a plain `herdr agent prompt` that starts with a re-read of the work brief, and tells the owner in one line that work took it. With `WORKSTATION_ROLE=lead` set the skill refuses; the gate only blocks the lead's file edits. Each space has `◆ lead` and `▸ work`, made by `herdr-manager setup`.

Rules for any main thread:
- The lead does not edit files or run tests, builds, linters or formatters.
- The work tab may edit files and run tests directly for small and sequential work. It still uses subagents for independent review (`cold-reviewer`) and for parallel ready nodes in a build.
- Lead edits go to `builder` or `builder-small` (scope `one-file` for 1-2 files, `node` for a plan node; routing in `engines/build.md`). Runs go to `run-digest`. Review goes to `cold-reviewer`. Research and log trawls go to a subagent. Tracker and source control host reads go to `change-reader`.
- Agents never dispatch other agents.
- A subagent copies a brief literally and does not expand variables. A brief that names the vault or the drafts dir carries the resolved absolute path (`printenv NOTES_DIR`, empty means `~/notes`; `printenv DRAFTS_DIR`, empty means `~/drafts`), never the `${...:-...}` form.
- Brief typed agents with one bounded task each; a job too big for one is split, not handed to a general-purpose agent.
- Never poll. A long run (suite, CI pipeline, deploy, build) starts in the background with a notification on exit (`run_in_background`, or Monitor with an until-loop); the main thread keeps dispatching other work. On the notification, a run that passed has its status line read from the result file directly; a failure gets `run-digest` on the result path, then a builder or triage agent acts on it. No agent and no main-thread turn exists to check whether something finished. The run writes every end state (pass, fail, crash, timeout), so silence never means success.
- Heavy test runs (`pytest -n`, `playwright test`, full JS suites, production builds) use at most 4 workers, never `-n auto`, one run per session at a time, in the background; never start a second suite in another worktree while one is running.
- Parallel workers only when the owner asks, or for parallel ready nodes in a build. Add a review round, plan or second agent only for the failure mode it covers.
- A claim that rests on something an agent read gets read by the main thread before it acts. Weigh every agent finding for realism, say which you accept and why, never relay a verdict verbatim.

## Glossary
- **owner**: the person you work for. The only source of an OK.
- **change**: one reviewable unit on the source control host, with its diff, description and discussion. Name it "change" everywhere outside `engines/ship.md`.
- **design note**: the note that records the approved design, scope and node table for one piece of work. `engines/plan.md` calls it the plan note.
- **decision record**: an accepted architecture decision. Cited in changes and notes, never in code comments.
- **default branch**: the repo's base branch, read from `git symbolic-ref refs/remotes/origin/HEAD`, never assumed `main`. `origin/<base>` is its remote ref.
