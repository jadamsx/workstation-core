# Hooks

Hooks are scripts in `claude/hooks/`. The settings wire them to tool events, and a hook that exits 2 blocks the call and sends its message back to Claude. Each hook's docstring is the full rule.

| Hook | Event and tool | What it blocks or does |
| --- | --- | --- |
| `pre-commit-guard.py` | Before Bash | `git commit`, `gh pr create` or `edit`, `glab mr create` or `update` when the staged diff holds AI-style comments, the repo has no pre-commit git hook, or the change title or description breaks the rules in `hooks.d` |
| `pre-push-guard.py` | Before Bash | `git push` until pre-commit passes on the diff, the open change has no required ticket key, still holds template placeholder text, or is already approved |
| `rm-guard.py` | Before Bash | Recursive `rm` outside `$TMPDIR`, the drafts folder, `~/.cache`, a repo's `.claude/worktrees/*` and build folders such as `node_modules` and `dist`. Also denies `rm` with recursive and force flags anywhere in the command text, even quoted, and `dangerouslyDisableSandbox` on a command that is not on `sandbox.excludedCommands` (every part split on an unquoted `&&`, `||`, `;`, `\|`, `&`, newline or parenthesis must match, and a redirect or command substitution outside single quotes is denied; an unreadable excluded list is denied too). Recursive and force flags are found wherever they sit among the `rm` arguments, including after the operand |
| `env-file-guard.py` | Before Edit, Write | Edits to real `.env.*` files. `.env.example`, `.sample` and `.template` stay editable |
| `drafts-layout-guard.py` | Before Edit, Write | Writes under the drafts or notes folder whose first path part is not allowed, and writes under retired paths |
| `shared-env-guard.py` | Before the Playwright navigate, type, fill, evaluate and upload tools | Typing, filling or uploading while the page sits on a host in `shared-envs.txt` |
| `agent-model-gate.py` | Before Agent | A subagent spawn that would run on the session model or the wrong model for the agent |
| `main-thread-gate.py` | Before Edit, Write, NotebookEdit, Bash, Agent, and on prompt submit | The main thread editing files or running tests, builds, linters and formatters. Put `main-thread-ok` in a prompt to lift it for that turn. With `WORKSTATION_ROLE=ask` it is an allowlist: no file edits, only read-only agents (`code-locator`, `researcher`, `change-reader`, `release-state-reader`, `run-digest`, `web-fetch`, `Explore`), and Bash may not name `herdr` or `manager-` except `herdr pane read|list`, `herdr tab list`, `herdr workspace list|get`, `herdr agent list`; `main-thread-ok` does not lift that. With `WORKSTATION_ROLE=lead` it denies spawning `builder`, `builder-small`, `rebase-resolver` and the review agents (`cold-reviewer`, `security-reviewer`, `finding-refuter`, `approach-reviewer` and the rest of `engines/review.md`) and points to `manager-send work`; `main-thread-ok` does not lift that either. In every role, for every caller, it denies writes to protected config paths, compared case-insensitively on both the given and the symlink-resolved path (`.git`, a `.git` file, `.husky`, `.claude` except `worktrees/<name>`, `plans/<file>` and memory notes; shell rc files, `.npmrc`, `.mcp.json`, `.pre-commit-config.yaml` and the rest of `PROTECTED_FILES` only directly under the home directory) and tells the agent to write a decision report |
| `notes-lint-guard.py` | After Edit, Write | Nothing. It runs `notes-lint` on a note you just wrote and hands failures back to Claude |
| `report-format-guard.py` | Before Write and Bash, manager sessions only | A manager report that is not `result-*.md` with a `Status: decision` or `Status: done` first line |
| `manager-brief-inject.py` | Session start: every source for a lead (`WORKSTATION_ROLE=lead`), compact or clear for a manager | Hands the lead or manager brief back as context. For a manager it also stores `session_id` in manager.json |
| `project-context.py` | Session start | Nothing. It loads the project's index note into the session, capped at 4000 characters |

## Permission rules

`claude/settings.base.json` also denies these commands outright: `git commit --no-verify` and `-n`, `git push --no-verify`, force pushes, `git reset --hard`, `git clean`, `git stash`, `git restore`, `git checkout --`, `docker volume rm`, `docker system prune -a`, and reads of `~/.ssh` and `~/.aws`. Merges (`gh pr merge`, `glab mr merge`) and pushes of tags and to `main`, `master` or `develop` ask first.

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
