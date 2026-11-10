# Review checklist: domain

Concurrency and UI sections of the review checklist, loaded when the diff touches them. Numbering follows `review-core.md`.

Process: engines/review.md

## Killer items

1. Two callers at once, a retry during a slow call and a double submit were each considered, and each race is guarded or accepted in writing (§10).
2. A redelivered event or repeated request is "already done", not a second write (§10).
3. UI: driven in a browser, screenshot taken, console clean (§16, `ui-verify.md`).
4. UI: keyboard reachable, visible focus, labelled controls, contrast (§16).
5. UI: loading, empty and error states exist and match the frame (§16).
6. UI: checked beside the linked design frame, and any state the frame omits raised as a question (§16).

## Reference

## 10. Concurrency and idempotency
- Two callers at once, a retry during a slow call, check-then-act races, shared mutable state, event-loop and thread boundaries.
- Redelivery and double submits: derived key, insert-only, a duplicate is "already done", every other error is a failure; know whether a batch rolls back on one conflict.
- Each race is guarded (revision check, conditional update, unique constraint) or accepted with a comment saying why.

## 16. UI and accessibility (UI changes only)
- It looks right against the design, driven in a browser with a screenshot and a clean console. (Google, CLAUDE.md Testing)
- Keyboard reachable, visible focus, labelled controls, sufficient contrast, and a screen-reader name on icon buttons. (WCAG 2.1 AA)
- Loading, empty and error states exist and match the design.
- Checked side by side against the linked design frame; a state or flow the frame doesn't show is a
  question for the designer.

## 19. Edge cases (flows named in the plan's `risk_flows`)
- Empty: no rows, no results, a new user with nothing yet.
- Huge: a long list, a large payload, a very long text in every field that renders it.
- Concurrent: two sessions or tabs on the same record, a double submit.
- Revoked mid-flow: a session, role or share removed between two steps of the flow.
- Keyboard only: the whole flow completes with no pointer. (WCAG 2.1 AA)
- Interrupted: reload, back button and a dropped connection leave no half-written state.
