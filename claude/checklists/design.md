# Design checklist

The single list of design and pre-build rules: what to check before code exists. Used by `engines/plan.md` and `engines/review.md` plan mode. It is the design-side twin of `~/.claude/checklists/review-core.md`.

Design §6-12 (data, API, security, failure modes, capacity, observability, rollout) are shared with review and live in `design-review-shared.md`.

Sources: Google's "Design Docs at Google" (Malte Ubl, industrialempathy.com/posts/design-docs-at-google/); Google SRE launch checklist (sre.google/sre-book/launch-checklist/); AWS Well-Architected Framework (docs.aws.amazon.com/wellarchitected/); adr.github.io; `agents/premise-attacker.md`; `~/.claude/CLAUDE.md`.

Shape each change against `~/.claude/checklists/review-core.md` so the plan already answers what reviewers will ask. Plus any domain checklists your team adds. Diagrams: `engines/write.md` owns whether one is needed, which type and the render check.

## Killer items

Quote the numbers you checked in the report.

1. The five answers (§0) are written, each with a `file:line` or `N/A` plus why. `unknown` blocks approval.
2. Every "X does Y" premise in the ticket has a `file:line` (§2). Without one it stays a guess.
3. Nothing already does this: helper, sibling repo or platform feature, checked off `origin/<base>` (§2, §3).
4. Any score, metric or gate was tried against a constant answer, and the sample count can separate candidates (§16).
5. The deliverable is validated before the inputs that feed it get built, and every event's consumer ships with or before its producer (§17).
6. Deploy order and rollback are stated for each step (shared Rollout).
7. UI follows the design frame; states the frame omits go to the designer (§18).
8. The report separates what was verified from what was reasoned, and has no strengths section.

## Reference

Process: `engines/review.md` plan mode.

## Reviewer conduct

Same as `engines/review.md` "Reviewer conduct", except: no strengths section, no mention of what's done well; findings only. One addition specific to design review: separate what you verified from what you reasoned about explicitly in the report; a design review that overclaims gets ignored faster than a code review that does.

### AI failure modes at design time

Shared core: `~/.claude/checklists/build.md` §3 "Honesty and verification". These are the design-time versions.

- An invented mechanism or premise stated as fact needs a `file:line`; without one it stays a guess.
- No citation or URL that wasn't opened; a homepage isn't a source for the claim it's attached to, and a domain isn't real until it resolves.
- Test the framing handed over instead of adopting it; a ticket's premise is a claim to check.
- No confident sizing ("small change", "a few weeks") without reading the code it's sized against.

## 0. The five answers

Before any plan is approved, including a plan of Claude's own, answer these. One sentence each. Every answer carries a `file:line`, or `N/A, greenfield` plus a sentence proving nothing overlaps, or `unknown`. `unknown` blocks approval.

0. **Should this be built at all?** A verdict, not a question passed upward: **build** (evidence nothing already does it) / **already exists** (cite it) / **don't** (say why). The last two end the task. No plan, no code, no building it anyway with a caveat.
1. What breaks if this is wrong?
2. What does this delete or replace?
3. What is the smallest version that delivers everything decided?
4. Who reads the output, and what do they do with it?

## 1. Problem, goals, non-goals

- Does the ticket state the concrete problem, not just a solution idea? (design-docs-at-google, "Overview and Context")
- Are goals distinct from non-goals, with explicit scope boundaries? (design-docs-at-google, "Goals and Non-Goals")
- Is the problem confirmed in the codebase or real user feedback, not assumed from intuition?
- What decision does this inform, and who makes it? A ticket informing no decision is the one to cut.
- Would a busy senior engineer quietly never pick this up? If so, decide whether that is the ticket's fault or the priority's.

## 2. Premises and mechanism

- Does the ticket claim "X currently does Y" or "Z is already logged"? Verify against the code, with file and line. Premises are written weeks before the work and rot quietly.
- For every "rendered from X", "called via Y", "registered at Z" or "mounted in W", find the code that does it at that exact spot.
- Have sibling and neighbouring repos been checked for overlapping or duplicate work, off `origin/<base>`?
- Is the stated scope ("small change", "N weeks of work") validated by reading the code, not guessed? Authors and generators both underestimate; say where a "small change" claim is wrong and why.

## 3. Reuse and should-it-exist

- Does a helper, service, sibling repo or platform feature already do this?
- Does an already-installed dependency solve it, or is a new one justified, maintained, and licence-compatible? (the build ladder in CLAUDE.md)
- Is this speculative work, or does it unblock a concrete next ticket?

## 4. Alternatives considered

- What are the concrete alternatives and their trade-offs? (design-docs-at-google, "Alternatives Considered")
- Which alternative is simpler, and why wasn't it picked?
- For each rejected alternative, what becomes unacceptable if we take it instead?

## 5. Architecture fit and decision records

- Have the repo's decision records (ADRs), if it keeps them, been read in full, not by search?
- Does a recorded decision bind here, and is there a conflict? A conflict stops the design; it is handed back, not resolved in the design.
- Read the exact line of a decision before citing it.
- Is the platform the right shape to receive this, or does it need a seam that doesn't exist yet? Name which option the design takes.
- Does something else need to happen first (a missing abstraction, a wrongly placed boundary) that would make this epic and the next smaller?

## 13. Dependencies

- What tickets or changes must land before this one, and in what order?
- For cross-repo or published-artifact changes: are consumers named as pinned or unpinned, with counts per unpinned consumer measured off `origin/<base>`?
- Have collisions been checked: tickets in the set that touch the same files, which lands first, what breaks if not?
- Are other in-flight changes touching the same files accounted for?

## 14. Cost and maintenance ownership

- What ongoing effort does this create: a fixture set that rots, a threshold someone must tune, a second source of truth that can disagree with the first?
- Is that maintenance named and owned, or left implicit?
- Against the value it serves, is the effort justified? Where is something expensive being built while a cheap thing that answers the same question goes undone.

## 15. Test strategy

- What must each change prove, at what level: unit, integration, or a real end-to-end run? (review §7)
- For a bugfix: does the reproduce test fail at base, at an assertion not in setup, and pass with the fix? (CLAUDE.md, review §7)
- Does the plan name the review §7 bar the tests must clear, rather than restating it here?

## 16. Measurement

- If this produces a score, metric or gate: what trivial strategy (constant, empty, abstention) might score the same? A constant scoring as well means it measures agreement with a fixture set rather than the thing it's named after.
- Is the sample count large enough to separate candidates, or does it move in coarse steps?
- Would the environment produce this result anyway, without the change?
- Does the name of the metric promise more than the number delivers?

## 17. Sequencing and change slicing

- What does each change's slice hand to the next one?
- Is the deliverable's shape validated (mocked, shown to its audience) before the inputs that feed it get built?
- Is every ticket's acceptance one sentence? A two-sentence acceptance is two tickets.
- Does every event's consumer ship before, or in the same release as, its producer? An event raised while no consumer is registered can be lost.

## 18. UI

- For every user-visible string, type, status and button: data or code? Cite the rule that decides it.
- UI follows the pre-made design frame when one exists; it is never invented. The check is fidelity to the frame, not taste.
- Any state or flow the frame doesn't show gets raised as a question for the designer, never designed by the agent.
