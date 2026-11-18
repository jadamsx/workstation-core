# Herdr spaces

A herdr space splits one workspace into three Claude tabs so the expensive model stops re-reading big contexts. That roughly halves the cost.

| Tab | Model | Job |
| --- | --- | --- |
| `◆ lead` | Opus | You talk to it. It plans, decides and approves |
| `▸ work` | Sonnet | Does the work: builds, reviews and babysits, with subagents |
| `? ask` | Haiku | Quick lookups for you only. Read-only |

## Install

Install [herdr](https://herdr.dev) yourself. It is Apache-2.0 and is not bundled. Then run `./install.sh install`. On macOS that also installs and loads the watcher (below).

## Set up a space

Once per space, open Claude in the tab you want as lead and run:

```sh
herdr-manager setup
```

It registers the tab as `◆ lead`, opens `▸ work` and `? ask` after it, and leaves your own tabs after those. Run it again to repair a missing tab.

## Daily use

1. Type your work into the lead.
2. The lead hands `/build`, reviews and `babysit` to work with `manager-send work "..."`.
3. When work finishes, the lead gets one `[worker-report] <path>` line and reads the file.
4. Work is cleared automatically after each done report. `/clear` is safe in any tab.
5. Use `? ask` yourself. The lead never sends it work.

`manager-start <name> --prompt "..."` opens an extra manager, only for a second parallel stream.

## The watcher

`herdr-report-watch` carries result files to the lead. `install.sh` renders and loads it as a launchd agent on macOS, logging to `~/Library/Logs/herdr-report-watch.log`. Elsewhere, run it yourself.

## Troubleshooting

- Startup prompts are answered for you: folder trust and external `CLAUDE.md` imports, only under the lead's folder. Anywhere else, run `claude` there once to trust it.
- `herdr-manager keep <name>` marks a manager as a long-lived named worker: its reports still arrive, but the watcher never closes or clears it and you close it yourself.
- `herdr-manager list` shows each manager, whether its pane is alive, and its newest report.
- `[worker-report] <name> idle, no report` means a manager sat idle for 15 minutes without reporting. Look at its tab.

[Managers](../reference/managers.md) lists every command.
