# Configuration and migration

Scripts read `${XDG_CONFIG_HOME:-~/.config}/social-capture/config.json` when present.
Set `SOCIAL_CAPTURE_CONFIG` to select another JSON file. An explicitly selected missing
file is an error. Keep this file outside the skill so skill updates preserve settings.

For a vault with the default `x/bookmarks` and `youtube` subfolders:

```json
{
  "vault_path": "/absolute/path/to/your/vault",
  "categories": ["research", "tools", "misc"],
  "application_heading": "How to apply"
}
```

To preserve an existing folder structure, set the final destination folders directly:

```json
{
  "bookmarks_path": "/absolute/path/to/your/vault/Reference/Social/X-Bookmarks/bookmarks",
  "youtube_path": "/absolute/path/to/your/vault/Personal/YouTube"
}
```

For each platform, destination precedence is:

1. `OBSIDIAN_BOOKMARKS_PATH` or `OBSIDIAN_YOUTUBE_PATH` environment variable.
2. `bookmarks_path` or `youtube_path` in the JSON configuration.
3. `OBSIDIAN_VAULT_PATH` environment variable, otherwise `vault_path` in configuration,
   followed by `x/bookmarks` for X or `youtube` for YouTube.

No destination means normal saves fail before writing. Dry runs need no destination
and write only to `--out-dir`, which defaults to `./rendered-notes`.

`categories` is an optional allowlist. When set, an unknown category becomes `misc`.
When omitted, any category made of letters, digits, underscores, and hyphens is accepted.
Missing or empty categories become `misc`. `tags`, `key_points`, and `how_to_apply` must
be arrays of strings. `application_heading` defaults to `How to apply`.

## Upgrading older installations

- Back up the installed skill before replacing it. Put any vault paths or personal
  category/heading preferences in the external configuration file first.
- The old `OBSIDIAN_SOCIAL_PATH`, hardcoded vault names, Telegram topic, and external
  `youtube_extractor` module are no longer used. Set the destinations above explicitly.
- The old X raw-markdown positional/file interface is replaced by `--json --in FILE`
  or JSON on stdin. Update calling jobs before switching them over. Extraction also
  returns JSON instead of automatically writing vault notes.
- Filenames now contain source IDs. Existing notes are not renamed or migrated.
  Check for an older note for the same source before re-capturing it; this version
  does not deduplicate across old filenames or changed titles/dates.
- Existing files are never overwritten. To revise a saved note, review it and use an
  explicit editing workflow rather than repeatedly calling the saver.
- The scripts do not depend on a daily bookmark/playlist job. A bulk job can reuse the
  JSON interface, but its scheduling, deduplication, and authentication remain separate.

Verify destinations with a synthetic record and `--dry-run --out-dir` before a live save.
