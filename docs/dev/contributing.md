# Contributing

## Defined once

Every rule, sentence and table lives in one file. Other files point to it by path and never restate it.

- Git safety, gates, delegation, the model rule and the report shape: `claude/engines/common.md`.
- Source control and tracker names: `claude/engines/ship.md` only.
- A model: the `model:` line of the agent, nowhere else.
- Checklist items: one checklist. Discipline rules: one discipline.
- Lower layers (engines, checklists, disciplines, agents) never name a skill.

If you find a rule in two places, delete one and link to the other. The structure test enforces the parts it can.

## Skill skeleton

A skill is `claude/skills/<name>/SKILL.md`, at most 60 lines, with this frontmatter and these four headings. `claude/templates/skill.md` is the starting file.

```md
---
name: <name, equal to the folder>
description: <trigger, 200 characters or fewer>
engine: <plan|build|review|write|ship>
params: {<key>: <value>}
---
## When
## Inputs
## Differs
## Output
```

`engine` and `params` are optional for a standalone skill. Say only what differs from the engine. Agents start from `claude/templates/agent.md`: one question, a pinned `model:`, the fewest tools.

## The structure test

`tests/test_claude_structure.py` checks the files under `claude/`:

- Skill frontmatter, the four headings, the 200-character description cap and the 60-line cap.
- Lower layers name no skill.
- Source control words (`gh`, `glab`, GitHub, GitLab, Jira, PR, MR) appear only in `engines/ship.md`.
- Every `engines/`, `checklists/`, `disciplines/` or `agents/` path reference resolves to a file.
- No em dashes.
- No sentence of 12 words or more appears in two files.

## Run the tests

```sh
uv run --no-project python -m unittest discover -s tests
uv run --no-project python -m unittest discover -s tests/hooks
uv run --no-project python -m unittest tests.test_claude_structure
```

`test_browser_scripts` needs Playwright for Python and fails to import without it. Everything else runs on the standard library.

## Prose

Docs and comments follow `claude/checklists/prose.md`: plain English, short, no em dashes, no filler. Use the `house-style` skill before writing anything longer than a couple of sentences.

## Changes

Keep a change to one concern. Run the tests before you push, and never skip a hook. Say in the description what you ran and what you could not run.
