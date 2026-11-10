---
title:
aliases: []
type: design
status: proposed
format: v2
ticket:
project:
date:
superseded_by:
change:
area:
updated:
verified:
sources: []
decided_by: []
implements: []
supersedes: []
related_adrs: []
---
# Title as a claim

## Context and scope
What exists today, with `file:line`, and what this covers. Say what is out of scope.

## Goals and non-goals
Goals as outcomes. Non-goals are things that could reasonably have been goals.

## Design
The verdict, the chosen approach, diagrams and the trade-offs that matter. Length follows importance; no pasted schemas.

## Alternatives considered
Each option and what made it lose.

## Cross-cutting concerns
Security, ops and rollout, in prose. The plan fields that apply (`roles`, `hot_path`, `migrations`, `flags`, `signals`, `frames`) stay in the Plan header as tags for the review agents.

## User Scenarios & Testing
Prioritised user stories, each independently testable. Edge cases at the end.

### User Story 1 - Title (Priority: P1)

Plain-language journey, why it has this priority, and how it is tested alone.

**Acceptance Scenarios**:

1. **Given** initial state, **When** action, **Then** outcome

### Edge Cases

- What happens when a boundary is hit?

## Requirements
One line each. Mark open questions `[NEEDS CLARIFICATION: question]`; none may remain at approval.

### Functional Requirements

- **FR-001**: System MUST do the specific thing

### Key Entities

Only when data is involved: each entity and what it represents, without implementation.

## Success Criteria
Measurable and technology-agnostic.

### Measurable Outcomes

- **SC-001**: A measurable result

## Plan header
One field per line: size, repos, plan skill, `vault`, then the plan fields the work touches (`risk_flows`, `roles`, `hot_path`, `migrations`, `frames`, `flags`, `signals`, `deps_added`). Empty means skipped.

## Node table
One row per node. `covers` lists the FR ids the node delivers; every FR is covered by at least one node and every node covers at least one FR.

| Node | Agent | Discipline | Owns | Wave | Intensity | Review | Acceptance | Covers |
|---|---|---|---|---|---|---|---|---|
| N1 | | | | 1 | | | | FR-001 |

## Progress
One line per node, then the ship steps: `- [ ] N1 <title>`, `- [~] N2 <title>` in progress, `- [x] N3 <title>` done, then `- [ ] review`, `- [ ] change`, `- [ ] CI green`. Written when the plan is approved.

## Traceability
Every FR and SC, the nodes that cover it and the test that proves it; for an SC the agent its plan field triggers (`perf-tester` via `hot_path`) counts. Status is `open`, `pass` or `fail`, filled from the real test runs.

| Req | Nodes | Test | Status |
|---|---|---|---|
| FR-001 | N1 | | open |
| SC-001 | N1 | `perf-tester` (via `hot_path`) | open |

## Decisions
Choices made at planning and during the build, each with the question asked and why. Rules the owner gives mid-session go here too, starting `Standing:`.

## Traps
Filled at ship: what bit during the build and the area note that now carries it.

## Out
Actions waiting for the owner's OK, sent once at the end: none.

## Links

Built to satisfy `[[decision-note]]`, which fixed the access model this design relies on.
