#!/usr/bin/env python3
"""
Watch a YouTube video: download, extract frames, return transcript + frame paths.
Usage: python scripts/watch_youtube.py <youtube_url>
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[4]))
from youtube_extractor import extract_youtube

SCRIPTS_DIR = Path(__file__).parent
EXTRACT_FRAMES_SH = SCRIPTS_DIR / "extract_frames.sh"
VIDEOS_DIR = Path(__file__).parents[4] / "social" / "temp" / "videos"


def watch_youtube(url: str, max_frames: int = 30) -> dict:
    """
    Download a YouTube video, extract frames, and return transcript result + frame paths.

    Returns dict with all extract_youtube keys plus:
      - frames: list of absolute paths to extracted JPG frames
      - frames_dir: temp dir holding the frames (caller must clean up after reading)
    """
    # Step 1: get transcript (subtitles only, fast)
    transcript_result = extract_youtube(url)
    if not transcript_result["success"]:
        return transcript_result

    # Delete the auto-generated stub summary — watch mode writes a richer one
    stub = transcript_result.get("summary_path")
    if stub:
        try:
            Path(stub).unlink(missing_ok=True)
        except OSError:
            pass

    # Step 2: download video file
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    dl_cmd = [
        "yt-dlp",
        "--cookies-from-browser", "brave",
        "--format", "bestvideo[height<=720]+bestaudio/best[height<=720]",
        "--output", str(VIDEOS_DIR / "%(title)s.%(ext)s"),
        "--no-playlist",
        "--print", "after_move:filepath",
        url,
    ]
    dl_result = subprocess.run(dl_cmd, capture_output=True, text=True, timeout=300)
    if dl_result.returncode != 0:
        return {**transcript_result, "frames": [], "frames_dir": None,
                "watch_error": f"Video download failed: {dl_result.stderr[:200]}"}

    video_path = dl_result.stdout.strip().splitlines()[-1]
    if not Path(video_path).exists():
        return {**transcript_result, "frames": [], "frames_dir": None,
                "watch_error": f"Downloaded file not found: {video_path}"}

    # Step 3: extract frames
    frames_result = subprocess.run(
        [str(EXTRACT_FRAMES_SH), video_path, "--max-frames", str(max_frames)],
        capture_output=True, text=True, timeout=120,
    )

    # Clean up video file — frames are all we need
    try:
        Path(video_path).unlink()
    except OSError:
        pass

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
    if len(sys.argv) < 2:
        print("Usage: python watch_youtube.py <youtube_url>")
        return 1

    result = watch_youtube(sys.argv[1])

    if not result["success"]:
        print(f"Failed: {result['error']}")
        return 1

    if result.get("watch_error"):
        print(f"Transcript saved but watch failed: {result['watch_error']}")
        return 1

    print(f"Transcript: Social/YouTube/{result['channel']}/transcripts/{Path(result['file_path']).name}")
    print(f"Frames: {result['frame_count']} extracted to {result['frames_dir']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
