# Agents

An agent is a single-purpose subagent in `claude/agents/<name>.md`. Its `model:` line is the only place a model is set: engines, skills and prompts never state or override it. The `agent-model-gate` hook refuses a spawn that would run on the session model.

Every agent is read-only except `builder`, `comment-cutter` and `rebase-resolver`. Agents never dispatch other agents. A refusal is one line: `<slug>. ask: <one question>.` The shared rules are in `claude/engines/common.md`.

The table is read from the agents' frontmatter. `claude/templates/agent.md` is the starting point for a new one.

| Agent | Model | Job |
| --- | --- | --- |
| `a11y-auditor` | haiku | Run axe on each UI state and tab through the flow, checking focus and labels. Reports violations with selectors. |
| `approach-reviewer` | opus | Review a design, plan or change's approach: alternatives, fit with recorded decisions, contracts, failure modes, rollout, tests, sequencing. Reports only. |
| `builder` | sonnet | Make the edit you were handed. Scope one-file for a bounded edit in 1-2 files, scope node for one plan node in your own worktree. |
| `caller-mapper` | haiku | List callers and importers of one function or type with file:line. Use for what-calls-X and blast radius. |
| `claim-prover` | sonnet | Run the real suite or endpoint to confirm behaviours, or replay build-time bugs. Pass or fail with output tail. |
| `clean-code` | sonnet | Judge code shape across a whole diff: duplicated knowledge, mixed jobs, branching that wants dispatch, invariants asserted in comments. |
| `code-locator` | haiku | Find where a symbol, config key, file or concept is defined, or inventory a path. Returns file:line rows. |
| `cold-reviewer` | sonnet | Review a diff with ticket and code only, never the plan or authoring session. Finds correctness, security and contract bugs. |
| `comment-cutter` | sonnet | Strip AI comment slop from a branch before push: restated-what comments, ticket references, tutorial docstrings. Edits comments only. |
| `comprehension-cutter` | haiku | Cut draft review comments to what the author can act on. Never judges whether a finding is true. |
| `design-gap-finder` | opus | Given a set of tickets or designs, find what the whole set misses: ordering, ownership, unvalidated outputs. |
| `edge-case-explorer` | sonnet | Run exploratory charters against a flow: empty, huge, concurrent, revoked mid-flow, long text, keyboard-only. One line per charter. |
| `finding-refuter` | sonnet | Try to refute draft review findings against a pinned checkout. Reports which hold. Never posts. |
| `change-reader` | haiku | Read one ticket or one change from the tracker or the source control host, read-only. Ticket text verbatim, change status as a table. |
| `migration-verifier` | sonnet | Run a migration up, down and up again on a throwaway database with realistic rows. Reports counts, constraints and timing. |
| `miss-hunter` | sonnet | Hunt for what a first review pass missed in a change, from one named angle. Reports only. |
| `ops-readiness-auditor` | haiku | Check a change for metrics, alerts, flag on/off, revert safety, runbook line. Yes or no per item, file:line. |
| `perf-tester` | sonnet | Run a load baseline on main versus the branch for a named hot path and report percentiles against thresholds. |
| `premise-attacker` | opus | Attack a ticket before it is built, or, in after-build mode, check shipped behaviour against epic and designs. |
| `rebase-resolver` | sonnet | Resolve rebase or merge conflicts in a worktree and re-run affected tests. Never pushes. |
| `researcher` | sonnet | Answer one research question from code, docs and the web, with a source for every claim. Read-only. |
| `role-tester` | sonnet | Test each plan role against each flow and API for permission leaks and dead ends. Reports a role-by-action matrix. |
| `run-digest` | haiku | Run one named test command, or reduce a saved CI job log, and report the first failure. Use before reading raw output. |
| `security-reviewer` | sonnet | Review a diff for auth, input, secrets and permission flaws, or scan added dependencies and licences. |
| `test-gap-auditor` | sonnet | Find behaviours in a diff with no test that would fail without the change. Reports only. |
| `ui-verifier` | sonnet | Drive a changed UI flow in Playwright, diff it against its design frame. No verdict. |
