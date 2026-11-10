---
name: notes-write
description: Write to the notes vault at ${NOTES_DIR:-~/notes} as a refactor: find the existing note, update it in place, fix wikilinks and frontmatter, merge duplicates. Use for any save-to-notes request.
---

## When
Anything a person might read later: plans, designs, decisions, research, runbooks, outcomes. `${DRAFTS_DIR:-~/drafts}` is agent-only scratch (screenshots, logs, eval output, raw review rounds, handoffs); a note links an artifact there by path and never copies it.

## Inputs
The content and its subject. A subject too vague to find a home is asked for once.

## Differs
Steps, in order:
1. Find the home: `code-locator` in notes mode, by filename, frontmatter title, alias, area index and body. More than one hit is a duplicate set.
2. Decide: update the existing note in place (change the lines the new content changes, keep the rest), merge duplicates into the best-linked note leaving nothing that points nowhere, or create one only when no home exists. Before updating, re-check the note's stale facts against the code and the tracker; bump `verified:` only for what was checked, else set `status: stale`.
3. Write per `engines/write.md` (register "Note"): one current statement, no append log. Copy the vault's `templates/<type>.md` (starters in `templates/`: design, proposal, review), never write from memory.
4. Repair links: `caller-mapper` finds every note linking to a merged or renamed note; repoint each at the survivor.
5. Lint and commit: run the vault's lint script on the whole vault if present; a failing lint means fix the note. Commit in the notes repo with a short message and no ticket ID. Nothing is pushed.

Two notes that disagree on a fact stop the run: ask which is right before merging.

### Where notes go
- Project streams: `projects/<slug>/<type>/`, `<type>` one of `designs`, `decisions`, `research`, `incidents`, `reviews`, created on first use; nothing else sits in a project folder. The note carries `project: <slug>`. Resolve the slug with `current-project`; none means ask once or use the top-level folders.
- Knowledge serving several streams: top-level `runbooks/`, `reference/`, `howto/`.
- Link a project as `[[projects/<slug>/index|Name]]`; every new project note is linked from that hub in a sentence saying why it matters.
- Designs: one note per ticket or epic, `<KEY>-<slug>.md`, body per `templates/design.md`. Status proposed, approved (with `date`, the gate the build reads), shipped or superseded. A replaced design stays, marked superseded and linked to its successor.

### Format
- Types: decision, design, howto, project, reference, research, review, runbook; the folder fixes the type.
- Frontmatter keys in the template's order, all present. `updated` and `verified` are `YYYY-MM-DD`. `status`: draft, current, stale, paused, superseded (design: proposed, approved, shipped, superseded). `area` names a folder in `areas/`.
- Body: one `# ` title, the template's `##` sections in order, `## Links` last with at least one linked sentence.
- Every note is linked from the root index, an area index or its project hub. The root `index.md` is an llms.txt-style index, one line per note saying what question it answers; every write updates that line.

### Links
- Every link sits in a sentence saying why the target matters. No bare "Related:" or "See also" lines, no area backlink in the body.
- Relations in frontmatter as quoted wikilinks: `decided_by`, `implements`, `supersedes`, `superseded_by`. `ticket` holds plain keys.
- Required by type: decision to its design and ticket; design to its decisions and what it supersedes; project to its decisions, designs, runbooks and reference notes; howto or runbook to the service it operates; research to what it informed; reference to the howto that uses it.
- Live facts (URLs, owners, versions) carry `sources` and `verified`; past 60 days is a lead, not a fact.
- Repo docs that change with code are linked, never copied.

## Output
Which notes changed, merged or were created, one line each, and any link that could not be fixed.
