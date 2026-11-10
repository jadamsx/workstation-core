# Engineering standards

## Build ladder
Understand the flow first, then stop at the first rung that holds: needed at all, already in this repo, stdlib, native platform feature, installed dependency, minimum code. A bug fix goes in the shared function after grepping every caller. Non-trivial logic leaves one runnable check.
Never simplify away: validation at trust boundaries, data-loss handling, security, accessibility, anything the owner asked for.

## Architecture
- SOLID, DRY, YAGNI. Composition over inheritance.
- Decouple business logic from transport and storage. Adapters only when they improve clarity.
- No speculative generalization. Abstractions proportional to current complexity.

## Code quality
- Write code a senior engineer would merge with minimal comments. Clarity over cleverness.
- Preserve existing project conventions unless there is a strong reason not to. Minimize diff size.
- Explicit data flow over hidden state. Small, focused functions.

## Python
- Mandatory type hints. Explicit, readable control flow. No unnecessary async.
- Centralize prompts and configuration. Use `uv` to run Python.

## Errors
- Fail fast. Domain-specific exceptions. Never swallow an exception silently.

## Documentation
- Google/ReST docstrings for public APIs and classes.

## Comments
- Self-explanatory code first. A comment explains WHY, never WHAT.
- No tutorial-style or AI-style comments, no TODOs unless asked, no ticket or ADR references.

## Testing
- Add to the existing test file. Short test names that say the behaviour.
- Bugfix tests and do-nothing proofs: `disciplines/tdd.md`.
- A route, component or user-visible flow gets driven with playwright: `checklists/ui-verify.md`.

# Prose for humans
Applies to everything a colleague reads: comments, docstrings, commits, changes, reviews, docs, chat messages, tickets.
- Process: `engines/write.md`. Rules: `checklists/prose.md`. Load `house-style` before anything longer than a couple of sentences.
- Plain English first. If "explain it like I'm 5" would be needed, the first pass was wrong.

# Working method

## Search
- Concepts ("where/how does X work", behaviour with no known name): `grepai search "<question>"` run inside a fresh main checkout of the repo (not your branch), then open that path in your worktree and `rg` there for current content. Exact names and strings: `rg`. Structure: `ast-grep`. If `grepai search` errors, fall back to `rg` once.
- Notes: `rg` `${NOTES_DIR:-~/notes}`, read the area index, then `grepai search` in that dir. A note marked stale or verified long ago is a lead, not a fact.
- Anything across many files goes to `code-locator`. Targeted search over whole-file reads; ranges over whole files.

## Common rules
Git and worktree safety, gates, delegation, the model rule and the report shape: `engines/common.md`.

## Context
- Output likely to exceed 50 lines goes through a sandboxed executor or `head`/`grep`. Big MCP results: minimal fields.
- Smallest read that answers. No re-reads. Batch independent calls. Stop when the task is done.

## Compact instructions
When summarising, always keep:
- The plan note path, the current wave and node.
- Open review findings, each with its file:line.
- Every standing instruction or "never do X" given this session, verbatim.

## Notes
- Before platform, tooling or process work, read `${NOTES_DIR:-~/notes}/index.md` and `grepai search` the vault; cite what you used.
- Anything readable (plans, designs, decisions, research) goes to `${NOTES_DIR:-~/notes}` through `notes-write` as a refactor. `${DRAFTS_DIR:-~/drafts}` holds agent artifacts only, under `projects/<slug>/<ticket-or-topic>/`; notes go under `projects/<slug>/`, `<slug>` from `current-project`. No new top-level folders in either.

## Before building anything
Answer the five questions in `checklists/design.md` section 0, one sentence each with a `file:line`, `N/A` plus why, or `unknown`. `unknown` blocks.
