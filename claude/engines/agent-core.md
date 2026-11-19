# Agent core

Every spawned agent loads this file.

## Git and worktrees
- Work only in the worktree you were given, at `<repo>/.claude/worktrees/<key>`. Never check out or switch branches in the owner's own tree.
- Never `git checkout --`, `restore` or `stash` with uncommitted changes. Back out a rebase with `git rebase --abort`.
- Pinned worktrees are read-only. A run that needs a changed file happens on a scratch copy under `$TMPDIR`, deleted after. Mutation checks use the same copy.
- Never push. A push goes through the owning engine and the owner's OK (`engines/common.md`). Never force-push; `--force-with-lease` only on your own change branch, clean tree, where the owning engine allows pushing.

## Agent rules
- Every agent is read-only except `builder`, `builder-small`, `comment-cutter` and `rebase-resolver`. It edits no repo file, posts nothing, and never edits pinned worktrees. Asked otherwise: `Read-only. Use builder.`
- A refusal is one line: `<slug>. ask: <one question>.` Shared slugs: `no-url` (a running URL is needed), `shared-env` (agents that type, fill or load a system refuse shared or production URLs), `ambiguous` (the spec allows two readings), `needs-confirm` (a destructive step needs the owner's OK), `scope-grew` (work outside the listed files), `missing-seam` (something the task needs does not exist).
- Proof that cannot be made to pass in two attempts: stop and show the error. After two failed corrections on the same point, suggest `/clear` with a restated task.
- The model lives only in an agent's frontmatter. Engines, skills and prompts never state or override it; a review that must be stronger than its author changes the pin, not the call.
- Say what you ran versus what you only read, and what you could not check.

## Shell
- Never set `dangerouslyDisableSandbox` pre-emptively. After a real denial retry once unsandboxed, never for `rm`, `cp` or `mv` outside allow paths, `curl`, `wget`, `ssh`, `scp`, anything touching `~/.ssh`, `~/.aws`, credentials or `~/.claude.json`, `osascript`, `open`, `sudo`, `chmod` or `kill`. If the retry is blocked or would prompt, report a decision and never wait on a prompt. Never use it for `ps` or `kill`: to stop a stuck shell run `shell-reap <pid>`.
- A search that may find nothing ends in `|| true`; a final step whose non-zero exit is only a result ends in `; true`.
- Check a path exists before `ls`, `cat` or `rg` on it.
- macOS `sed -i` needs `sed -i ''`; use python, or better the Edit tool.
- Never use `rm -r` or `herdr workspace close`; hooks block them.
- Never write `rm -rf` in any command, even quoted or as test text: Claude Code prompts on it even in bypass mode. Move things to `~/.Trash` instead.
- Never `git stash`: commit the work, or use a worktree. `git stash list` and `git stash show` are read-only and allowed.
- Never `sleep` or poll in a loop: run the command with `run_in_background` and wait for its notice.
- Every commit and change title starts with a gitmoji.

## Findings file
When a prompt names a findings path, write the agent's full output to it with one Write call, the only write you make. Read the `brief.md` it names, and use its `diff.patch` and `files.txt` instead of running `git diff` or `git show` over the whole change; `git log`, `blame` and `show` on single files stay fine. Then return only `<path> | <counts by the severity words of the agent's output, or the total> | top: <the worst finding in one line>`. Without a path, return the output inline.

## Lead brief
A `[watcher] looks stuck` line means kick the tab at once (tell it to continue, unblock it, or give it the next node); ask the owner only if kicking fails. Read a report's `Status` and `BLUF` lines first and open the rest only when needed to act.

## Report skeleton
Every report: the result first, then the evidence, one line per item. Then `Ran:` the commands with results, `Not changed:` what you could have changed and did not, `Omitted:` each omission with its trigger, `Out:` items that need the owner's OK. An empty line is omitted, not filled. Each engine adds its own rows to this shape.
