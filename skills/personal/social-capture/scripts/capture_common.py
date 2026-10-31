"""Shared local configuration and note writing for social-capture. Stdlib only."""
import argparse
from datetime import date
import json
import os
from pathlib import Path
import re
import sys
import unicodedata


def load_config():
    default = Path(os.getenv('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'social-capture/config.json'
    path = Path(os.getenv('SOCIAL_CAPTURE_CONFIG', str(default))).expanduser()
    if not path.exists():
        if 'SOCIAL_CAPTURE_CONFIG' in os.environ:
            raise ValueError(f'Configuration file does not exist: {path}')
        return {}
    config = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(config, dict):
        raise ValueError('Configuration must be a JSON object')
    return config


def destination(config, platform):
    key, env, suffix = ('bookmarks_path', 'OBSIDIAN_BOOKMARKS_PATH', 'x/bookmarks') if platform == 'x' else ('youtube_path', 'OBSIDIAN_YOUTUBE_PATH', 'youtube')
    explicit = os.getenv(env) or config.get(key)
    root = os.getenv('OBSIDIAN_VAULT_PATH') or config.get('vault_path')
    if explicit:
        return Path(explicit).expanduser()
    if root:
        return Path(root).expanduser() / suffix
    raise ValueError(f'Configure {key} or vault_path in the local config, or set {env}')


def safe_component(value, field):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', value):
        raise ValueError(f'{field} must contain only letters, digits, underscores, or hyphens')
    return value


def string_list(value, field):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f'{field} must be a list of strings')
    return value


def prepare_record(rec, config, platform):
    if not isinstance(rec, dict):
        raise ValueError('Input must be a JSON object')
    rec = dict(rec)
    id_key = 'tweet_id' if platform == 'x' else 'video_id'
    rec[id_key] = safe_component(rec.get(id_key), id_key)
    rec['date'] = rec.get('date') or date.today().isoformat()
    date.fromisoformat(rec['date'])
    # Require the canonical form so dates cannot create surprising filenames.
    if date.fromisoformat(rec['date']).isoformat() != rec['date']:
        raise ValueError('date must be YYYY-MM-DD')
    rec['category'] = safe_component(rec.get('category') or 'misc', 'category')
    categories = config.get('categories')
    if categories is not None:
        for item in string_list(categories, 'categories'):
            safe_component(item, 'category')
        if rec['category'] not in categories:
            rec['category'] = 'misc'
    for key in ['tags', 'key_points', 'how_to_apply']:
        rec[key] = string_list(rec.get(key, [rec['category']] if key == 'tags' else []), key)
    for key in ['title', 'summary', 'author', 'author_handle', 'author_id', 'channel', 'channel_handle', 'published', 'duration', 'playlist', 'full_text', 'text', 'url']:
        if key in rec and not isinstance(rec[key], str):
            raise ValueError(f'{key} must be a string')
    rec['title'] = rec.get('title') or (rec.get('full_text') or rec.get('text') or '')[:80].strip() or 'Untitled'
    if platform == 'x':
        if not rec.get('url'):
            raise ValueError('url is required for an X post')
    else:
        rec['url'] = rec.get('url') or f'https://www.youtube.com/watch?v={rec[id_key]}'
    return rec


def note_path(rec, platform):
    title = unicodedata.normalize('NFKD', rec['title']).encode('ascii', 'ignore').decode()
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:60].rstrip('-') or 'untitled'
    source_id = rec['tweet_id' if platform == 'x' else 'video_id']
    return Path(rec['category']) / f"{rec['date']}-{slug}-{source_id}.md"


def frontmatter(fields):
    # JSON quoted strings and arrays are also valid YAML. Escape newlines/quotes
    # without requiring PyYAML at runtime or accidentally creating YAML keys.
    return '---\n' + '\n'.join(f'{key}: {json.dumps(value, ensure_ascii=True)}' for key, value in fields.items()) + '\n---\n\n'


def application_section(rec, config):
    heading = config.get('application_heading', 'How to apply')
    if not isinstance(heading, str) or not heading.strip() or '\n' in heading or '\r' in heading:
        raise ValueError('application_heading must be a non-empty single line')
    return ['## ' + heading, *('- ' + item for item in rec['how_to_apply']), ''] if rec['how_to_apply'] else []


def save_cli(platform, render):
    parser = argparse.ArgumentParser(description=f'Save a structured {platform} capture as an Obsidian note')
    parser.add_argument('--json', action='store_true', required=True, help='read a JSON record')
    parser.add_argument('--in', dest='infile', help='input JSON file; defaults to stdin')
    parser.add_argument('--dry-run', action='store_true', help='write only to --out-dir')
    parser.add_argument('--out-dir', default='rendered-notes', help='dry-run output directory; defaults to ./rendered-notes')
    args = parser.parse_args()
    try:
        config = load_config()
        raw = Path(args.infile).read_text(encoding='utf-8') if args.infile else sys.stdin.read()
        rec = prepare_record(json.loads(raw), config, platform)
        relative = note_path(rec, platform)
        markdown = render(rec, config)
        base = Path(args.out_dir).expanduser() if args.dry_run else destination(config, platform)
        output = base / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation protects existing notes even when two jobs run at once.
        with output.open('x', encoding='utf-8') as file:
            file.write(markdown)
        print(f'Saved: {output}')
        if args.dry_run:
            print('Dry run: vault unchanged')
        return 0
    except (OSError, ValueError, TypeError) as error:
        print(f'Failed: {error}', file=sys.stderr)
        return 1
