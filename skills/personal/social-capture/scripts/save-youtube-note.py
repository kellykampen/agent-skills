#!/usr/bin/env python3
"""Render a YouTube note from JSON. Run with --help for input and dry-run options."""
from capture_common import application_section, frontmatter, save_cli


def render(rec, config):
    fields = {key: rec.get(key, '') for key in ['title', 'channel', 'channel_handle', 'video_id', 'date', 'published', 'url', 'playlist', 'category', 'tags', 'duration']}
    body = ['# ' + rec['title'], '', '## Summary', rec.get('summary') or '_(summary pending)_', '',
            '## Key points / notes', *('- ' + item for item in rec['key_points']), '',
            *application_section(rec, config), '## Watch', rec['url'], '']
    return frontmatter(fields) + '\n'.join(body)


if __name__ == '__main__':
    raise SystemExit(save_cli('youtube', render))
