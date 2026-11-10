# Write engine

Process for everything a colleague reads: change title and description, ticket, review comment, reply, chat, commit, note. The rules are in `checklists/prose.md` (killer items, §1 to §8); this file is the order of work. Gates, git safety, report and refusals: `engines/common.md`. Source control and tracker mechanics, including template paths: `engines/ship.md`.

## Params

| Param | Values | Effect |
|---|---|---|
| `target` | `change`, `ticket`, `comment`, `reply`, `commit`, `note`, `chat` | picks the register in `checklists/prose.md` §7 and the template rule below |

## Steps

1. Pick the register. One line chat: apply `checklists/prose.md` from memory. Anything longer: read it, killer items first, §7 for the register.
2. Gather facts from the finished work, not the plan you started with: the diff, the commits, the tracker key, the real state of linked changes. Never invent a key, a link or a number. A missing fact is asked for once.
3. Take the template (below), then write.
4. Check the draft against `checklists/prose.md`, quoting the numbers checked.
5. Run the three lines (below) and show them. Nothing ships before the owner's OK (`engines/common.md`), except a ship run's one unasked rewrite of its own change description (`engines/ship.md`).

## Template handling

- Read the template for this artifact type before typing (paths: `engines/ship.md`). Fill its headings verbatim: same wording, level and order. Never invent, drop, reorder or rename a section. A description that reads well and replaced the template is a defect.
- Invent a heading only when nothing in the template fits. Renaming a section is paraphrasing.
- A "Steps to test" section, when the template has one, holds the test and lint status: what ran, with results, and what could not run and why.
- Section with nothing to say: delete it, or if the template demands it, `N/A` and one clause saying why.
- No template: change gets What, Why, Risk. Ticket gets Overview, Acceptance criteria (scope lives here; say what is out and why in a line under the list; criteria name what the work must prove, not what it touches), Technical notes (cause, constraints, pointers), Notes (links, open questions). Drop any you cannot fill.
- Emoji headings only when the team template already has them, copied exactly.

## Description budget (change)

- Under 120 words in all (`checklists/prose.md` §6, the stricter of the two caps that existed).
- The "what does this do" section is bullets: one per behaviour change, not per file, four or fewer, one line each.
- At most one short paragraph after: what will bite the reviewer and the diff cannot show. Often none.
- Every other section is a line or two, or `N/A`.
- Write the bullets first, then ask what the reviewer still cannot work out. That is the paragraph.
- Check the branch is not behind its target; a stale description describes a diff nobody will merge.
- A template section asking for screenshots or output accepts a diagram block (decision below). UI change: screenshots in one table, one row per state, before and after (or design and after when a frame is linked), same width, same viewport; `N/A, new` in an empty before cell; no verdict. A change that only works or fails, like a deep link, gets no screenshots: say what was checked.

## Ticket

- Read the existing ticket first and rewrite from what the work is now. Link the parent and related tickets instead of restating them. For in-flight work, get the real state of each change; a wrong status section is worse than none.
- A ticket for in-flight work is a living document: update the status in the description when a step lands, and keep comments for conversation.
- Check before saving: would someone outside the conversation know what to do first; is every link real; does the summary say what the work achieves.

## Rewriting an existing one

Rewrite from the current state, then re-check against the template and the budget. A fix round that changed what the work does makes the description stale even when it still reads well.

## Audit mode

Asked whether a piece reads as machine-written, or to review one: quote each offending line with the rule it breaks and a fix in a few words. Do not rewrite, guess at authorship or score it. Offer the edit afterwards. Editing a draft: `checklists/prose.md` §8; return the text and one short line per non-obvious change; ask when the audience or next action is unclear.

## Diagram decision

Draw one only when the change moves a boundary: a new service call, state transition, request path or failure mode. Before and after as two blocks when it reroutes an existing flow; a bug fix earns the pair only when the bug is a route. Not for a bugfix inside one function, and not on every change.

- Name the question first: which component owns the write, what happens off the request path, which dependency is ours to trust, where does this data come from now. No one-line question, no diagram.
- Delete it if: two nodes, every arrow is a call and its reply, any node is a sentence, it restates the description, or it would be identical before and after.

## Three lines before anything ships

Nothing goes out under the owner's name unless they can explain it in one sentence. Shown to the owner, who approves these and not the full text:
1. What it claims, in plain words with no identifiers.
2. Per claim: verified by running, verified by reading, or judgement.
3. The first thing to concede if challenged.

Also: every claim true as written ("all hooks pass" is a claim, so run them); say which suites ran and which could not and why.

## Report

Per `engines/common.md`: the text, the three lines, and anything left unverified.
