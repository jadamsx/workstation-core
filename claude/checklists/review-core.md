# Review checklist: core

The one list every review works from, and the agents that run it (`cold-reviewer`, `finding-refuter`, `miss-hunter`, `test-gap-auditor`, `clean-code`). Each question is answered against the diff with a file and a line, or marked "not applicable" with a reason. A question answered from memory hasn't been checked.

Core holds §0-7 and §17. `review-domain.md` holds §10 and §16. The seven concerns design and review share (§8, 9, 11, 12, 13, 14, 15) live in `design-review-shared.md`.

Sources: Google Engineering Practices, "What to look for in a code review" and "The standard of code review" (google.github.io/eng-practices/review/reviewer/); the OWASP Code Review Guide v2 and ASVS; Microsoft's code-with-engineering-playbook review checklists. Global rules (testing, errors, comments) live in `~/.claude/CLAUDE.md`. Plus any domain checklists your team adds.

## Killer items

Quote the numbers you checked in the report. An item you skipped is named, with why.

1. Claims ledger built: every load-bearing claim in the ticket, description and docstrings is marked verified, false or unverified because X.
2. Every finding carries a `file:line` that resolves in the pinned tree, what breaks and the fix. One that does not resolve is dropped.
3. Entry-point threat model: you reached the code the way a caller does, and any gate the diff relies on is followed to the code that runs it (shared Security).
4. Failure reported as success: every read followed to the function that runs it; none swallows an error into `[]`, `None` or `{}` (shared Failure modes).
5. Tests: every new test fails against a do-nothing implementation, and a reproduce test fails at an assertion on the old code (§7).
6. The diff changed or deleted nothing nobody asked for, and the history of the changed lines (`git log -L`) does not contradict it (§0).
7. Said what you ran and what you only read, and named the changed files you did not read. Agreement between agents is not evidence.
8. A real bug is stated first; style never pads the report.

## Reference

Process: engines/review.md (claims, pin, hunt lanes, refute, confirm, briefing, severity, reviewer conduct, rounds).

## 0. Context: ticket, decision records, plan
- Every acceptance criterion is met or named as another change's job; an unmet one is a scope question, resolve it against the change description.
- What did the diff change or delete that nobody asked for?
- History of the changed lines: `git log -L` or `git blame` on the base. A diff that undoes what an earlier commit deliberately fixed, or re-adds what one deliberately removed, is a finding; quote that commit. (trailofbits differential-review)
- A false premise is reportable on its own even when the diff is clean, because the scope came from it.
- Decision records, if the repo keeps them: read every applicable one. A conflict with a recorded decision stops the review and is handed back.
- Plan fit: matches its slice of the parent epic's ticket text and any design doc the change links, and states what it hands the next change.
- Value: the decision or user outcome it serves, and whether it serves it.

## 1. Design
- Is this the right approach, or is there a simpler one that does the job? (Google)
- Should it exist at all? Does a helper, service, sibling repo or platform feature already do it?
- Does it belong in this layer and repo, and does it fit the rest of the system rather than just work in isolation? (Google)
- Is the abstraction proportional to today's problem, with no speculative generality? (Google over-engineering, CLAUDE.md YAGNI)
- For an abstraction that doesn't pay yet (an interface with one implementation, a factory for one product, a layer that only forwards), say what it would take for it to start earning.
- For every "rendered from X", "called via Y" or "registered at Z", does the mechanism exist? Find the code with a file and line.
- When a ticket spans repos, read every change in it: the strongest finding may be invisible from inside one.
- **When the diff adds a guard** (a lint, sweep, parity test or allow-list), hunt its blind spot. Look for siblings with the same flaw under another spelling: the same identity as `owner_id` or `user_id`, the same fallback as a ternary, the same store keyed dynamically. Then ask whether what it does catch was already covered upstream. A guard whose whole matched set is protected elsewhere catches nothing.

## 2. Functionality and correctness
- Does it do what the author intended, and is that what the user needs? (Google)
- Premises: is each "X does Y" in the ticket, description and comments true in the code?
- Edge inputs: empty, None, zero, one, many, the maximum, duplicates, unicode, very long, negative, wrong type.
- Every branch and error path, with nothing silently falling through, and unknown states refused. (Google)
- Time: UTC and ISO, expiry, ordering, string versus numeric sort.
- The error path at each transition of a run, request or state machine.

## 3. Complexity and code quality
- Can a reader understand each line quickly without re-reading? (Google)
- Dependency direction: lower layers don't import higher ones, and no cycles hidden behind local imports.
- Explicit data flow, with no hidden state or globals. (CLAUDE.md)
- Types: full hints or strict TS, and `Any` or `any` only with a reason. (CLAUDE.md)
- Dead code: unused imports, unreachable branches, stale flags, commented-out code.

## 4. Naming
- Names say what a thing is or does, in the domain's words, with no bare `data`, `info`, `handle`, `process`, `manager` or `helper`. (Google)
- Dense-but-short code gets named intermediates rather than fewer lines.
- Long names aren't a problem. Unclear ones are.
- Worse than a name that says nothing is one that says the wrong thing because the code moved on.

## 5. Comments and docs (owner: CLAUDE.md Comments)
- Comments explain why, not what, and are mostly absent where the code speaks for itself. (Google, CLAUDE.md)
- A docstring states the contract: inputs, outputs, errors raised, side effects. It doesn't restate the signature. (CLAUDE.md)
- A comment made false by the change is a blocker.
- No ticket, decision record or change references or TODOs in code. Comment gates pass. (CLAUDE.md)
- The README, runbook, decision record or API doc is updated when behaviour or setup changes. (Google)

## 6. Style and consistency
- The repo's style guide and linters are the authority on pure style. Otherwise match the surrounding code. (Google standard)
- Don't add to an existing inconsistency. Raise a follow-up rather than copy bad style. (Google)
- Error, logging and layout conventions match the file's.

## 7. Tests (owner of the rule: CLAUDE.md Testing)
- New or changed behaviour has tests at the right level: unit, integration, or end to end on a real service. (Google)
- A reproduce test fails on the old code at an assertion, not in setup, an import or an `AttributeError`, and passes with the fix. (CLAUDE.md)
- Every test fails against a do-nothing implementation, and pins the observable things that changed. (CLAUDE.md)
- Security properties are asserted on real compiled output or the real gate, never on a fake that filters for itself.
- Fakes behave like the real thing where it matters: duplicate-key errors, error envelopes, pagination.
- Edge inputs from section 2 are covered, and test names say the behaviour, briefly. (CLAUDE.md)
- Run it for real where you can reach it. Never against a shared or demo database. Mutate code in a scratch copy.
- The already-satisfied case and the exactly-one-requirement-short case, not just everything-missing and everything-present. Two gates on the same path can mask each other. Both sides of a feature flag. Error responses name the specific field or state, not a generic failure. Empty array, missing key and null are three different cases.
- A test a repair round would be tempted to delete is often the one to keep.

## 17. Delivery
- The title follows convention and the description follows the repo template: merge order, deploy dependencies, what the gate doesn't cover, "waits for <change>". (CLAUDE.md)
- Pre-commit, lint, type check and the focused suite pass before the push. (CLAUDE.md)
