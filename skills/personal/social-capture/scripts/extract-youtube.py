#!/usr/bin/env python3
"""
Extract YouTube transcript and save to Obsidian.
Usage: python scripts/extract-youtube.py <youtube_url>
"""

import sys
import os

# Add parent directory to path to import youtube_extractor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from youtube_extractor import extract_youtube


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python extract-youtube.py <youtube_url>")
        return 1

    url = sys.argv[1]
    result = extract_youtube(url)

    if result["success"]:
        print(f"Saved: Social/YouTube/{result['channel']}/transcripts/{result['file_path'].split('/')[-1]}")
        return 0
    else:
        print(f"Failed: {result['error']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
