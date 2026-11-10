---
name: reflect
description: Mine this session for reusable procedures, corrections and knowledge, and propose skill, CLAUDE.md or memory updates without applying them. Use for /reflect or at the end of substantial work.
---

## When
End of substantial work, or on a CI failure, a human review comment, or the same correction given twice. Once per ticket, never per step. On ticket close, move what is still true into the vault with `notes-write`; drafts stay scratch and are never bulk-migrated.

## Inputs
This session. If `node-index` is installed, `node-index report --min 3` gives measured recurrence (signatures are `kind | actor | normalised-title`); without it, count from the session.

## Differs
Propose, never impose: nothing is written before the owner approves, except trivial memory notes.

Mine for:
1. Repeated procedures (2+ times this session, or clearly in past ones): a skill candidate. Three occurrences is the bar when measured; under it, leave it alone.
2. Corrections to approach, style or a wrong assumption: a `CLAUDE.md` line (project-level if repo-specific, global if universal).
3. Environment facts found the hard way (hosts, ports, auth quirks): `CLAUDE.md` or memory.
4. Dead ends and why, so they are not retried.

| Candidate shape | Verdict |
|---|---|
| Fixed sequence of commands, no judgement | `script`, in the owning repo's `scripts/` |
| Knowledge, ordering, gotchas, a checklist | `skill` |
| Same delegated prompt each time, varying target | subagent prompt template |
| Recurs but every instance differs materially | leave manual, say why |

Once built, stop it resurfacing: `node-index mark '<signature>' --status extracted --note '<path>'`.

| Kind | Lands in |
|---|---|
| Repeatable procedure | a skill (`templates/skill.md`; `~/.claude/skills/<name>/` cross-project, `<repo>/.claude/skills/` repo-specific) |
| Convention true for every task in the repo | `CLAUDE.md`, one line each |
| A correction, with its reason | `memory/feedback_*.md` (`templates/memory.md`) |
| Ongoing work, goals, constraints | `memory/project_*.md` |
| External pointer: URL, dashboard, ticket | `memory/reference_*.md` |
| Ticket artifacts: logs, screenshots, output | `${DRAFTS_DIR:-~/drafts}/projects/<slug>/<topic>/` |
| A ticket's plan, design, decisions, or durable knowledge from a closed ticket | the vault, through `notes-write` |

Never in memory what the repo already records (code structure, past fixes, git history, `CLAUDE.md`); save what was non-obvious about it instead. Update an existing file rather than duplicate; delete memories that proved wrong; absolute dates; one line per memory in `MEMORY.md`. Prose per `engines/write.md`. After writing a skill, tell the owner its trigger phrase.

## Output
At most 5 items, `[skill|claude-md|memory] one-line description: why it is worth saving`. An empty list is valid. Then ask which to write.
