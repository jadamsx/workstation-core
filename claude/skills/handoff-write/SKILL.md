---
name: handoff-write
description: Write everything the next session needs into a handoff file in ${DRAFTS_DIR:-~/drafts}/handoffs/, linking every design note and artifact. Use when context is full or for /handoff-write.
---

## When
Context is filling, the session ends mid-task, or the owner says handoff, hand over, save context or "moving to a new session". `handoff-read-in` loads the file.

## Inputs
The session itself. Unsure items are asked once in step 3.

## Differs
1. Gather, read-only, silent (`change-reader` for any ticket or change whose state is needed). Collect: the goal in the owner's words; every decision, answer and preference; work done, failures, open questions; working dir and, in a git repo, root, branch, `HEAD` short SHA, `git status --short`; every design note touched under `${NOTES_DIR:-~/notes}/projects/*/designs/`; every artifact path written under `${DRAFTS_DIR:-~/drafts}`; every ticket, change, doc or chat reference verbatim; the last result of each verification command; any file in drafts modified today that the session did not reference.
2. Classify with the inclusion test: without this line, would the next agent do the wrong thing, redo finished work, retry a failed approach, or ask what the owner already answered? Yes: include. Clearly no: omit. Unsure: ask. Always omit session narration, pleasantries, facts one cheap command returns, restated linked content (link it), generic advice.
3. Ask about unsure items once with `AskUserQuestion`: one multi-select, one option per item (label up to 8 words, one line on why it matters). Ticked and free text go in. Skip when nothing is unsure.
4. Write `${DRAFTS_DIR:-~/drafts}/handoffs/<YYYY-MM-DD>-<slug>.md` per `engines/write.md` (kebab-case slug, two to five words; on a clash append `-2`, never overwrite; create the directory). Every linked path must exist, and every design note touched is listed by vault path. Stop early if the drafts dir is not writable.

Structure, in order; an empty section is `- none`:
```markdown
# Handoff: <title of the work>

- Date: <YYYY-MM-DD HH:MM local>
- Working dir: <absolute path>
- Repo: <repo root> · branch `<branch>` · HEAD `<short sha>`
- Uncommitted: <`git status --short` lines, "clean", or "not a git repo">

## Goal
<1-3 sentences, the owner's words where possible. What done means.>

## Linked artifacts
Read these in full before acting. They are the source of truth for design and scope.
- Design note: <absolute vault path>, <one-line purpose>
- Artifact: <absolute drafts path>, <one-line purpose>
- Ticket, change or page: <verbatim ID or URL>

## Decisions (settled, do not re-ask)
- <decision>, <reason, or "owner's call">

## Preferences and constraints
- <stated preference, guardrail, or off-limits area>

## State
- Done: <item> (<path or commit>)
- In progress: <item>, <exactly where it stopped>
- Not started: <item>

## Verification
- `<command>` → <pass | fail: key error line>

## Dead ends (do not retry)
- <approach>, <why it failed>

## Open questions (need the owner)
- <question>, <your recommendation>

## Next action
1. <first concrete step: file, command or agent to dispatch>
```
One fact per bullet; exact paths, symbols, commands and error text, never a paraphrased error. Next action step 1 is startable without a question.

## Output
```
Handoff written: <YYYY-MM-DD>-<slug>.md
Path: ${DRAFTS_DIR:-~/drafts}/handoffs/<YYYY-MM-DD>-<slug>.md
Linked: <N> design note(s), <N> artifact(s)
Resume in a new session with: /handoff-read-in
```
