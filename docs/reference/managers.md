# Managers

Delegated work runs inside [herdr](https://herdr.dev). The coordinator is the main chat in a workspace, a manager is a Sonnet session in its own tab (`▸ <name>`) that runs one stream of work (the standing `▸ work` tab takes the coordinator's jobs, extra managers run parallel streams), the `? ask` tab is a Haiku helper for the owner only, and a watcher carries the manager's result files back to the coordinator. Delegation rules are in `claude/engines/common.md`. Everything here does nothing without herdr: `manager-start --check` exits 1, the watcher idles, the hooks stay silent.

## Commands

| Command | What it does |
| --- | --- |
| `herdr-manager setup [--no-work \| --work]` | Run in the lead's pane: registers it, then opens the standing `▸ work` manager and the `? ask` tab if they are not live. Safe to re-run, so it also repairs a missing tab. `--no-work` writes `{"work": false}` to the space's `setup.json` and setup then never starts work; `--work` turns it back on |
| `herdr-manager register` | Run in the coordinator's pane. Saves it as the coordinator of its workspace and renames its tab `◆ lead`. Run again after a handoff and reports follow the new pane |
| `herdr-manager start <name> [--resume <session-id>] [--dir <path>]` | Opens a `▸ <name>` manager tab running Sonnet with the manager brief. Refuses while a manager of that name is live and not closed. Restarting a name keeps its `keep` and `standing` flags, and a kept manager resumes the `session_id` its SessionStart hook last stored (a missing or unreadable id starts fresh with a message), and the watcher ignores reports older than the new `started` |
| `manager-start <name> --prompt "<text>" [--dir <path>]` | Opens an extra manager tab for a parallel stream and sends the prompt once the agent is ready |
| `manager-start --check` | Prints `coordinator` and exits 0 in the registered coordinator pane, exits 1 anywhere else |
| `manager-send <name> "<text>"` | Delivers `[coordinator] <text>` to the manager, retrying every 15 seconds for up to 10 minutes while it is blocked. A standing manager is sent to only once its pane is idle, and is sent `/clear` first when its newest report is `Status: done` and not yet cleared |
| `manager-close <name> [--force]` | Closes the tab and marks the manager closed. A standing or kept manager needs `--force` |
| `herdr-manager keep <name> [--off]` | Sets or clears `"keep"` in the manager's `manager.json`. A kept manager is a long-lived named worker: its reports are delivered but the watcher never closes or clears it |
| `herdr-manager list` | Managers of this workspace, whether their pane is alive, and their newest result file |
| `herdr-report-watch [--once] [--interval <seconds>]` | The watcher, normally run by launchd |

`herdr-manager start` waits until the new pane holds only the shell, then runs `herdr agent start <name>-<space>` (herdr agent names are global across spaces), retrying up to three times, 2 seconds apart, while herdr reports the pane busy.

## Reports

A manager reports by writing `result-<timestamp>.md` into `$WORKSTATION_REPORTS`. The first line is `Status: decision` (the tab stays open) or `Status: done` (the watcher delivers it, then closes the tab, or sends `/clear` to a standing manager once its pane is idle; a kept manager is never closed or cleared, the human closes it). The watcher sends the coordinator `[worker-report] <path>` once per file, retrying every 15 seconds while the coordinator is blocked. It also sends:

- `[worker-report] <name> exited without a report`, once per pane, when a manager's pane is gone.
- `[watcher] <name> looks stuck: <reason>. Assume the worst and kick it.`, one line with no pane text, checked every 30 seconds for each manager and work tab and sent once per stall. A tab looks stuck when it shows no activity for `STALL_SECONDS` (default 600) and both hold: its job is open (the newest real prompt in its session transcript, from `manager-send`, a lead or a human, is newer than every `result-*.md`; no prompt found counts as open) and no Bash-tool shell or monitor is alive under its claude process. A permission prompt that has stood for 60 seconds (rechecked on screen just before sending) or a guard that has refused the tab 3 times within `STALL_SECONDS` is sent regardless. Activity is a change to the session or a subagent transcript, a report, or a shell under the tab that is using CPU. The tab re-arms on new activity, and a restart does not repeat the line. The reaper also spares the shells of a tab whose last turn is a `WAITING:` message under 2 hours old. A manager whose newest report is `Status: done` is not checked.

State is kept in `<root>/.watch-state.json`. The root is `WORKSTATION_REPORTS_ROOT`, default `~/.local/state/workstation/reports`.

## Hooks

Active only where `WORKSTATION_REPORTS` is set, so only in manager sessions. [Hooks](hooks.md) lists their events.

- `report-format-guard.py` blocks a file in the reports folder that is not named `result-*.md` (or the `.draft` that is moved to such a name) or whose first line is not a Status line, and prints the correct command.
- `manager-brief-inject.py` returns `claude/templates/manager-brief.md` after a compact or clear, and on every session start records `session_id` in manager.json. A lead (`WORKSTATION_ROLE=lead`) gets `claude/templates/lead-brief.md` on every source. Manager and work tabs start with `WORKSTATION_ROLE=work`.

## The watcher agent

`launchd/dev.workstation.herdr-report-watch.plist` runs `herdr-report-watch` with `KeepAlive` and logs to `~/Library/Logs/herdr-report-watch.log`. `install.sh` renders it into `~/Library/LaunchAgents/` (`__ROOT__` is the install root, `__HOME__` your home) and loads it with `launchctl bootstrap`, on macOS when `herdr` is on `PATH`. Re-running replaces a changed plist and leaves an unchanged, loaded one alone. `install.sh uninstall` boots it out and removes the file. On other systems, run `herdr-report-watch` yourself.
