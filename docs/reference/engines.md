# Engines

An engine is the full procedure for one stage of work, in `claude/engines/<name>.md`. A skill picks an engine and sets its parameters. Nothing else restates an engine's rules.

| Engine | Owns | Parameters |
| --- | --- | --- |
| `common` | Git and worktree safety, gates, delegation, the model rule, agent refusals, report skeleton, glossary. Every engine and agent loads it | none |
| `plan` | Sizing, the five design questions, the plan note, the node table, epic mode | `kind`: `task`, `bug`, `spike`, `story`, `epic`, `fix`. `intensity`: `light`, `medium`, `intense` |
| `build` | Running an approved plan's nodes in worktrees, ready node by ready node, then the whole-repo gates and proof | `scope`: `node`, `wave`, `plan`; default the whole ready graph |
| `review` | Review of your own branch, someone else's change, comments, an epic or a plan: pinning a checkout, reviewers, verification of findings, posting rules, the intensity scale | `mode`: `self`, `change`, `epic`, `comments`, `plan`. `intensity`: `light`, `medium`, `intense`; `recheck` is a flag on `change`. `target` |
| `write` | Process for anything a colleague reads: change descriptions, tickets, comments, commits, notes | `target`: `change`, `ticket`, `comment`, `reply`, `commit`, `note`, `chat` |
| `ship` | The source control adapter, the tracker, automated reviewers, the push gate, the CI loop, conflicts | `target`: a change URL, `<project> #<number>` or empty. `phase`: `open`, `loop` |

## How they fit

`plan` ends at an approved node table. `build` reads that table and refuses without it. `review` runs once per plan, over the whole branch in `self` mode; nodes get a done-check. `write` shapes every description and comment. `ship` is the only file that names a source control host or tracker, and it owns pushing.

## The common rules, in short

- Work only in the worktree you were given. Never push, never force-push outside your own change branch.
- Nothing is posted, pushed, moved, approved or merged without the owner's OK, and an OK covers only the items shown.
- The main thread coordinates. Edits go to `builder`, test runs to `run-digest`, review to `cold-reviewer`. Agents never dispatch agents.
- A model is set only in an agent's frontmatter.
- Proof that fails twice stops the work and shows the error.

The full text is `claude/engines/common.md`.

## Review intensity

Two separate dials: a plan's `kind` sizes the planning, `intensity` sets how hard any review is. Default `light` everywhere; auth, input, secrets or permissions raise it to `medium`.

| Level | What runs |
| --- | --- |
| `light` | One finder; a fix-check only if round 1 found a Blocker |
| `medium` | `cold-reviewer`; round 2 a `finding-refuter` fix-check; round 3 a quick confirmation |
| `intense` | `cold-reviewer`, `clean-code`, `test-gap-auditor` in parallel, `security-reviewer` where it applies; rounds 2 and 3 as `medium` |

A plan's node table has an `intensity` column per node. The exact rules are in `claude/engines/review.md`, section "Round shapes". Name a level in the request to override it.
