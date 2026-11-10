---
name: debt-ledger
description: Harvest every deliberate-shortcut comment in a repo into a ledger with its ceiling and upgrade trigger, flagging the ones with no trigger. Use for /debt-ledger or "what did we defer".
---

## When
Shortcuts marked with a `ponytail:` comment (`ponytail: <ceiling>, <upgrade path>`, from the ponytail plugin by DietrichGebert) need tracking so a deferral cannot quietly become permanent. Over-engineering cleanup is not this; that is `clean-code` on a diff.

## Inputs
A repo path (default: the current repo). Optionally a ledger file to write.

## Differs
Reads and reports only; changes no code.
1. Scan with `code-locator`: `grep -rnE '(#|//) ?ponytail:' .` plus other comment prefixes for the stack, skipping `node_modules`, `.git` and build output. The prefix keeps prose that merely mentions the convention out.
2. One row per marker, grouped by file: `<file>:<line>, <what was simplified>. ceiling: <limit>. upgrade: <trigger>.` Ceiling and trigger come from the comment; `git blame -L<line>,<line>` adds a name when the owner wants one.
3. Tag `no-trigger` on every marker naming no upgrade path or trigger.
4. Write a file only when asked, to `${DRAFTS_DIR:-~/drafts}/debt-ledger-<repo>.md`.

## Output
Rows grouped by file, then `<N> markers, <M> with no trigger.`, or `No ponytail: debt. Clean ledger.` when none.
