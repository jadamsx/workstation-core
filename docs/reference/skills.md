# Skills

A skill is a slash command. Each one is `claude/skills/<name>/SKILL.md`, and most set an [engine](engines.md) and its parameters in frontmatter. A skill file says only what differs from its engine. Skills with no engine are self-contained.

The table is read from the skills' frontmatter. The parameters shown are the skill's defaults.

| Skill | Engine | Params | What it does |
| --- | --- | --- | --- |
| `babysit` | `ship` | `{phase: loop, target: current-branch}` | Drive a change to green: watch the pipeline and automated reviewers, fix what is valid, loop until clean. Use for `/babysit <url>` or after opening a change. |
| `build` | `build` | `{scope: wave}` | Execute an approved plan's node graph in a worktree, wave by wave, then hand to verify-self. Use for `/build <plan note or ticket>`. Refuses without an approved plan. |
| `change-write` | `write` | `{target: change}` | Write or rewrite a change title and description in the team's style, filling the repo template and saying only what the diff cannot. Use when opening or tidying a change. |
| `debt-ledger` | none | none | Harvest every deliberate-shortcut comment in a repo into a ledger with its ceiling and upgrade trigger, flagging the ones with no trigger. Use for /debt-ledger or "what did we defer". |
| `diagrams` | none | none | Pick the diagram type, draw it so a reviewer can object to the routing, and render it in both themes. Use when a Mermaid block is about to be written. |
| `handoff-read-in` | none | none | Load a handoff file from `${DRAFTS_DIR:-~/drafts}/handoffs/` into this session and resume without re-asking settled questions. Use at the start of a continuing session or for /handoff-read-in. |
| `handoff-write` | none | none | Write everything the next session needs into a handoff file in `${DRAFTS_DIR:-~/drafts}/handoffs/`, linking every design note and artifact. Use when context is full or for /handoff-write. |
| `house-style` | none | none | Load the writing rules before writing anything a colleague reads: tickets, change titles and descriptions, review comments, chat, docs, commits, code comments. |
| `notes-write` | none | none | Write to the notes vault at `${NOTES_DIR:-~/notes}` as a refactor: find the existing note, update it in place, fix wikilinks and frontmatter, merge duplicates. Use for any save-to-notes request. |
| `plan-bug` | `plan` | `{kind: bug, intensity: medium}` | Plan the fix for one defect: reproduce first, find the root cause and every caller, set the proof. Use for `/plan-bug <ticket or symptom>` and any "this is broken" report. |
| `plan-epic` | `plan` | `{kind: epic, intensity: medium}` | Design a whole epic before any ticket is built: premise attack, flow diagram, adversarial rounds, ticket table. Use for `/plan-epic <key or brief>` or "plan this whole thing". |
| `plan-fix` | `plan` | `{kind: fix, intensity: medium}` | Plan the response to every human review comment on your change after /verify-comments: fixes, follow-ups and replies, approved by you before building or posting. Use for `/plan-fix <change url>`. |
| `plan-spike` | `plan` | `{kind: spike, intensity: medium}` | Plan a time-boxed spike: the question, the decision it informs and the cheapest experiment. Use for `/plan-spike <question>` when the answer matters more than the code. |
| `plan-story` | `plan` | `{kind: story, intensity: medium}` | Plan one story before building: verdict, premise attack, approach review, node graph. Use for `/plan-story <ticket or description>` and any change touching several files or an interface. |
| `plan-task` | `plan` | `{kind: task, intensity: medium}` | Plan one bounded task, a change with a known shape, before building. Quick path for one file with an obvious check. Use for `/plan-task <description>` and small features or refactors. |
| `reflect` | none | none | Mine this session for reusable procedures, corrections and knowledge, and propose skill, CLAUDE.md or memory updates without applying them. Use for /reflect or at the end of substantial work. |
| `ticket-write` | `write` | `{target: ticket}` | Write or rewrite a ticket's summary and description in the team's style, with what the assignee needs. Use for "raise a ticket", "draft the issue" or /ticket-write. |
| `verify-change` | `review` | `{mode: change, intensity: medium, target: url}` | Review someone else's change on a pinned checkout; post confirmed findings after your OK. Medium by default, `light` or `intense` on request, `recheck` to re-review. Use for `/verify-change <url>`. |
| `verify-comments` | `review` | `{mode: comments, intensity: medium, target: url-or-pasted}` | Judge other people's review comments on a change against the code: valid, not valid or partly valid, with evidence. Posts and edits nothing. Use for /verify-comments or "are these comments right". |
| `verify-epic` | `review` | `{mode: epic, intensity: medium, target: epic-key}` | Review every change of an epic through the review engine, then check the seams: merge order, shared contracts and schemas, epic coverage. Use for `/verify-epic <epic key or change list>`. |
| `verify-plan` | `review` | `{mode: plan, intensity: medium, target: ticket-epic-or-doc}` | Attack a ticket, epic or written plan before anyone builds it: premises, approach, gaps, sequencing. Never edits the thing reviewed. Use for `/verify-plan <ticket, epic or doc>`. |
| `verify-self` | `review` | `{mode: self, intensity: medium, target: branch}` | Review your own built work with fresh reviewers, fix everything, cut comments, describe the change, push through the gate and babysit it green. Use before pushing. Posts nothing. |
