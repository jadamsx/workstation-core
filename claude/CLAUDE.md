# Engineering standards

## Build ladder
Understand the flow first, then stop at the first rung that holds: needed at all, already in this repo, stdlib, native platform feature, installed dependency, minimum code. A bug fix goes in the shared function after grepping every caller. Non-trivial logic leaves one runnable check.
Never simplify away: validation at trust boundaries, data-loss handling, security, accessibility, anything the owner asked for.
This codebase is yours, and you will keep building on it: merge duplicates you meet, fix related bugs and restructure what is in the way. Never add a second function beside one that already does the job. Reviews are the gate.

## Architecture
- SOLID, DRY, YAGNI. Composition over inheritance.
- Decouple business logic from transport and storage. Adapters only when they improve clarity.
- No speculative generalization. Abstractions proportional to current complexity.

## Code quality
- Write code a senior engineer would merge with minimal comments. Clarity over cleverness.
- Preserve existing project conventions unless there is a strong reason not to. Minimize diff size.
- Explicit data flow over hidden state. Small, focused functions.

## Other code rules
- Python: type hints, `uv`, configuration and prompts in one place, no unnecessary async. Google/ReST docstrings on public APIs.
- Fail fast with domain-specific exceptions; never swallow one.
- A comment explains WHY, never WHAT. No tutorial or AI-style comments, TODOs, or ticket or ADR references. No comments in config files (YAML, HCL); the reason goes in the commit message.
- Tests: add to the existing test file, short names that say the behaviour. Bugfix tests: `disciplines/tdd.md`. UI flows: `checklists/ui-verify.md`.

# Prose for humans
Applies to everything a colleague reads. Process: `engines/write.md`. Rules: `checklists/prose.md`. Load `house-style` before anything longer than a couple of sentences.

# Working method

## Search
- Concepts: `grepai search "<question>"` inside a fresh main checkout (not your branch), then `rg` the path in your worktree. Exact strings: `rg`. Structure: `ast-grep`. If `grepai search` errors, fall back to `rg` once.
- Many files: `code-locator`.
- Notes: `rg` `${NOTES_DIR:-~/notes}`, read the area index, then `grepai search` there. A stale note is a lead, not a fact.

## Common rules
Git and worktree safety, gates, delegation, the model rule and the report shape: `engines/common.md`.

## Context
Output likely to exceed 50 lines goes through a sandboxed executor or `head`/`grep`; big MCP results use minimal fields.

## Compact instructions
When summarising, always keep:
- The plan note path, the current wave and node.
- Open review findings, each with its file:line.
- Every standing instruction or "never do X" given this session, verbatim.

## Notes
- Before platform, tooling or process work, read `${NOTES_DIR:-~/notes}/index.md` and `grepai search` the vault; cite what you used.
- Readable output (plans, designs, decisions, research) goes to `${NOTES_DIR:-~/notes}` via `notes-write`. `${DRAFTS_DIR:-~/drafts}` is agent artifacts only, under `projects/<slug>/<ticket-or-topic>/` (`<slug>` from `current-project`).

## Before building anything
Answer the five questions in `checklists/design.md` section 0, one sentence each with a `file:line`, `N/A` plus why, or `unknown`. `unknown` blocks.
