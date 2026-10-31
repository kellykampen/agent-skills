# Platform extraction

## YouTube

The self-contained extractor calls `yt-dlp --dump-json --no-playlist` for metadata,
then downloads manual or automatic WebVTT subtitles into a temporary folder. It strips
cue timestamps and markup and removes consecutive repeated subtitle lines.

Configure the executable with `YT_DLP_BIN`, otherwise it resolves `yt-dlp` on `PATH`.
`YT_SUB_LANGS` defaults to `en.*,en`. Browser cookies are off by default; use
`YT_DLP_COOKIES_BROWSER` to select an authorized browser when required.

Successful metadata extraction returns `success: true` even when subtitles are absent
or subtitle extraction fails. `transcript_available: false` indicates a metadata-only
capture; the script does not currently distinguish absent captions from subtitle-fetch
errors. Metadata failures return `success: false` and an error message.

Watch mode downloads a video at up to 720p and calls the included frame extractor.
It deletes its downloaded video folder on success or failure. Successful PNG frames
remain in the returned `frames_dir` until the caller removes them.

## X/Twitter

Read rendered post text with an available authorized browser tool. Existing Finch
access may supply metadata or fallback text. Source completeness depends on the client
and API response; mark partial captures with `truncated: true` and report the limitation.
The saver retains `author_id` when the author name and handle are unknown.

The scripts render supplied records; they do not authenticate to X, read bookmarks,
or configure browser sessions. No paid scraper is required.
