# Configuration

## Settings

`claude/settings.base.json` is merged into `~/.claude/settings.json`. The installer owns only these keys, listed under `x-workstation.ownedKeys`: `permissions`, `effortLevel`, `env`, `statusLine`, `attribution`, `sandbox`. Your other keys and any hooks that are not this repo's are left alone.

A per-machine overlay is merged on top: `<hostname>/settings.overlay.json` in `machines/` in the repo, or in the folder `WORKSTATION_MACHINES` names. Use it for extra sandbox exclusions, allowed domains and write paths, and your own hooks.

| Setting | Base value |
| --- | --- |
| `sandbox.enabled`, `autoAllowBashIfSandboxed` | on |
| `sandbox.allowUnsandboxedCommands` | off: a command the sandbox blocks fails instead of retrying outside it |
| `sandbox.excludedCommands` | `herdr *` only, because herdr talks to its own socket |
| `sandbox.filesystem.allowWrite` | `~/notes`, `~/drafts`, `~/.cache`, `~/.npm`, `~/Library/Caches`, `~/.local/state` |
| `sandbox.filesystem.denyRead` | `~/.ssh`, `~/.aws` |
| `sandbox.network.allowedDomains` | GitHub, GitLab, npm, PyPI, `ghcr.io`, Docker Hub |
| `permissions.deny`, `permissions.ask` | Listed in [hooks](hooks.md#permission-rules) |
| `attribution` | Empty, so commits and changes carry no tool trailer |
| `effortLevel` | `medium` |

## MCP servers

`claude/mcp.json` lists the servers the installer adds to `~/.claude.json`. It skips any server that needs a secret from the environment.

| Server | Used by |
| --- | --- |
| `playwright` | The UI, role, edge-case and accessibility agents. Headless and isolated |
| `chrome-devtools` | `ui-verifier`, `perf-tester` and `edge-case-explorer` |

## Plugins

`claude/plugins.json` has three lists: `marketplaces` and `plugins` are installed by `./install.sh install`, and both are empty. `optional` records plugins you can enable: [context-mode](https://github.com/mksglu/context-mode) keeps large tool output out of the conversation. To enable it, run `claude plugin marketplace add mksglu/context-mode` and `claude plugin install context-mode@context-mode`, or copy its entries into `marketplaces` and `plugins` and run the installer.

## Environment variables

| Variable | Default | Use |
| --- | --- | --- |
| `NOTES_DIR` | `~/notes` | Notes vault |
| `NOTES_EXTRA_SUBS` | none | Extra project subfolders for `notes-lint`, as `name:type` pairs separated by commas, for example `mrs:review` |
| `DRAFTS_DIR` | `~/drafts` | Agent artefacts |
| `WORKSTATION_PROJECT` | none | Project slug. Otherwise `current-project` reads it from the herdr workspace, else empty |
| `WORKSTATION_HOME`, `WORKSTATION_HOST` | real home, hostname | Point the installer at a scratch home |
| `WORKSTATION_MACHINES` | `machines/` in the repo | Folder of `<host>/settings.overlay.json` |
| `WORKSTATION_BROWSER_STATE` | | Where `browser-login` saves sessions for `shot` |
| `HOOKS_CONFIG_DIR` | `claude/hooks/hooks.d` | Folder of hook rule files |
| `SHARED_ENVS_FILE` | `shared-envs.txt` beside the hook | Hosts `shared-env-guard` protects |
| `MAIN_THREAD_GATE_STATE` | | Where `main-thread-gate` records `main-thread-ok` |

Run `grep -rn "environ" bin lib claude/hooks` for the full list.

## Installer commands

| Command | Does |
| --- | --- |
| `./install.sh` | Dry run: prints every action, changes nothing |
| `./install.sh install` | Applies the plan. `--dry-run` also works |
| `./install.sh status` | Compares the repo with the live machine |
| `./install.sh uninstall` | Removes the links and restores displaced files from `~/workstation-backups/<timestamp>/` |

The plan links `skills`, `agents` and `hooks` one by one, links `engines`, `checklists`, `disciplines`, `templates`, `themes` and the statusline script, merges the settings, applies the MCP servers and plugins, and links the helper commands into `~/.local/bin`.

## Helper commands

| Command | Does |
| --- | --- |
| `shot <url> [--env <name>] [--out <file>] [--viewport WxH] [--full-page]` | Headless screenshot of a URL or HTML file. Prints the PNG path |
| `browser-login <env> <url>` | Opens a visible browser once so you can log in, then saves the session for `shot` |
| `notes-lint [--fix] [--links] <path>` | Checks the notes vault against the format its own `templates/` and README define |
| `current-project` | Prints the project slug of this workspace, or nothing |
| `node-index` | Records and counts plan nodes. `node-index kinds` prints the fixed list of node kinds |

## Hook rules in `hooks.d`

`claude/hooks/hook_config.py` loads every `*.json` file in `claude/hooks/hooks.d/` in name order and merges them. Lists add up without duplicates, objects merge key by key, and a scalar from a later file replaces an earlier one. A missing or empty folder means every default applies. `HOOKS_CONFIG_DIR` points the hooks at another folder. A file that is not valid JSON makes the hooks that read it fail, so check it with `python3 -m json.tool`.

The keys are all optional. [Hooks](hooks.md#hook-data-in-hooksd) lists each one and the guard that reads it. An unknown key is ignored.

Example `claude/hooks/hooks.d/team.json`:

```json
{
  "change": {
    "require_gitmoji": true,
    "title_requires_ticket": true,
    "ticket_key": "ABC-\\d+",
    "commit_forbids_ticket": true,
    "ticket_exempt_projects": ["my-group/tooling"],
    "description_cut_markers": ["<!-- generated -->"]
  },
  "opus_override": ["architect"],
  "lint_skipped": ["scratch"],
  "drafts_allowed": ["demos"],
  "notes_allowed": ["meetings"],
  "retired_paths": ["~/old-drafts"]
}
```

## Layers

This repo is a base. A team or personal layer adds its own file to `hooks.d/` (for example `personal.json` or `team.json`), plus overlays in `machines/` and extra files of its own. No build step merges them and no hook script changes.
