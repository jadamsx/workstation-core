# Make it yours

The repo ships with defaults and a few blanks. This page covers each one.

## Set your source control host and tracker

`claude/engines/ship.md` is the only file that names a source control host or tracker. Its "Source control adapter" table has a GitHub column (`gh`) and a GitLab column (`glab`). Everything else says "the source control host" and "the tracker".

- GitHub or GitLab: nothing to change. The column is picked from the git remote.
- Another source control host: add a column to that table, and nowhere else.
- A tracker: the ship engine reads and moves tickets through the source control host's issues, or through a tracker connector you install. Add the connector in your settings overlay and the engine uses it.

The structure test fails if source control words appear outside `ship.md`, so keep it that way. To keep local changes out of the shared file, fork the repo and edit your fork.

## Add hook rules for your team

The commit and push guards read optional rules from every `*.json` file in `claude/hooks/hooks.d/`. Files load in name order, lists add up and objects merge. Every rule is off until you turn it on. Example `team.json`:

```json
{
  "change": {
    "title_requires_ticket": true,
    "ticket_key": "[A-Z][A-Z0-9]+-\\d+"
  },
  "opus_override": ["premise-attacker"]
}
```

[Hooks](../reference/hooks.md) lists the keys. `HOOKS_CONFIG_DIR` points the hooks at another folder.

## Add a domain checklist

A checklist is a short list of killer items plus a reference section. Copy `claude/templates/checklist.md` to `claude/checklists/<name>.md`, write five to nine killer items that cause real damage when skipped, and put the rest under Reference. Then point to it from the one place that should load it: an engine step, an agent or a discipline. The structure test checks that every path reference resolves.

## Add to your CLAUDE.md

`claude/CLAUDE.md` is linked to `~/.claude/CLAUDE.md`. Edit it for your standards and keep the pointers to the engines. For rules that apply to one project, put a `CLAUDE.md` in that repo: Claude Code reads both.

## Write your own skill, agent, checklist or discipline

Start from the file in `claude/templates/`.

| You want | Copy | To |
| --- | --- | --- |
| A slash command | `skill.md` | `claude/skills/<name>/SKILL.md` |
| A specialist | `agent.md` | `claude/agents/<name>.md` |
| A rule list | `checklist.md` | `claude/checklists/<name>.md` |
| A way of working for a node | `discipline.md` | `claude/disciplines/<name>.md` |

A skill sets `engine:` and `params:` in its frontmatter and fills four headings: When, Inputs, Differs, Output. Say only what differs from the engine. An agent has one question, a pinned `model:` and the fewest `tools:` it needs. Run `./install.sh install` to link the new file, then run the tests: see [contributing](../dev/contributing.md).

## Where notes and drafts live

| Variable | Default | Holds |
| --- | --- | --- |
| `NOTES_DIR` | `~/notes` | Plans, designs, decisions: anything a person reads, under `projects/<slug>/` |
| `DRAFTS_DIR` | `~/drafts` | Agent artefacts, under `projects/<slug>/<topic>/` |

Set them in your shell profile. The sandbox allows writes to `~/notes` and `~/drafts` only, so add your own paths to `sandbox.filesystem.allowWrite` in an overlay. The project slug comes from `WORKSTATION_PROJECT`.

## Per-machine settings

Put `<hostname>/settings.overlay.json` in a `machines/` folder in the repo, or in the folder `WORKSTATION_MACHINES` names, and the installer merges it over `claude/settings.base.json`. Use it for extra sandbox exclusions, more allowed domains and your own hooks. [Configuration](../reference/configuration.md) has the rest.

## Tune the guard hooks

The commit, push, drafts and model guards take their rules from JSON files in `claude/hooks/hooks.d/`. To require a gitmoji or a ticket key, allow another drafts folder or let an agent run on Opus, add a file such as `hooks.d/mine.json` and leave the hook scripts alone. See [configuration](../reference/configuration.md#hook-rules-in-hooksd) for the format and an example.
