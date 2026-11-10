---
name: plan-spike
description: Plan a time-boxed spike: the question, the decision it informs and the cheapest experiment. Use for /plan-spike <question> when the answer matters more than the code.
engine: plan
params: {kind: spike, intensity: medium}
---
## When
A feasibility or approach question where the output is a finding and the code is thrown away. If the work will ship, plan it with `plan-task` or `plan-story`.

## Inputs
The question. A vague one starts the interview, but only Task and Extra info are asked.

## Differs
- Discipline `spike`. The verdict names the decision this informs and who makes it; a spike that informs no decision does not run.
- Prior art: notes first, then `researcher` and `code-locator`; cite sources for what is known.
- One to three nodes of kind `spike`; `owns` is a scratch branch or copy and nothing merges.
- Review is one `premise-attacker` round.
- Findings go to `projects/<slug>/research/` via `notes-write` (top-level `research/` with no project), linked from the index and the decision they informed.

## Output
Question, decision, box, experiment, node row, go question.
