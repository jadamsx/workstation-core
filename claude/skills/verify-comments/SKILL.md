---
name: verify-comments
description: Judge other people's review comments on a change against the code: valid, not valid or partly valid, with evidence. Posts and edits nothing. Use for /verify-comments or "are these comments right".
engine: review
params: {mode: comments, intensity: light, target: url-or-pasted}
---
## When
Comments pasted in, or a change whose threads need judging before anything changes. Finding new problems is `verify-change`; reviewing your own branch is `verify-self`.

## Inputs
The comments, or the change URL (its unresolved threads are fetched).

## Differs
- Rounds follow `engines/review.md` "Round shapes".
- Changes nothing and posts nothing; its drafted reply is the text `/plan-fix` posts.
- Load `house-style` before writing the report.
- On your own change, fixes follow via `/plan-fix <change>`.

## Output
Engine report for `comments`: per comment verdict, severity, status, outcome and drafted reply; then must-change, follow-up, leave.
