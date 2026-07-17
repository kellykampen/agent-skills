---
name: social-capture
description: Capture social media content (YouTube transcripts, X threads) and save to Obsidian. Use this skill when a URL is posted in the Social Telegram topic (530).
---

# Social Content Capture

## CRITICAL: Obsidian Path

**ALWAYS use the iCloud Obsidian vault path:**
```
/Users/greg/Library/Mobile Documents/iCloud~md~obsidian/Documents/Ideaverse/Social/
```

**DO NOT use** `/Users/greg/Ideaverse/` - that's a stale local copy.

## Overview

Automatically captures content from social platforms and saves organized transcripts/content to Obsidian.

**Purpose:** Extract and archive social media content for later reference.

## When to Use

- YouTube URL posted in Social topic (530)
- X/Twitter post URL posted in Social topic
- Any social platform URL in Social topic

## Available Scripts

Located in `scripts/`:

| Script | Purpose | Usage |
|--------|---------|-------|
| `extract-youtube.py` | Extract YouTube transcript only | `python scripts/extract-youtube.py <url>` |
| `watch_youtube.py` | Download video + extract frames + transcript | `python scripts/watch_youtube.py <url>` |
| `extract_frames.sh` | Extract JPG frames from a video file | `./scripts/extract_frames.sh <video_path> --max-frames 30` |
| `save-x-post.py` | Save X/Twitter post to Obsidian | `python scripts/save-x-post.py <username> <title>` (pipe content) |

## CRITICAL: Acknowledge Immediately — Before Any Processing

**The FIRST thing you do when any URL arrives is send an instant acknowledgment to Telegram.** Do this before opening any browser, running any script, or doing anything else.

```python
import sys
sys.path.insert(0, '/Users/greg/codebase/telegram-claude')
from telegram_sender import send_to_telegram
send_to_telegram(topic_id=530, text="Got it, processing...")
```

This fires in under 1 second. Greg should never be left wondering if his message was received.

## Workflow

### YouTube URL Detection

When a message in Social topic contains a YouTube URL:

1. **Send immediate acknowledgment** (see above)
2. Detect YouTube URL pattern (`youtube.com/watch` or `youtu.be/`)
3. Check for `--watch` flag (see Watch Mode below)
4. Run the appropriate script
5. **Read the saved transcript file**
6. **Write a proper summary** to the channel folder (not transcripts/) — with real content from the transcript, using the frontmatter template below
7. Reply to Telegram with result — only AFTER both transcript AND summary are saved

**CRITICAL: The task is NOT done until the summary is written. Do NOT reply to Telegram after step 2. The summary is mandatory, not optional. Never report done with only the transcript saved.**

### Standard Execution (transcript only — default)

```python
from youtube_extractor import extract_youtube

result = extract_youtube(url)

if result["success"]:
    reply = f"Saved: Social/YouTube/{result['channel']}/{result['file_path'].split('/')[-1]}"
else:
    reply = f"Failed: {result['error']}"
```

### Watch Mode (frames + transcript — opt-in)

**Trigger:** Message contains `--watch`, or Greg says "watch this", "analyse the visuals", "frame by frame".

```python
import sys
sys.path.insert(0, '/Users/greg/codebase/telegram-claude/.claude/skills/social-capture/scripts')
from watch_youtube import watch_youtube

result = watch_youtube(url)  # returns all extract_youtube keys + frames list + frames_dir
```

**After calling watch_youtube:**

1. Read the transcript from `result["file_path"]`
2. Read each frame image using the `Read` tool — Claude sees them as images
3. Write a rich visual summary to the channel folder (see Visual Summary Format below)
4. Copy the frames Claude actually uses into the Obsidian **sources** attachment folder:
   - Path: `sources/Social/YouTube/<Channel>/<YYYY-MM-DD-slug>/<video-slug>-001.png`
   - e.g. `sources/Social/YouTube/The Inner Circle Trader/2020-05-08-OTE-Vol-01/ote-vol01-001.png`
   - Full path: `/Users/greg/Library/Mobile Documents/iCloud~md~obsidian/Documents/Ideaverse/sources/Social/YouTube/<Channel>/<date-slug>/`
   - **Never put frames in the channel notes folder** — they pollute the file browser and break the reading experience
   - **CRITICAL: Use a video-slug prefix on every frame filename** — e.g. `judas-swing-001.png`, `ote-vol01-001.png`. Generic names like `frame-001.png` cause Obsidian vault-wide embed collisions when multiple videos share the same filenames.
   - Obsidian resolves `![[filename]]` vault-wide — unique prefixes ensure the right images always load
