---
name: plan-spike
description: Plan a time-boxed spike: the question, the decision it informs and the cheapest experiment. Use for /plan-spike <question>.
disable-model-invocation: true
engine: plan
params: {kind: spike}
---
## When
A feasibility or approach question where the answer matters more than the code. Work that will ship is `plan-task` or `plan-story`.

## Inputs
The question. A vague one starts the interview, which asks only Task and Extra info.

## Differs
Discipline `spike`. The verdict names the decision it informs and who makes it; none, no run. Prior art: notes, then `researcher` and `code-locator`; cite sources for what is known. One to three `spike` nodes; `owns` is a scratch branch or copy; nothing merges. Review is one `premise-attacker` round. Findings go to `projects/<slug>/research/` via `notes-write` (top-level `research/` with no project), linked from the index and the decision.

## Output
Question, decision, box, experiment, node row, the go question.
