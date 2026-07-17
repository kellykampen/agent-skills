# Supported Platforms

## YouTube

**Status:** Implemented

**URL Patterns:**
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `youtube.com/watch?v=VIDEO_ID`

**Extraction Method:** `yt-dlp` with `--write-auto-sub`

**Requirements:**
- `yt-dlp` installed via Homebrew
- Brave browser for cookies (bypasses age restrictions)

**Output:** Markdown file with timestamped transcript

---

## X/Twitter

**Status:** Implemented

**URL Patterns:**
- `https://x.com/username/status/ID`
- `https://twitter.com/username/status/ID`

**Extraction Method:** Brave MCP (primary) or Chrome MCP

**Why browser:** Scrapers truncate "note tweets" (long-form posts) to 275 chars. Browser renders full content.

**Brave MCP Workflow:**
1. `brave_launch()` - ensure Brave is running with remote debugging
2. `brave_tabs()` - list available tabs
3. `brave_navigate(url)` - load the tweet
4. `brave_get_page_text()` - extract full content

**Chrome MCP Workflow (if available):**
1. `tabs_context_mcp(createIfEmpty=True)` - get/create tab group
2. `tabs_create_mcp()` - create new tab
3. `navigate(tabId, url)` - load the tweet
4. `get_page_text(tabId)` - extract full content

**NEVER use Apify, WebFetch, or any scraper for X posts.** If browser fails, report the error — do not fall back to scrapers.

**Output:** Markdown file with tweet text, author, date, engagement stats

---

## Podcasts

**Status:** Not implemented

**Notes:** Many podcasts on YouTube can use YouTube extractor.

---

## Articles

**Status:** Not implemented

**Planned Method:** Web scraping with readability extraction.
