#!/usr/bin/env python3
"""
Watch a YouTube video: download, extract frames, return transcript + frame paths.
Usage: python scripts/watch_youtube.py <youtube_url>

Uses the sibling extractor, temporary video downloads, and optional browser cookies.
Returns JSON; the caller owns cleanup of the returned frames directory.
"""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
EXTRACT_FRAMES_SH = SCRIPTS_DIR / "extract_frames.sh"
YT_DLP = os.getenv("YT_DLP_BIN", "yt-dlp")


def _load_extract_youtube():
    """Load extract_youtube() from the sibling hyphenated module file."""
    spec = importlib.util.spec_from_file_location(
        "extract_youtube_mod", str(SCRIPTS_DIR / "extract-youtube.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.extract_youtube


def _cookie_args() -> list:
    browser = os.getenv("YT_DLP_COOKIES_BROWSER", "").strip()
    return ["--cookies-from-browser", browser] if browser else []


def watch_youtube(url: str, max_frames: int = 30) -> dict:
    """
    Download a YouTube video, extract frames, and return transcript result + frame paths.

    Returns dict with all extract_youtube keys plus:
      - frames: list of absolute paths to extracted PNG frames
      - frames_dir: temp dir holding the frames (caller must clean up after reading)
    """
    extract_youtube = _load_extract_youtube()

    # Step 1: get transcript + metadata (subtitles only, fast).
    transcript_result = extract_youtube(url)
    if not transcript_result["success"]:
        return transcript_result

    videos_dir = Path(tempfile.mkdtemp(prefix="watch-video-dl-"))
    try:
        # Step 2: download video file.
        dl_cmd = [
            YT_DLP,
            *_cookie_args(),
            "--format", "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "--output", str(videos_dir / "%(title)s.%(ext)s"),
            "--no-playlist",
            "--print", "after_move:filepath",
            url,
        ]
        dl_result = subprocess.run(dl_cmd, capture_output=True, text=True, timeout=300)
        if dl_result.returncode != 0:
            return {**transcript_result, "frames": [], "frames_dir": None,
                    "watch_error": f"Video download failed: {dl_result.stderr[:200]}"}

        video_path = dl_result.stdout.strip().splitlines()[-1] if dl_result.stdout.strip() else ""
        if not video_path or not Path(video_path).exists():
            return {**transcript_result, "frames": [], "frames_dir": None,
                    "watch_error": f"Downloaded file not found: {video_path}"}

        # Step 3: extract frames.
        frames_result = subprocess.run(
            [str(EXTRACT_FRAMES_SH), video_path, "--max-frames", str(max_frames)],
            capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {**transcript_result, "frames": [], "frames_dir": None,
                "watch_error": str(error)}
    finally:
        shutil.rmtree(videos_dir, ignore_errors=True)

    if frames_result.returncode != 0:
        return {**transcript_result, "frames": [], "frames_dir": None,
                "watch_error": f"Frame extraction failed: {frames_result.stderr[:200]}"}

    try:
        frames_data = json.loads(frames_result.stdout)
    except json.JSONDecodeError:
        return {**transcript_result, "frames": [], "frames_dir": None,
                "watch_error": "Could not parse frame extraction output"}

    return {
        **transcript_result,
        "frames": frames_data.get("frames", []),
        "frames_dir": frames_data.get("output_dir"),
        "frame_count": frames_data.get("frame_count", 0),
        "video_duration_seconds": frames_data.get("video_duration_seconds"),
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--max-frames", type=int, default=30)
    args = parser.parse_args()
    if args.max_frames < 1:
        parser.error("--max-frames must be positive")
    result = watch_youtube(args.url, args.max_frames)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["success"] and not result.get("watch_error") else 1


if __name__ == "__main__":
    sys.exit(main())
