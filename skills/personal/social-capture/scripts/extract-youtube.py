#!/usr/bin/env python3
"""
Extract YouTube video metadata + transcript using yt-dlp (self-contained).

Usage:
    python scripts/extract-youtube.py <youtube_url> [--json] [--out <file.txt>]

Output:
    - Default: prints a JSON object to stdout:
        {
          "success": true,
          "video_id": "...",
          "title": "...",
          "channel": "...",
          "channel_handle": "@...",   # or "" if unknown
          "published": "YYYY-MM-DD",  # or "" if unknown
          "duration": "H:MM:SS",      # or "" if unknown
          "url": "https://www.youtube.com/watch?v=...",
          "transcript": "plain-text transcript (may be empty if no subs)",
          "transcript_available": true/false
        }
      On failure: {"success": false, "error": "..."}
    - With --out <file>: also writes the plain-text transcript to that file.

Requires yt-dlp on PATH, or YT_DLP_BIN pointing to the executable. Extraction never
writes vault notes. Set YT_DLP_COOKIES_BROWSER only when browser cookies are needed.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

YT_DLP = os.getenv("YT_DLP_BIN", "yt-dlp")


def _cookie_args() -> list:
    browser = os.getenv("YT_DLP_COOKIES_BROWSER", "").strip()
    return ["--cookies-from-browser", browser] if browser else []


def _fmt_duration(seconds) -> str:
    try:
        s = int(float(seconds))
    except (TypeError, ValueError):
        return ""
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def _fmt_date(yyyymmdd) -> str:
    if not yyyymmdd or not re.fullmatch(r"\d{8}", str(yyyymmdd)):
        return ""
    s = str(yyyymmdd)
    return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"


def _clean_vtt(vtt_text: str) -> str:
    """Turn a WebVTT subtitle file into de-duplicated plain text."""
    lines = []
    seen_last = None
    for raw in vtt_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        # timestamp cue lines: 00:00:01.000 --> 00:00:03.000 ...
        if "-->" in line:
            continue
        if re.fullmatch(r"\d+", line):  # cue index
            continue
        # strip inline tags like <00:00:01.000> and <c>...</c>
        line = re.sub(r"<[^>]+>", "", line).strip()
        if not line:
            continue
        if line == seen_last:  # auto-subs repeat lines heavily
            continue
        seen_last = line
        lines.append(line)
    return "\n".join(lines)


def extract_youtube(url: str) -> dict:
    """Fetch metadata + transcript for a YouTube URL. Returns a dict (see module docstring)."""
    if not Path(YT_DLP).exists() and not _which(YT_DLP):
        return {"success": False, "error": f"yt-dlp not found: {YT_DLP} (install it or set YT_DLP_BIN)"}

    # 1. Metadata via --dump-json (single network call, no download).
    meta_cmd = [YT_DLP, "--dump-json", "--no-playlist", *_cookie_args(), url]
    try:
        meta_proc = subprocess.run(meta_cmd, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"success": False, "error": str(error)}
    if meta_proc.returncode != 0:
        return {"success": False, "error": f"yt-dlp metadata failed: {meta_proc.stderr.strip()[:300]}"}
    try:
        meta = json.loads(meta_proc.stdout.splitlines()[0])
    except (json.JSONDecodeError, IndexError):
        return {"success": False, "error": "could not parse yt-dlp metadata JSON"}

    video_id = meta.get("id", "")
    handle = meta.get("uploader_id", "") or ""
    if handle and not handle.startswith("@"):
        handle = ""  # uploader_id is sometimes a UC... channel id, not a handle
    result = {
        "success": True,
        "video_id": video_id,
        "title": meta.get("title", ""),
        "description": meta.get("description", ""),
        "channel": meta.get("channel") or meta.get("uploader", ""),
        "channel_handle": handle,
        "published": _fmt_date(meta.get("upload_date")),
        "duration": _fmt_duration(meta.get("duration")),
        "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else url,
        "transcript": "",
        "transcript_available": False,
    }

    # 2. Transcript: download subtitles (prefer manual, fall back to auto) into a temp dir.
    with tempfile.TemporaryDirectory(prefix="yt-subs-") as tmp:
        sub_cmd = [
            YT_DLP, "--skip-download",
            "--write-subs", "--write-auto-subs",
            "--sub-langs", os.getenv("YT_SUB_LANGS", "en.*,en"),
            "--sub-format", "vtt",
            "--no-playlist",
            "--output", str(Path(tmp) / "%(id)s.%(ext)s"),
            *_cookie_args(),
            url,
        ]
        try:
            subprocess.run(sub_cmd, capture_output=True, text=True, timeout=180)
        except (OSError, subprocess.TimeoutExpired):
            pass  # transcript is best-effort; metadata still returns
        vtts = sorted(Path(tmp).glob("*.vtt"))
        if vtts:
            try:
                transcript = _clean_vtt(vtts[0].read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                transcript = ""
            if transcript:
                result["transcript"] = transcript
                result["transcript_available"] = True

    return result


def _which(cmd: str):
    from shutil import which
    return which(cmd)


def main() -> int:
    args = [a for a in sys.argv[1:]]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if args else 1

    url = args[0]
    out_file = None
    if "--out" in args:
        i = args.index("--out")
        out_file = args[i + 1] if i + 1 < len(args) else None

    result = extract_youtube(url)

    if out_file and result.get("success") and result.get("transcript"):
        Path(out_file).write_text(result["transcript"], encoding="utf-8")
        result["transcript_written_to"] = out_file

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