5. Delete `result["frames_dir"]` (temp dir) after copying the keepers
6. Reply to Telegram: "Saved with visual summary — X frames embedded"

**CRITICAL: Do NOT save all frames. Only save the ones you embed in the summary. Discard the rest.**

**CRITICAL: Frames ALWAYS go in `sources/Social/YouTube/<Channel>/<date-slug>/`. Never in the notes folder.**

**CRITICAL: Frame filenames MUST use a video-slug prefix — `<video-slug>-NNN.png`. Never `frame-NNN.png`. Generic names collide across videos.**

### Visual Summary Format (Watch Mode only)

The summary file should read like a beautifully structured article with screenshots at the right moments:

```markdown
---
title: "Video Title"
source: "https://youtu.be/xxxxx"
author: "Channel Name"
published: 2026-01-10
created: 2026-01-11
description: "Brief description"
tags:
  - "youtube"
  - "watch"
  - "topic-tag"
---

# Video Title

**Channel:** Name | **Published:** date | **Duration:** Xm

## Overview

2-3 sentence intro of what the video covers.

## Key Section Heading

Paragraph summarising this section of the video.

![[frame-003.png]]
*Caption: what this frame shows and why it matters*

## Next Section

Continue the pattern — text, then frame where the visual adds real context.

![[frame-011.png]]
*Caption: description*

## Key Takeaways

- Bullet point summary
- Of the most important points
```

**Rules for frame selection:**
- Only embed a frame when it adds real context (diagram, code, data, UI demo, slide)
- Skip frames of talking heads with nothing on screen
- **NEVER save intro slides, title cards, logo animations, legal disclaimers, or outro screens** — these are always the first and last frames and are completely useless
- **NEVER save near-duplicate frames** — if the same chart appears across 4 consecutive frames with only the cursor position changing, pick one and discard the rest
- **Always review every extracted frame before saving** — do not blindly copy all frames to Obsidian
- 3-8 frames is the right range for most videos
- Write a caption for every embedded frame that accurately describes what is actually visible in that specific frame

### X/Twitter URL Detection

When a message in Social topic contains an X/Twitter URL:

1. **Send immediate acknowledgment** (see top of Workflow section)
2. Detect X URL pattern (`x.com/*/status/` or `twitter.com/*/status/`)
3. Use **Brave MCP** to open the URL and extract full content (handles note tweets)
3. **Use the save script** to ensure correct Obsidian path
4. Reply to Telegram with saved path

**IMPORTANT:** Always auto-save X posts to Obsidian. Do not ask for confirmation.

**CRITICAL: BRAVE ONLY — NEVER Chrome MCP for X posts.** Greg's X account is only logged in on Brave. Chrome MCP will not have access to X content.

**Extraction Method:** Brave MCP (`brave_get_text`) + save script

**CRITICAL: NEVER use `brave_new_tab` for X posts.** New tabs can open in Profile 6 (youtube-history) where X is NOT logged in. Always use `brave_navigate` on an existing Profile 1 tab, then restore it when done.

```python
# 1. Get current tabs — find a Profile 1 tab to reuse
tabs = mcp__brave-browser__brave_tabs()
# SKIP: studio.youtube.com, youtube.com/watch (Profile 6), grok.com (hangs on navigation)
# PREFER: gmail, airbnb, booking.com, cloudflare, about:blank, chrome://newtab
profile1_tab = next(t for t in tabs if
    "studio.youtube" not in t["url"] and
    "youtube.com/watch" not in t["url"] and
    "grok.com" not in t["url"]
)
original_url = profile1_tab["url"]

# 2. Navigate that tab to the X URL
mcp__brave-browser__brave_navigate(tabId=profile1_tab["id"], url=x_url)
# Wait ~3 seconds for page to load

# 3. Extract text content
content = mcp__brave-browser__brave_get_text(tabId=profile1_tab["id"])

# 4. Restore the tab to its original URL
mcp__brave-browser__brave_navigate(tabId=profile1_tab["id"], url=original_url)

# 5. Parse content and save using the script (ensures correct iCloud path)
```

