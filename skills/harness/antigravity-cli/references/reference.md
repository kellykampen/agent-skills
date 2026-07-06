# `agy` Reference — flags, slash commands, config, plugins, MCP

Companion to `SKILL.md`. Read this when a task goes past headless one-shots. Ground truth is
always the installed CLI — verify with `agy --help`, `agy help`, `agy models`, and
`agy plugin help`, since flags and models change between versions.

## All CLI flags (from `agy --help`, v1.0.16)

| Flag | Meaning |
| --- | --- |
| `-p`, `--print`, `--prompt` | Run a single prompt non-interactively and print the response. |
| `-i`, `--prompt-interactive` | Run an initial prompt, then continue interactively. |
| `-c`, `--continue` | Continue the most recent conversation. |
| `--conversation <ID>` | Resume a previous conversation by its UUID. |
| `--model <STRING>` | Model for this session. Use exact display strings from `agy models`. |
| `--add-dir <PATH>` | Add a directory to the workspace (repeatable). |
| `--project <ID>` | Use an existing project for the session. |
| `--new-project` | Create a new project for this session. |
| `--sandbox` | Run in a sandbox with terminal restrictions enabled. |
| `--dangerously-skip-permissions` | Auto-approve all tool permission requests. |
| `--print-timeout <DUR>` | Timeout for `--print` waiting (default `5m0s`), e.g. `20m`. |
| `--log-file <PATH>` | Override the CLI debug log path (not the answer output). |

Subcommands: `changelog`, `help`, `install`, `models`, `plugin`/`plugins`, `update`.
- `agy models` — list model strings (copy `--model` values from here).
- `agy update` — update the CLI. `agy changelog` — release notes.
- `agy install` — (re)configure PATH and shell aliases; flags `--skip-aliases`, `--skip-path`.

## Slash commands (interactive TUI)

Type `/` to open the command menu, `?` for help on an empty prompt. Useful ones:

| Command | Purpose |
| --- | --- |
| `/model` | Switch the reasoning model mid-session. |
| `/planning` | Multi-turn plan mode for complex tasks. |
| `/fast` | Fast mode for quick actions. |
| `/resume` (`/switch`, `/conversation`) | Load and resume previous conversation threads. |
| `/rewind` (`/undo`) | Roll conversation history back to an earlier point. |
| `/fork` (`/branch`) | Branch the current session into a parallel one. |
| `/rename`, `/title` | Rename the thread / toggle terminal title updates. |
| `/clear` | Clear the terminal and reset conversation context. |
| `/diff` | Show unified diffs of modified files. |
| `/add-dir`, `/open` | Add a dir to the workspace / open a path in `$EDITOR`. |
| `/config` (`/settings`) | Interactive settings editor. |
| `/permissions` | Switch the permission preset. |
| `/agents`, `/tasks` | Agent Manager (subagent approvals) / Task Manager (shell logs). |
| `/skills`, `/hooks`, `/mcp` | Browse Agent Skills / hooks / MCP servers. |
| `/keybindings`, `/statusline` | Customize key bindings / status bar. |
| `/usage` | Real plan-quota screen ("Models & Quota") -- weekly + 5-hour limits for the Gemini pool and the Claude/GPT pool. |
| `/credits` | Pay-per-token credit balance -- disabled/unused on subscription plans. |
| `/btw` | Ask a side question without derailing the main thread. |
| `/exit`, `/logout` | Close the CLI / remove saved auth tokens. |

## File & context references in prompts

Reference paths inline instead of pasting contents (works in `-p` prompts too):
- `@src/main.go` — a single file
- `@src/` — an entire directory
- `@**/*.ts` — a glob

## Permission presets

Set via `/permissions` or `settings.json`:

| Preset | Behavior |
| --- | --- |
| `request-review` | Default — prompt before tool execution. |
| `proceed-in-sandbox` | Auto-proceed while inside a sandbox. |
| `always-proceed` | Never prompt — proceed automatically (equivalent effect to `--dangerously-skip-permissions`). |
| `strict` | Prompt for all non-read tools. |

