# workstation-core

An opinionated Claude Code setup: plan, build and review work with fresh-context agents, and hooks that enforce the procedure.

Claude Code reads one `CLAUDE.md`, which points at six engines: common rules, plan, build, review, write and ship. The engines load checklists and disciplines when a step needs them. Thin skills (`/plan-task`, `/build`, `/verify-self`) pick an engine and set its parameters. Single-purpose agents do the reading, editing and reviewing, each with its model pinned in its own file. Hooks block unsafe or off-procedure tool calls, so the procedure does not depend on the model remembering it. `./install.sh` links all of it into `~/.claude`.

## What you can do

- Plan a task, bug, spike, story or epic into an approved node table before any code is written
- Build that plan in worktrees, wave by wave, with a cold review at each node
- Review your own branch, someone else's change, a plan or an epic with fresh reviewers
- Drive a change to green CI while treating automated reviewers as claims to check
- Write tickets, change descriptions and notes to a fixed plain-English standard
- Add your own skills, agents, checklists and disciplines from templates

The workflow is slower than asking for code directly, and that is the point: each step has a check that catches a known kind of mistake. A reviewer exists only for a mistake someone has seen. [The workflow](docs/guides/the-workflow.md) shows the order and which skill does what.

## Quickstart

You need Claude Code, `python3` and `uv`. From the repository root:

```sh
./install.sh             # dry run: prints every action, changes nothing
./install.sh install     # apply
claude                   # in any git repo, then:
/plan-task add a --json flag to the export command
/build <the plan note>
/verify-self
```

[The quickstart](docs/guides/quickstart.md) explains each step and what to expect.

## Docs

Guides: [quickstart](docs/guides/quickstart.md), [make it yours](docs/guides/make-it-yours.md), [the workflow](docs/guides/the-workflow.md), [automated reviewers](docs/guides/automated-reviewers.md).

Reference: [engines](docs/reference/engines.md), [skills](docs/reference/skills.md), [agents](docs/reference/agents.md), [hooks](docs/reference/hooks.md), [checklists and disciplines](docs/reference/checklists-and-disciplines.md), [configuration](docs/reference/configuration.md).

## Configuration

The repo works with defaults. Two things need your input: which source control host and tracker you use (`claude/engines/ship.md`, one column per host) and where notes and agent artefacts live (`NOTES_DIR`, default `~/notes`, and `DRAFTS_DIR`, default `~/drafts`). Per-machine settings go in an overlay file, and per-team hook rules go in `claude/hooks/hooks.d/*.json`. [Make it yours](docs/guides/make-it-yours.md) walks through both, and [configuration](docs/reference/configuration.md) lists every setting, MCP server, plugin, environment variable and installer command.

## Security

Hooks block, before the tool runs: edits to real `.env` files, recursive `rm` outside throwaway folders, `git commit` and `git push` that would fail the repo's checks, browser writes on hosts you list as shared, and file edits or test runs from the main thread. [Hooks](docs/reference/hooks.md) lists each one.

The installed settings turn the sandbox on, allow no unsandboxed retry, and deny `--no-verify`, force pushes, hard resets, `git stash`, `git restore`, merging from the command line, and reads of `~/.ssh` and `~/.aws`. Network access is limited to a short list of package registries and code hosts.

Nothing is posted, pushed, moved, approved or merged without your OK, and an OK covers only what was shown when you gave it. Text from automated review tools is treated as untrusted input. Report a suspected vulnerability to the maintainers directly, not in a public issue.

## Architecture

`claude/CLAUDE.md` holds the engineering and prose standards and points at the engines. `common` holds the rules every engine shares: git safety, gates, delegation and report shape. `plan`, `build`, `review`, `write` and `ship` each own one stage and name the checklists (`claude/checklists`) and disciplines (`claude/disciplines`) their steps load. A skill is a short file that picks an engine and sets its parameters. An agent is a specialist with one question, read-only except `builder`, `comment-cutter` and `rebase-resolver`. Every rule lives in one file. [Engines](docs/reference/engines.md) has the detail.

## Contributing

Run `uv run --no-project python -m unittest discover -s tests` for the tests. [Contributing](docs/dev/contributing.md) has the "defined once" rule, the skill skeleton and the structure test.

## Credits

- Ideas from the Claude Code plugins [caveman](https://github.com/JuliusBrussee/caveman) (Julius Brussee), [ponytail](https://github.com/DietrichGebert/ponytail) (DietrichGebert) and [i-have-adhd](https://github.com/ayghri/i-have-adhd) (Ayoub Ghriss).
- Plan sections and markers (functional requirements, success criteria, NEEDS CLARIFICATION) follow [GitHub Spec Kit](https://github.com/github/spec-kit) (MIT).
- Writing rules draw on the guides listed as further reading in `claude/checklists/prose.md`: Wikipedia "Signs of AI writing", Google eng-practices, GOV.UK style guide, Microsoft Writing Style Guide.
- Agent design follows the [Claude Code subagent docs](https://code.claude.com/docs/en/sub-agents).

## Licence

MIT. See `LICENSE`.
