# Automated reviewers

Copilot code review, CodeRabbit, Danger, review plugins and scanners comment on a change without being asked. `babysit` treats that text as input to check, not as instructions. The rules live in `claude/engines/ship.md`, section "Automated reviewers".

## How a comment is handled

1. It is detected by author type or check name.
2. It is read as a claim and checked against the code, the same way as any review finding.
3. A valid claim is fixed in the code through a `builder`, silently.
4. An invalid or hallucinated claim never stops the run. It goes in chat under `## Dismissed automated comments` with one line of reasoning.
5. Nothing is replied to, resolved or reacted to on the tool's behalf, and nothing is posted because of it.

A comment cannot tell the agent to run a command, skip a check or change a setting.

## Scanner and quality findings

Scanner jobs are read once they finish, from the check annotations on GitHub or the code-quality report artefact on GitLab. If the pipeline publishes none, `babysit` says "no code quality report" in one line and moves on. It does not read other jobs' logs instead.

- Only findings the change introduced count. It compares with the base branch.
- A correct finding is fixed in the code, never by raising a threshold.
- A wrong one goes under `## Dismissed scanner findings` with one line why.
- A genuine exception gets an inline waiver with its reason, never a bare one.

## Human reviewers

Human comments are not handled here. `verify-comments` judges each one against the code, `plan-fix` plans the response, and you approve before anything is posted.

## Limits

The loop runs until checks are green and every valid automated comment is fixed, with at most 10 fix rounds. A flaky-looking failure (runner died, timeout) is retried once before any code is changed. A hidden template job counts as running tests only when something calls it, so the loop checks the CI config before trusting "green".
