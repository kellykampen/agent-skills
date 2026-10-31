#!/usr/bin/env python3
"""Render an X post from JSON. Run with --help for input and dry-run options."""
from capture_common import application_section, frontmatter, save_cli


def render(rec, config):
    handle = rec.get('author_handle', '')
    fields = {key: rec.get(key, '') for key in ['title', 'author', 'author_handle', 'tweet_id', 'url', 'date', 'category', 'tags']}
    if not fields['author']:
        fields['author'] = handle.lstrip('@')
    if not fields['author'] and rec.get('author_id'):
        fields['author_id'] = rec['author_id']
    body = ['# ' + rec['title'], '']
    if rec.get('summary'):
        body += ['## Summary', rec['summary'], '']
    if rec['key_points']:
        body += ['## Key Points', *('- ' + item for item in rec['key_points']), '']
    text = rec.get('full_text') or rec.get('text') or ''
    body += ['## Full Text', *('> ' + line for line in text.splitlines())]
    if rec.get('truncated'):
        body += ['>', '> _(text truncated by source)_']
    body += ['', *application_section(rec, config), '## Original Tweet', rec['url'], '']
    return frontmatter(fields) + '\n'.join(body)


if __name__ == '__main__':
    raise SystemExit(save_cli('x', render))
