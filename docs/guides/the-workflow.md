# The workflow

Work goes plan, build, review, ship. Each stage has one engine, and each skill is a thin entry point to one of them. [Engines](../reference/engines.md) has the parameters.

## Plan

A plan is a node table: for each node the agent, discipline, files it owns, wave, intensity, reviewer and one acceptance sentence. The plan engine writes it, a plan review attacks it, and you approve it. Review intensity (`light`, `medium`, `intense`, default `medium`) sets how hard the plan and each node are reviewed. Name a level to override it.

| Skill | Use it for |
| --- | --- |
| `plan-task` | A bounded change with a known shape |
| `plan-bug` | One defect: reproduce first, find the root cause and every caller |
| `plan-spike` | A time-boxed question |
| `plan-story` | One story that touches several files or an interface |
| `plan-epic` | A whole epic: premise attack, flow diagram, ticket table |
| `plan-fix` | The response to human review comments on your change |
| `verify-plan` | An attack on a ticket or plan someone else wrote |

## Build

`build` takes an approved plan and runs its nodes in worktrees, wave by wave. `builder` edits, a cold reviewer checks each node at its boundary, and the discipline a node names (tdd, refactor, migration and others) sets how it proves the node done. A last gate runs the whole suite once, then each stated behaviour is run against the real thing.

## Review

| Skill | Reviews | Posts |
| --- | --- | --- |
| `verify-self` | Your own branch, then fixes it | Nothing |
| `verify-change` | Someone else's change | Findings, after your OK |
| `verify-comments` | Other people's review comments on your change | Nothing |
| `verify-epic` | Every change of an epic, then the seams | Findings, after your OK |
| `verify-plan` | A plan or ticket, before it is built | Nothing |

`verify-change` is `medium` by default. Say `light` for one finder, `intense` for the multi-agent review and `recheck` after the author pushes fixes. Every finding is checked twice, once by the main thread and once by an agent that did not write it, and only what survives is shown.

## Ship

`change-write` and `ticket-write` write the description from the repo's template. `babysit` watches the pipeline after the push, fixes valid failures and valid automated comments, and stops at green. It never merges or approves. See [automated reviewers](automated-reviewers.md).

## Around the edges

`notes-write` saves to your notes vault as a refactor of the existing note. `handoff-write` and `handoff-read-in` carry a session across a full context. `reflect` mines a session for reusable procedures and proposes updates without applying them. `debt-ledger`, `diagrams` and `house-style` stand alone. See [skills](../reference/skills.md).
