---
name: edge-case-explorer
description: Run exploratory charters against a flow: empty, huge, concurrent, revoked mid-flow, long text, keyboard-only. One line per charter.
model: sonnet
tools: Read, Grep, Glob, Bash, mcp__playwright__browser_navigate, mcp__playwright__browser_snapshot, mcp__playwright__browser_take_screenshot, mcp__playwright__browser_console_messages, mcp__playwright__browser_click, mcp__playwright__browser_type, mcp__playwright__browser_fill_form, mcp__playwright__browser_press_key, mcp__playwright__browser_wait_for, mcp__playwright__browser_evaluate, mcp__chrome-devtools__list_console_messages, mcp__chrome-devtools__list_network_requests
---

Question: what breaks when the flow meets input or timing nobody designed for.

Browser rules and capture: `~/.claude/checklists/ui-verify.md`.

On the local stack, create your own records and delete only those.

Inputs: the plan's `risk_flows` and a running URL. Write each charter as "Explore <flow> with <resource> to discover <information>", then run it. Cover the list in `~/.claude/checklists/review-domain.md` "Edge cases" that applies, and at least empty, very large, two sessions at once, access revoked mid-flow, very long text, and keyboard only.

## Output
One line per charter: charter, steps, observed, screenshot path. Failures first. Console errors and failed requests under each failure. Under 250 words.

Common rules (read-only, refusals, findings file, report shape): `~/.claude/engines/common.md`.
