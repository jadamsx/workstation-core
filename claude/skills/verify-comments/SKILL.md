---
name: verify-comments
description: Judge other people's review comments on a change against the code: valid, not valid or partly valid, with evidence. Posts and edits nothing. Use for /verify-comments or "are these comments right".
engine: review
params: {mode: comments, intensity: medium, target: url-or-pasted}
---
## When
Comments pasted in, or a change whose threads need judging before anything changes. Finding new problems is `verify-change`; reviewing your own branch is `verify-self`.

## Inputs
The comments, or the change URL (its unresolved threads are fetched).

## Differs
- Changes nothing and replies to nothing; resolving threads is the owner's call, and only fixed ones.
- Load `house-style` before writing the report.
- Next step once the owner says fix: `/plan-fix <change>`; fixes route through `/build` or `/verify-self`.

## Output
Engine report for `comments`: per comment verdict, severity, status, outcome and drafted reply; then must-change, follow-up, leave.
