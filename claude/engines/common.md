# Common rules

Engines and main threads load this file. Agents load `agent-core.md`. The shell rules, the findings file and the report skeleton are defined there and apply to engines too.

## Gates
- Nothing is posted, pushed, moved, approved or merged without the owner's OK. A `herdr-manager build <plan>` hand-off pre-approves the worker's pushes and draft MRs, and posting a fix plan's replies and resolving its fixed threads. Merge only when the owner explicitly asks, each time; a yes to the review's post-and-approve question covers approving, never merging; the permission prompt still applies. "Approve" means only the changes your verdict marked `approve`, one at a time; ask again if facts changed since the verdict. Exception: replies and resolves in threads on our own change go out after the push, no second OK.
- An OK covers the items shown when it was given. It does not carry over to later items or later rounds.
- Exceptions, each defined in `engines/ship.md`: tracker moves for your own work, one unasked rewrite of your own change's description in a ship run, and re-requesting review on your own change once per new head sha.
- Anything that needs an OK goes under `## Out` in the report. One ask, at the end.

## Delegation
Lead and work roles are defined in `templates/lead-brief.md` and `templates/manager-brief.md`; each space has `◆ lead` and `▸ work`, made by `herdr-manager setup`. A skill that points here and runs in a lead is handed to the work tab as the lead brief says.

Agents are optional: use one only when it saves context or time.

Rules for any main thread:
- Main-thread edits go to `builder` or `builder-small` when they save context or time (`one-file` for 1-2 files, `node` for a plan node; see `engines/build.md`). Runs, review, research and tracker reads follow the same rule. Small checks run inline.
- Agents never dispatch other agents.
- A subagent copies a brief literally and does not expand variables. A brief that names the vault or the drafts dir carries the resolved absolute path (`printenv NOTES_DIR`, empty means `~/notes`; `printenv DRAFTS_DIR`, empty means `~/drafts`), never the `${...:-...}` form.
- Brief typed agents with one bounded task each; a job too big for one is split.
- Heavy test runs (`pytest -n`, `playwright test`, full JS suites, production builds) use at most 4 workers, never `-n auto`, one run per session at a time, in the background; never start a second suite in another worktree while one is running.
- Parallel workers only when the owner asks, or for parallel ready nodes in a build. Add a review round, plan or second agent only for the failure mode it covers.
- A claim that rests on something an agent read gets read by the main thread before it acts. Weigh every agent finding for realism, say which you accept and why, never relay a verdict verbatim.

## Glossary
- **owner**: the person you work for. The only source of an OK.
- **change**: one reviewable unit on the source control host, with its diff, description and discussion. Name it "change" everywhere outside `engines/ship.md`.
- **design note**: the note that records the approved design, scope and node table for one piece of work. `engines/plan.md` calls it the plan note.
- **decision record**: an accepted architecture decision. Cited in changes and notes, never in code comments.
- **default branch**: the repo's base branch, read from `git symbolic-ref refs/remotes/origin/HEAD`, never assumed `main`. `origin/<base>` is its remote ref.
