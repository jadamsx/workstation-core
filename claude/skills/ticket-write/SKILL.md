---
name: ticket-write
description: Write or rewrite a ticket's summary and description in the team's style, with what the assignee needs. Use for "raise a ticket", "draft the issue" or /ticket-write.
engine: write
params: {target: ticket}
---

## When
Raising or rewriting a ticket. Reading or moving a ticket: `engines/ship.md` (Tracker).

## Inputs
The work in plain words. The existing ticket if one exists, the parent epic and related tickets to link.

## Differs
- Register: `checklists/prose.md` §7 "Ticket". Template, fallback headings and the living-status rule: `engines/write.md`.
- Summary is a label on a board: verb, object, stop. An "and" is fine only when the work has two halves and order matters.
- The ticket template for the issue type is the one to fill (see `engines/ship.md`).
- Nothing is written to the tracker before the owner's go on the three lines (`engines/common.md`).

## Output
Summary, description, the three lines, and each link checked as real.