**Or via bash:**
```bash
echo "$MARKDOWN_CONTENT" | python .claude/skills/social-capture/scripts/save-x-post.py "username" "Post title"
```

**Why browser over scraping:** Scrapers truncate "note tweets" (long-form posts >280 chars). Browser renders the full content.

**NEVER use Apify, WebFetch, or any scraper for X posts.** Always use Brave MCP. NEVER use Chrome MCP — X is only logged in on Brave. If Brave MCP fails, report the error to the user — do NOT fall back to scrapers or Chrome.

### Other URLs (Articles, Blog Posts, Unknown Sites)

**CRITICAL: Do NOT use browser MCP for unknown/external sites.** Browser requires user approval for new domains.

For any URL that is NOT YouTube or X/Twitter, use **WebFetch**:

```python
# Use WebFetch tool - no browser approval needed
WebFetch(
    url="https://example.com/article",
    prompt="Extract the main content, key points, strategies, tips, and recommendations from this article. Provide a structured summary."
)
```

**ALWAYS auto-save article summaries to Obsidian** under `Social/Articles/` with proper frontmatter.

**Article saving workflow:**
1. Use WebFetch to extract content
2. Create markdown file with YAML frontmatter (see Article Template below)
3. Save to: `/Users/greg/Library/Mobile Documents/iCloud~md~obsidian/Documents/Ideaverse/Social/Articles/YYYY-MM-DD-Article-Title.md`
4. Reply to Telegram with saved path and brief summary

**Do NOT ask for permission** - just extract and save automatically like X posts and YouTube videos.

**When to use what:**
| URL Type | Tool | Reason |
|----------|------|--------|
| `youtube.com`, `youtu.be` | `extract-youtube.py` script | Uses yt-dlp, no browser |
| `x.com`, `twitter.com` | Brave MCP | X is logged in on Brave only, need JS for full content |
| `github.com` | GitHub API via curl | No browser needed, see GitHub section below |
| Everything else | WebFetch | No browser approval needed |

### GitHub URL Detection

For GitHub repos, use the **GitHub API via curl** (no browser needed):

```bash
# List repo contents
curl -s https://api.github.com/repos/OWNER/REPO/contents | jq -r '.[].name'

# Get raw file content
curl -s https://raw.githubusercontent.com/OWNER/REPO/main/PATH/TO/FILE

# Get repo metadata
curl -s https://api.github.com/repos/OWNER/REPO | jq '{name, description, stargazers_count, language}'
```

**GitHub extraction workflow:**
1. Parse owner/repo from URL: `github.com/OWNER/REPO`
2. Fetch README: `curl -s https://raw.githubusercontent.com/OWNER/REPO/main/README.md`
3. If code review needed, fetch specific files via raw.githubusercontent.com
4. Save summary to `Social/GitHub/OWNER-REPO.md` or `Social/X/username/` if linked from X post

**IMPORTANT:** When an X post links to GitHub, include security review of the code in the Obsidian note. Check for:
- Input sanitization
- Prompt injection vulnerabilities
- API key handling
- Dependencies

### URL Detection Patterns

```python
import re

YOUTUBE_PATTERN = r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]+'
X_PATTERN = r'(https?://)?(www\.)?(x\.com|twitter\.com)/\w+/status/\d+'
# Everything else → WebFetch
```

## File Structure

Content is saved to Obsidian:

```
Ideaverse/Social/
├── YouTube/
│   ├── <Channel Name>/
│   │   ├── <Topic>-Summary.md          ← Summary file (created after extraction)
│   │   └── transcripts/
│   │       └── YYYY-MM-DD-Video-Title.md  ← Raw transcript
│   └── <Other Channel>/
├── X/
│   ├── <Username>/
│   │   └── YYYY-MM-DD-Tweet-excerpt.md
│   └── <Other User>/
├── GitHub/
│   └── <repo-name>.md
└── Articles/
    └── YYYY-MM-DD-Article-Title.md
```

**YouTube Summary Location:** Summaries go in the channel folder (e.g., `YouTube/Ali Khan/SMT-Model-Summary.md`), NOT in the transcripts folder.

**YouTube Summary Naming:** Topic-first, no date prefix. Use the video topic as the filename, not the publish date.
- Correct: `OTE-Pattern-Recognition-Vol-01-Summary.md`
- Wrong: `2020-05-08-OTE-Pattern-Recognition-Vol-01-Summary.md`

