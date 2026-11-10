# Hooks

Hooks are scripts in `claude/hooks/`. The settings wire them to tool events, and a hook that exits 2 blocks the call and sends its message back to Claude. Each hook's docstring is the full rule.

| Hook | Event and tool | What it blocks or does |
| --- | --- | --- |
| `pre-commit-guard.py` | Before Bash | `git commit`, `gh pr create` or `edit`, `glab mr create` or `update` when the staged diff holds AI-style comments, the repo has no pre-commit git hook, or the change title or description breaks the rules in `hooks.d` |
| `pre-push-guard.py` | Before Bash | `git push` until pre-commit passes on the diff, the open change has no required ticket key, still holds template placeholder text, or is already approved |
| `rm-guard.py` | Before Bash | Recursive `rm` outside `$TMPDIR`, the drafts folder, `~/.cache`, a repo's `.claude/worktrees/*` and build folders such as `node_modules` and `dist` |
| `env-file-guard.py` | Before Edit, Write | Edits to real `.env.*` files. `.env.example`, `.sample` and `.template` stay editable |
| `drafts-layout-guard.py` | Before Edit, Write | Writes under the drafts or notes folder whose first path part is not allowed, and writes under retired paths |
| `shared-env-guard.py` | Before the Playwright navigate, type, fill, evaluate and upload tools | Typing, filling or uploading while the page sits on a host in `shared-envs.txt` |
| `agent-model-gate.py` | Before Agent | A subagent spawn that would run on the session model or the wrong model for the agent |
| `main-thread-gate.py` | Before Edit, Write, NotebookEdit, Bash, and on prompt submit | The main thread editing files or running tests, builds, linters and formatters. Put `main-thread-ok` in a prompt to lift it for that turn |
| `notes-lint-guard.py` | After Edit, Write | Nothing. It runs `notes-lint` on a note you just wrote and hands failures back to Claude |
| `project-context.py` | Session start | Nothing. It loads the project's index note into the session, capped at 4000 characters |

## Permission rules

`claude/settings.base.json` also denies these commands outright: `git commit --no-verify` and `-n`, `git push --no-verify`, `gh pr merge`, `glab mr merge`, force pushes, `git reset --hard`, `git clean`, `git stash`, `git restore`, `git checkout --`, `docker volume rm`, `docker system prune -a`, and reads of `~/.ssh` and `~/.aws`. Pushes of tags and to `main`, `master` or `develop` ask first.

## Hook data in `hooks.d`

The guards read optional rules from every `*.json` in `claude/hooks/hooks.d/`, through `hook_config.py`. [Configuration](configuration.md#hook-rules-in-hooksd) explains the file format and merge order. Each hook reads the files once, when it starts.

| Key | Used by | Effect |
| --- | --- | --- |
| `change.require_gitmoji` | `pre-commit-guard` | A commit message or change title must start with an emoji or a `:shortcode:` |
| `change.title_requires_ticket` | both git guards | A change title needs a ticket key |
| `change.commit_forbids_ticket` | `pre-commit-guard` | A commit message given with `-m` must not carry a ticket key |
| `change.ticket_key` | both git guards | Regular expression for a ticket key. Default `[A-Z][A-Z0-9]+-\d+` |
| `change.commit_ticket_key` | `pre-commit-guard` | Key pattern for the commit message check. Falls back to `ticket_key` |
| `change.ticket_exempt_projects` | both git guards | Project path prefixes (case-insensitive) whose changes need no key. The path comes from the source control project id, else the `origin` remote |
| `change.description_cut_markers` | `pre-commit-guard` | Text after which a description is generated, so everything from the first marker on is left out of the checks |
| `change.placeholders` | `pre-push-guard` | Template text that blocks a push when a change description still holds it, on top of the built-in phrases |
| `opus_override` | `agent-model-gate` | Agent names that may be spawned on Opus by explicit override |
| `lint_skipped` | `notes-lint-guard` | Vault folders to skip, on top of `templates`, `.obsidian`, `.git` and `.githooks` |
| `drafts_allowed`, `notes_allowed` | `drafts-layout-guard` | Extra top-level names allowed in the drafts folder and the notes vault |
| `retired_paths` | `drafts-layout-guard` | Paths (`~` allowed) where writes are blocked and redirected to the project folder in drafts |

`shared-envs.example.txt` shows the host list for `shared-env-guard`: copy it to `shared-envs.txt` beside the hook, or point `SHARED_ENVS_FILE` at your own. An entry matches the exact host, or any subdomain when it starts with a dot. With no file, nothing is shared.