## Config & context files

| Path | Role |
| --- | --- |
| `~/.gemini/antigravity-cli/settings.json` | User settings: `model`, `colorScheme`, `permissions.allow`, `trustedWorkspaces`. |
| `~/.gemini/antigravity-cli/keybindings.json` | Key bindings (editable via `/keybindings`; delete to reset). |
| `~/.gemini/antigravity-cli/conversations/<UUID>.db` | Per-conversation SQLite store; the filename is the conversation ID. |
| `~/.gemini/antigravity-cli/conversation_summaries.db` | Index of conversations (`conversation_summaries` table: `conversation_id`, `title`, `preview`, `workspace_uris`, `last_modified_time`). |
| `~/.gemini/config/mcp_config.json` | Global MCP server config. |
| `.agents/mcp_config.json` | Per-workspace MCP server config. |
| `.agents/skills/<name>.md` | Local Agent Skill → becomes a `/<name>` slash command. |
| `.agents/hooks/` | Lifecycle hooks (pre-flight / post-format interceptors). |
| `AGENTS.md` (repo root) | Workspace context/instructions — a cross-agent standard format. Put project rules here so every agy run in the repo inherits them. |

`settings.json` example (note `model` is the same display string as `--model`):
```json
{
  "colorScheme": "dark",
  "model": "Gemini 3.5 Flash (High)",
  "permissions": { "allow": ["command(git diff)", "command(git status)"] },
  "trustedWorkspaces": ["~/code/project"]
}
```

`permissions.allow` entries like `command(git diff)` pre-approve specific tool calls so even a
non-skip run won't stop to ask for them — handy for read-only git commands in headless jobs.

## Plugins

```
agy plugin list                     # list imported plugins
agy plugin install <target>         # supports plugin@marketplace
agy plugin uninstall <name>
agy plugin enable|disable <name>
agy plugin validate [path]
agy plugin import gemini            # migrate Gemini CLI extensions → agy plugins
agy plugin import claude            # migrate Claude plugins → agy plugins
```

## Finding a specific conversation ID to resume

`--conversation <UUID>` needs the ID. To find the right past session by topic:

```bash
# Preferred: query the summaries index by title/preview
sqlite3 ~/.gemini/antigravity-cli/conversation_summaries.db \
  "SELECT conversation_id, title, datetime(last_modified_time) \
     FROM conversation_summaries WHERE title LIKE '%billing%' OR preview LIKE '%billing%' \
     ORDER BY last_modified_time DESC;"

# Fallback (the live agy process may hold summaries in its WAL, returning 0 rows):
# grep the per-conversation DBs for a distinctive keyword and rank by hit count.
cd ~/.gemini/antigravity-cli/conversations
for db in *.db; do n=$(strings "$db" 2>/dev/null | grep -ic billing); \
  [ "$n" -gt 0 ] && echo "$n  $db"; done | sort -rn
```

The filename minus `.db` is the ID. Or, interactively, run bare `agy` and use `/resume` to pick
from a list — no UUID hunting. `-c`/`--continue` only reopens the *most recent* conversation, so
use `--conversation <UUID>` when it isn't the last one you touched.

## Authentication

Desktop: agy opens a browser for OAuth on first run. Headless/SSH: it prints an authorization
URL + one-time code to complete on a machine with a browser. If a run reports it's
unauthenticated, the user must complete login interactively once — you can't script the OAuth
step. (An `ANTIGRAVITY_API_KEY` env var is referenced by some guides for key-based auth; treat
it as unverified and confirm against `agy --help` / current docs before relying on it.)

## Accuracy notes

Third-party blog posts about `agy` circulate some commands that are **not** in the installed
v1.0.16 CLI — e.g. `agy run`, `agy inspect`, a `-m` short flag, `/context`, `/help`, and a
`~/.config/antigravity/config.toml`. Don't rely on those; trust `agy --help` and `agy help`
for this machine's version.
