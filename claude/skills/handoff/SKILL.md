---
name: handoff
description: Write a handoff file for the next session, or read one in and resume. Use when context is full, for /handoff, or to continue earlier work ("read in", "resume").
---
## When
Write: context is filling, the session ends mid-task, or "hand over", "save context". Read: a new session continues earlier work. Mode comes from the request; unclear, ask once.

## Inputs
Write: the session itself. Read: optionally a filename, path or part of a slug; otherwise the newest files are offered. Files live in `${DRAFTS_DIR:-~/drafts}/handoffs/`.

## Differs
Write:
1. Gather, read-only, silent (`change-reader` for any ticket or change whose state is needed): the goal in the owner's words; every decision, answer, preference; work done, failures, open questions; working dir and, in git, root, branch, short `HEAD`, `git status --short`; design notes touched under `${NOTES_DIR:-~/notes}/projects/*/designs/`; artifact paths written under drafts; ticket, change, doc and chat references verbatim; the last result of each verification command; any file in drafts modified today that the session did not reference.
2. Keep a line only if without it the next agent would do the wrong thing, redo work, retry a failed approach or re-ask an answered question. Unsure: one multi-select `AskUserQuestion`, one option per item. Omit narration, facts one cheap command returns, restated linked content (link it), generic advice.
3. Write `<YYYY-MM-DD>-<slug>.md` per `engines/write.md` (kebab-case, two to five words; on a clash append `-2`; create the directory; stop if not writable). Every linked path must exist. One fact per bullet, exact paths, commands and error text. Next action step 1 is startable without a question. Sections in order, empty is `- none`: header (Date, Working dir, Repo with branch and HEAD, Uncommitted), Goal, Linked artifacts (read in full; source of truth for design and scope), Decisions (settled, do not re-ask), Preferences and constraints, State (Done, In progress with where it stopped, Not started), Verification (`<command>` → pass or fail with the key line), Dead ends (do not retry), Open questions (with a recommendation), Next action. Title line: `# Handoff: <work>`.

Read:
1. Choose the file. A name matching once is used. Otherwise `ls -1t` the directory; with none, say `No handoff files in ${DRAFTS_DIR:-~/drafts}/handoffs/. Run /handoff in the old session first.` and stop. Offer the newest four with `AskUserQuestion`, single-select, newest first and recommended, label the filename, description `<title>, <working dir>`. Ask even for one; never load silently or print the listing as prose.
2. Read the handoff and every Linked artifact in full, silently. A missing path is noted, not searched for.
3. Check drift, read-only (`change-reader` when a change is named): working dir, branch, HEAD, uncommitted against the header, one line per mismatch. Never switch branch, stash, reset or edit to fix one.
4. Brief, then ask `Continue with the next action?` (`continue` recommended, `something else`). `continue` starts the action in the same turn; `something else` waits. Start no work before the answer.

After reading: Decisions are settled unless repo state contradicts one (name both). Preferences apply throughout; never retry a Dead end unless asked. Ask only about Open questions or gaps. Handoff and design disagree: design wins for design and scope, handoff for current state; name it in one line.

## Output
Write: `Handoff written: <file>`, `Path:`, `Linked: <N> design note(s), <N> artifact(s)`, `Resume in a new session with: /handoff`.
Read: `Loaded`, `Goal`, `State: <done> done · <in progress> · <not started> not started`, `Read: <N> linked artifact(s)`, `Missing`, `Drift`, `Open questions: <count>, <first>`, `Next action`; omit empty lines except Next action.
