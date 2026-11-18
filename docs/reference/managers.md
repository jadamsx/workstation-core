# Managers

Delegated work runs inside [herdr](https://herdr.dev). The coordinator is the main chat in a workspace, a manager is a Sonnet session in its own tab (`▸ <name>`) that runs one stream of work, and a watcher carries the manager's result files back to the coordinator. Delegation rules are in `claude/engines/common.md`. Everything here does nothing without herdr: `manager-start --check` exits 1, the watcher idles, the hooks stay silent.

## Commands

| Command | What it does |
| --- | --- |
| `herdr-manager register` | Run in the coordinator's pane. Saves it as the coordinator of its workspace and renames its tab `◆ lead`. Run again after a handoff and reports follow the new pane |
| `manager-start <name> --prompt "<text>" [--dir <path>]` | Opens the manager tab and sends the prompt once the agent is ready |
| `manager-start --check` | Prints `coordinator` and exits 0 in the registered coordinator pane, exits 1 anywhere else |
| `manager-send <name> "<text>"` | Delivers `[coordinator] <text>` to the manager, retrying every 15 seconds for up to 10 minutes while it is blocked |
| `manager-close <name>` | Closes the tab and marks the manager closed |
| `herdr-manager list` | Managers of this workspace, whether their pane is alive, and their newest result file |
| `herdr-report-watch [--once] [--interval <seconds>]` | The watcher, normally run by launchd |

`herdr-manager start` waits until the new pane holds only the shell, then runs `herdr agent start`, retrying up to three times, 2 seconds apart, while herdr reports the pane busy.

## Reports

A manager reports by writing `result-<timestamp>.md` into `$WORKSTATION_REPORTS`. The first line is `Status: decision` (the tab stays open) or `Status: done` (the watcher delivers it, then closes the tab). The watcher sends the coordinator `[worker-report] <path>` once per file, retrying every 15 seconds while the coordinator is blocked. It also sends:

- `[worker-report] <name> exited without a report`, once per pane, when a manager's pane is gone.
- `[worker-report] <name> idle, no report` with the last lines of the pane, once per idle spell, when a manager has been idle for 15 minutes without writing a report and its last message does not start with `WAITING:`.

State is kept in `<root>/.watch-state.json`. The root is `WORKSTATION_REPORTS_ROOT`, default `~/.local/state/workstation/reports`.

## Hooks

Active only where `WORKSTATION_REPORTS` is set, so only in manager sessions. [Hooks](hooks.md) lists their events.

- `report-format-guard.py` blocks a file in the reports folder that is not named `result-*.md` (or the `.draft` that is moved to such a name) or whose first line is not a Status line, and prints the correct command.
- `report-stop-guard.py` blocks one stop when the turn wrote no report and the last message does not start with `WAITING:`.
- `manager-brief-inject.py` returns `claude/templates/manager-brief.md` after a compact or clear.

## The watcher agent

`launchd/dev.workstation.herdr-report-watch.plist` runs `herdr-report-watch` with `KeepAlive` and logs to `~/Library/Logs/herdr-report-watch.log`. It has `__ROOT__` and `__HOME__` placeholders for an installer that renders and loads launchd agents; the core installer does not, so without one run `herdr-report-watch` yourself.
