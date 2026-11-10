# Quickstart

This installs the setup into `~/.claude`, then runs one small change through plan, build and verify.

You need Claude Code, `python3` and `uv`. Everything else is optional.

## Optional tools

Each one is used when present; the setup works without it.

- `grepai`: concept search over a repo. Without it, agents fall back to `rg`.
- `ripgrep` (`rg`) and `ast-grep`: exact and structural code search, used by `code-locator` and `caller-mapper`.
- `jq` and `bc`: the status line.
- `mmdc` (Mermaid CLI): renders diagrams. `npx -y @mermaid-js/mermaid-cli` also works.
- Playwright for Python: `shot` and `browser-login`, the two helpers that drive a browser.
- Node.js (`npx`): starts the MCP servers in `claude/mcp.json`.
- `gh` or `glab`: the source control CLI the `ship` engine and the push guard call, one per host.
- `herdr`: `current-project` reads the pane's workspace name from it.

## Install

```sh
# from the repository root
./install.sh             # dry run: prints every action
./install.sh install     # apply
./install.sh status      # compare the repo with the live machine
```

Read `install.sh` and `lib/workstation.py` first, since the installer writes into `~/.claude` and `~/.local/bin`. It symlinks skills, agents, hooks, engines, checklists, disciplines and templates, merges `claude/settings.base.json` into your `settings.json`, applies the MCP servers in `claude/mcp.json`, and links five helper commands. A file it displaces is moved to `~/workstation-backups/<timestamp>/` with a manifest. `./install.sh uninstall` restores from it.

Make sure `~/.local/bin` is on your `PATH`, then create the two folders the skills write to:

```sh
mkdir -p ~/notes ~/drafts
```

Plans and notes go to `~/notes`, agent artefacts to `~/drafts`. [Make it yours](make-it-yours.md#where-notes-and-drafts-live) shows how to move them.

## Plan

Set a project name, open Claude Code in a git repository and give it one bounded task:

```sh
export WORKSTATION_PROJECT=myproject
claude
```

```
/plan-task add a --json flag to the export command
```

`plan-task` sizes the task, runs five design questions against the code, writes a node table and has fresh reviewers attack it. A node names its files, its acceptance check, its discipline and its review intensity. The plan is saved as a note under `~/notes/projects/myproject/designs/` with `status: proposed`.

Read the table. Say `go` to approve it, or say what to change. Nothing is built before the go. Use `/plan-bug` for a defect, `/plan-spike` for a question and `/plan-story` or `/plan-epic` for bigger work.

## Build

```
/build <the plan note>
```

`build` refuses a plan that is not approved. It makes a worktree at fresh `origin/<base>`, runs the nodes wave by wave through `builder`, reviews each node with a `cold-reviewer`, runs the formatter, linter, types and tests once on the whole tree, and says what it ran. Nodes that own disjoint files run in parallel.

## Verify

```
/verify-self
```

Fresh reviewers read your branch, every finding is fixed, comment slop is cut, and the change description is written from the repo's template. Nothing is posted or pushed without your OK. After you push, `/babysit` watches the pipeline and the [automated reviewers](automated-reviewers.md).

## Next

- [The workflow](the-workflow.md): which skill does what, and when.
- [Make it yours](make-it-yours.md): your source control host, your checklists, your own skills.
- [Skills](../reference/skills.md): the full list.
