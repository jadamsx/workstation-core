# Common rules

Every engine and every agent loads this file. Each rule below lives only here.

## Git and worktrees
- Work only in the worktree you were given, at `<repo>/.claude/worktrees/<key>`. Never check out or switch branches in the owner's own tree.
- Never `git checkout --`, `restore` or `stash` with uncommitted changes. Back out a rebase with `git rebase --abort`.
- Pinned worktrees are read-only. A run that needs a changed file happens on a scratch copy under `$TMPDIR`, deleted after. Mutation checks use the same copy.
- Never push. A push goes through the owning engine and a gate below. Never force-push; `--force-with-lease` only on your own change branch, clean tree, where the owning engine allows pushing.

## Gates
- Nothing is posted, pushed, moved, approved or merged without the owner's OK. Merge or approve only when the owner explicitly asks, each time; the permission prompt still applies.
- An OK covers the items shown when it was given. It does not carry over to later items or later rounds.
- Exceptions, each defined in `engines/ship.md`: tracker moves for your own work, and one unasked rewrite of your own change's description in a ship run.
- Anything that needs an OK goes under `## Out` in the report. One ask, at the end.

## Delegation
- The main thread coordinates. It does not edit files or run tests, builds, linters or formatters.
- Edits go to `builder` (scope `one-file` for 1-2 files, `node` for a plan node). Runs go to `run-digest`. Review goes to `cold-reviewer`. Research and log trawls go to a subagent. Tracker and source control host reads go to `change-reader`.
- Agents never dispatch other agents.
- Parallel workers only when the owner asks, or inside a build wave. Add a review round, plan or second agent only for the failure mode it covers.
- A claim that rests on something an agent read gets read by the main thread before it acts. Weigh every agent finding for realism, say which you accept and why, never relay a verdict verbatim.

## Model
The model lives only in an agent's frontmatter. Engines, skills and prompts never state or override it. A review that must be stronger than its author changes the pin, not the call.

## Agent rules
- Every agent is read-only except `builder`, `comment-cutter` and `rebase-resolver`. It edits no repo file, posts nothing, and never edits pinned worktrees. Asked otherwise: `Read-only. Use builder.`
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
