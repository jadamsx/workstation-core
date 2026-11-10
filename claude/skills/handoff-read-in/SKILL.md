---
name: handoff-read-in
description: Load a handoff file from ${DRAFTS_DIR:-~/drafts}/handoffs/ into this session and resume without re-asking settled questions. Use at the start of a continuing session or for /handoff-read-in.
---

## When
A new session continues earlier work: "read in", "pick up the handoff", "resume", "continue from last session". The file comes from `handoff-write`.

## Inputs
Optionally a filename, path or part of a slug. Otherwise the newest files are offered.

## Differs
1. Choose the file. A named file that matches once is used. Otherwise `ls -1t ${DRAFTS_DIR:-~/drafts}/handoffs/*.md`; with none, output exactly `No handoff files in ${DRAFTS_DIR:-~/drafts}/handoffs/. Run /handoff-write in the old session first.` and stop. For the newest four, read the `# Handoff:` title and `Working dir:` line and ask with `AskUserQuestion`, single-select, newest first and recommended, label the filename, description `<title>, <working dir>`. Ask even for one file. Never load the newest silently or print the listing as prose.
2. Read silently the handoff and every path under Linked artifacts, in full. A missing path is noted; no replacement is searched for.
3. Check drift, read-only (`change-reader` when a change is named): compare working dir, branch, HEAD and uncommitted changes with the header, one line per mismatch. Never switch branch, stash, reset or edit to fix one.
4. Brief the owner, then ask `Continue with the next action?` with `AskUserQuestion` (`continue` recommended, `something else`). `continue` starts the action in the same turn; `something else` waits. Start no work before the answer.

Rules for the rest of the session:
- Every Decision is settled; revisit one only when repo state contradicts it, naming the entry and the contradiction.
- Preferences and constraints apply throughout. Never retry a Dead end unless the owner asks.
- Ask only about Open questions or what neither the handoff nor its artifacts cover.
- Handoff and a linked design disagree: the design wins for design and scope, the handoff for current state. Name the conflict in one line.

## Output
This block only, omitting lines with no content except Next action:
```
Loaded: <filename>
Goal: <one line>
State: <done count> done · <in-progress item> · <not-started count> not started
Read: <N> linked artifact(s)
Missing: <path>
Drift: <mismatch>
Open questions: <count>, <first question>
Next action: <step 1>
```
