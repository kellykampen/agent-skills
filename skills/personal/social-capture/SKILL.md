---
name: social-capture
description: Capture an X/Twitter post or YouTube video into an Obsidian note with a summary, takeaways, and source metadata. Use when the user asks to save a social URL or analyze a video's visuals.
metadata:
  version: "2.0.0"
---

# Social capture

Read the source, synthesize useful notes, and save them through the included scripts.
Capture on demand when the user asks to save a URL. A pasted URL alone does not authorize
saving it or sending messages. Reply with the actual saved path and a short summary.

## Local configuration

Read [references/configuration.md](references/configuration.md) before the first save
or when migrating an older installation. Destinations, category lists, and application
headings belong in local configuration, outside the installed skill folder.

The savers require an explicit vault destination. They never guess a vault name.
`--dry-run --out-dir /path/to/samples` renders notes without a vault configuration.
Dry runs create sample files in that output folder and do not write to the vault.

## YouTube

1. Run `python3 scripts/extract-youtube.py "URL"`. It returns JSON metadata, a plain-text
   transcript, and `transcript_available`. It does not save a note. `yt-dlp` must be on
   `PATH`, or selected with `YT_DLP_BIN`.
2. Read the transcript and create `summary`, `key_points`, optional `how_to_apply`,
   `category`, and `tags`. Merge these with the extracted metadata in a JSON file.
   If the transcript is unavailable, use available metadata and clearly state that
   the note is based on metadata, not a watched or transcribed video.
3. Run `python3 scripts/save-youtube-note.py --json --in /path/to/record.json`.

For visuals, use watch mode only when requested or when visual analysis is part of the
user's task:

```bash
python3 scripts/watch_youtube.py "URL" --max-frames 30
```

Watch mode also requires `ffmpeg` and `ffprobe` on `PATH`. Its JSON includes the transcript,
PNG frame paths, and `frames_dir`. Inspect the frames using an available image tool.
Keep only useful frames in the user's attachment folder, with a video-ID prefix on each
filename. Remove the returned temporary frames folder after inspection or copying.
A `watch_error` means visual analysis failed; report that without claiming to have watched.

Browser cookies are off by default. Set `YT_DLP_COOKIES_BROWSER` only when needed and
authorized. See [references/platforms.md](references/platforms.md) for extraction details.

## X/Twitter

1. Use an available browser tool to read the full post, especially long-form posts.
   Use the user's selected browser and existing access. If an authorized Finch CLI
   is available, its JSON output can supply metadata or act as a fallback. Check the
   returned text for truncation rather than assuming every API response is complete.
2. Synthesize a title, summary, key points, and optional application ideas. Preserve
   the source text separately. If only partial text is available, set `truncated: true`
   and say so in the response. Do not introduce a paid scraping service automatically.
3. Run `python3 scripts/save-x-post.py --json --in /path/to/record.json`.

Required X fields are `tweet_id` and `url`; the date defaults to today. For example:

```json
{
  "tweet_id": "1234567890",
  "url": "https://x.com/example/status/1234567890",
  "title": "A useful technique",
  "author": "Example",
  "author_handle": "@example",
  "category": "research",
  "tags": ["research"],
  "summary": "What the post explains.",
  "key_points": ["The useful takeaway."],
  "full_text": "The original source text.",
  "how_to_apply": ["A concrete next step."],
  "truncated": false
}
```

YouTube records require `video_id`; they may also include `title`, `channel`,
`channel_handle`, `published`, `duration`, `playlist`, and the synthesis fields above.
The URL is derived from the video ID if absent. The savers default missing titles to
`Untitled`, so provide a useful title when metadata is available.

## Saving behavior

Both savers accept `--json`, `--in FILE`, `--dry-run`, and `--out-dir DIRECTORY`.
They emit the actual output path. Frontmatter strings and lists are escaped as YAML.
Notes use `CATEGORY/DATE-TITLE-SOURCE_ID.md`; different source IDs cannot collide just
because titles match. A matching existing filename causes an error rather than an
overwrite. Review existing notes before choosing a separate update or migration action.

Bulk jobs may call these scripts with the same local configuration and record format.
This skill does not install schedules, send Telegram messages, or require external
pipeline scripts. Articles and other platforms are outside this skill's current scope.
