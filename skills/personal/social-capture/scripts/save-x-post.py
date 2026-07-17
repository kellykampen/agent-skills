#!/usr/bin/env python3
"""
Save X/Twitter post content to Obsidian.
Usage: python scripts/save-x-post.py <username> <content_file>

The content_file should contain the markdown content to save.
This script handles the correct Obsidian path so it always goes to iCloud.
"""

import sys
import os
from pathlib import Path
from datetime import date

# CRITICAL: Always use iCloud Obsidian vault
OBSIDIAN_SOCIAL = Path(os.getenv(
    "OBSIDIAN_SOCIAL_PATH",
    os.path.expanduser("~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Ideaverse/Social")
))


def save_x_post(username: str, content: str, title: str) -> dict:
    """
    Save X post content to Obsidian.

    Args:
        username: X/Twitter username (without @)
        content: Markdown content to save
        title: Short title for the filename (first ~50 chars of post)

    Returns:
        dict with: success, file_path, error
    """
    try:
        # Create folder structure: X/<username>/
        user_folder = OBSIDIAN_SOCIAL / "X" / username
        user_folder.mkdir(parents=True, exist_ok=True)

        # Clean title for filename (no spaces - use hyphens)
        clean_title = "".join(c for c in title if c.isalnum() or c in " -_")[:50].strip()
        clean_title = clean_title.replace(" ", "-")

        # Create filename with date
        today = date.today().isoformat()
        filename = f"{today}-{clean_title}.md"
        file_path = user_folder / filename

        # Write content
        file_path.write_text(content)

        return {
            "success": True,
            "file_path": str(file_path),
            "relative_path": f"Social/X/{username}/{filename}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main() -> int:
    if len(sys.argv) < 3:
        print("Usage: python save-x-post.py <username> <content_file>")
        print("  or pipe content: echo 'content' | python save-x-post.py <username> <title>")
        return 1

    username = sys.argv[1]

    # Check if content is piped in
    if not sys.stdin.isatty():
        content = sys.stdin.read()
        title = sys.argv[2] if len(sys.argv) > 2 else "Untitled"
    else:
        # Read from file
        content_file = sys.argv[2]
        title = sys.argv[3] if len(sys.argv) > 3 else Path(content_file).stem
        content = Path(content_file).read_text()

    result = save_x_post(username, content, title)

    if result["success"]:
        print(f"Saved: {result['relative_path']}")
        return 0
    else:
        print(f"Failed: {result['error']}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