The date belongs in the frontmatter (`published:` field), not the filename. This keeps the channel folder sorted by topic, not by date, which is far more useful when browsing.

**Watch Mode images:** All frames go in the Obsidian `sources/` folder (never in the notes folder):
```
Ideaverse/sources/Social/YouTube/<Channel>/<YYYY-MM-DD-slug>/frame-001.png
```
This is Obsidian's configured attachment root. The notes folder stays clean with only `.md` files.

## CRITICAL: No Spaces in Filenames

**ALL filenames MUST use hyphens instead of spaces.** This makes paths copy-pasteable in terminals.

- Use: `2026-02-05-Outrank-Local-Business.md`
- NOT: `2026-02-05 - Outrank Local Business.md`

The `save-x-post.py` script and `youtube_extractor.py` handle this automatically. When saving files directly (articles, GitHub), always replace spaces with hyphens in the filename.

## CRITICAL: Frontmatter Template

**ALL social captures MUST include YAML frontmatter at the top of the file.**

### X/Twitter Template
```yaml
---
title: "Post Title"
source: "https://x.com/username/status/123456789"
author: "@username"
published: 2026-01-10
created: 2026-01-11
description: "Brief 1-line description of what the post covers"
tags:
  - "x-post"
  - "topic-tag"
---
```

### YouTube Template
```yaml
---
title: "Video Title"
source: "https://youtube.com/watch?v=xxxxx"
author: "Channel Name"
published: 2026-01-10
created: 2026-01-11
description: "Brief description of video content"
tags:
  - "youtube"
  - "topic-tag"
---
```

### GitHub Template
```yaml
---
title: "Repo Name"
source: "https://github.com/owner/repo"
author: "owner"
published:
created: 2026-01-11
description: "What the repo does"
tags:
  - "github"
  - "tool-type"
---
```

### Article Template
```yaml
---
title: "Article Title"
source: "https://example.com/article"
author: "Author Name"
published: 2026-01-10
created: 2026-01-11
description: "Brief summary"
tags:
  - "article"
  - "topic-tag"
---
```

### Field Definitions

| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Post/video/repo title |
| `source` | Yes | Original URL |
| `author` | Yes | Username/channel (with @ for X) |
| `published` | No | Date content was originally published (if known) |
| `created` | Yes | Date we captured it (today) |
| `description` | Yes | Brief 1-line summary |
| `tags` | Yes | Always include platform tag + topic tags |

### Example Complete X Post

```markdown
---
title: "How I Use Claude Code - Creator Setup"
source: "https://x.com/bcherny/status/2007179832300581177"
author: "@bcherny"
published: 2026-01-03
created: 2026-01-11
description: "Boris Cherny (Claude Code creator) shares his personal 13-tip setup"
tags:
  - "x-post"
  - "claude-code"
  - "workflow"
  - "tips"
---

# How I Use Claude Code - Boris Cherny's Personal Setup

[Rest of content...]
```

## References

Located in `references/`:
- `platforms.md` - Supported platforms and extraction methods

## Response Format

**IMPORTANT: Always reply to Telegram when done.** The user shouldn't have to ask if you're finished.

After saving content, your terminal response IS the Telegram reply. Keep it concise:

**Success:**
```
Saved: Social/X/username/2025-01-06-Post-title.md

Brief 1-line summary of what the post is about.
```

**With due diligence:**
```
Saved: Social/X/username/2025-01-06-Post-title.md

Brief summary + added due diligence notes from [site].
```

**Failure:**
```
Failed: No subtitles found for this video
```

**Do NOT** make the user ask "is that done?" - your response confirms completion.

## CRITICAL: Telegram Update Required — DIRECT SEND, NOT RESPONSE WATCHER

**After all processing is done, you MUST send the result directly to Telegram using telegram_sender. Do NOT rely on the response watcher picking up your text output — it may time out before you finish.**

```python
import sys
sys.path.insert(0, '/Users/greg/codebase/telegram-claude')
from telegram_sender import send_to_telegram
send_to_telegram(topic_id=530, text="Saved: Social/X/username/2026-04-28-Post-title.md\n\nBrief summary of what the post is about.")
```

This is mandatory. The response watcher cannot be relied upon for on-demand sessions doing long tasks. Direct send ensures Greg always gets the reply.
