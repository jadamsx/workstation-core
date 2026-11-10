---
extends: none
---
# Investigate first

When the plan picks this: an unknown cause, intermittent behaviour or a performance regression. The output is a cause, not a fix.

## Rules
- Gather evidence before changing product code. Separate the observed symptom from the inferred cause.
- Trace inputs, state transitions, ownership boundaries and failure output.
- Rank hypotheses by evidence and by how cheaply each can be falsified. Test the cheapest first.
- Do not edit until one mechanism explains all the evidence.
- Instrument on a scratch copy and remove it afterwards.
- Quote the shortest decisive log line, not the log.

## Proof
Name the cause with the file:line and the run or log that shows it. Say what you ruled out.

## Stop
Evidence is enough to name the cause or the exact blocker. Make no fix unless the plan authorises one, and then switch to reproduce-first.

Process: engines/build.md
