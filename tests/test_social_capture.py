"""Offline contract tests for social-capture CLIs. No browser, account, or vault access."""
import json
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/personal/social-capture/scripts'


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = self.root / 'config.json'
        self.config.write_text(json.dumps({'vault_path': str(self.root / 'vault')}))
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(('OBSIDIAN_', 'SOCIAL_CAPTURE_', 'YT_DLP_', 'YT_SUB_'))}
        self.env['SOCIAL_CAPTURE_CONFIG'] = str(self.config)
        self.env['HOME'] = str(self.root)
        self.env['OBSIDIAN_SOCIAL_PATH'] = str(self.root / 'legacy-vault')

    def run_script(self, script, *args, record=None):
        return subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                              input=json.dumps(record) if record is not None else None,
                              text=True, capture_output=True, env=self.env)

    def record(self, platform, **overrides):
        rec = {'title': 'A "quoted" title\\path\n第二行', 'date': '2026-10-31',
               'category': 'ai-agents', 'tags': ['a"b', 'two\nlines'],
               'summary': 'A summary', 'key_points': ['A takeaway'],
               'how_to_apply': ['Try locally']}
        if platform == 'x':
            rec.update(tweet_id='1234567890', url='https://x.com/example/status/1234567890', author='A "Name"')
        else:
            rec.update(video_id='abcdefghijk', channel='A "Channel"')
        rec.update(overrides)
        return rec

    def save(self, platform, rec, *args):
        script = 'save-x-post.py' if platform == 'x' else 'save-youtube-note.py'
        result = self.run_script(script, '--json', *args, record=rec)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_json_notes_escape_frontmatter_and_use_source_ids(self):
        for platform, id_key in [('x', 'tweet_id'), ('youtube', 'video_id')]:
            with self.subTest(platform=platform):
                rec = self.record(platform)
                self.save(platform, rec)
                folder = self.root / 'vault' / ('x/bookmarks' if platform == 'x' else 'youtube')
                files = list(folder.rglob('*.md'))
                self.assertEqual(len(files), 1)
                self.assertIn(rec[id_key], files[0].name)
                frontmatter = files[0].read_text().split('---', 2)[1]
                fields = {k: json.loads(v.strip()) for k, v in (line.split(':', 1) for line in frontmatter.strip().splitlines())}
                self.assertEqual(fields['tags'], rec['tags'])
                field = 'author' if platform == 'x' else 'title'
                self.assertEqual(fields[field], rec[field])

    def test_distinct_source_ids_do_not_collide(self):
        for platform, key in [('x', 'tweet_id'), ('youtube', 'video_id')]:
            for source_id in ['12345678901', '12345678902']:
                self.save(platform, self.record(platform, **{key: source_id}))
        self.assertEqual(len(list((self.root / 'vault').rglob('*.md'))), 4)

    def test_repeat_does_not_overwrite_existing_note(self):
        for platform in ['x', 'youtube']:
            rec = self.record(platform)
            self.save(platform, rec)
            script = 'save-x-post.py' if platform == 'x' else 'save-youtube-note.py'
            result = self.run_script(script, '--json', record={**rec, 'summary': 'Replacement'})
            self.assertNotEqual(result.returncode, 0)
        self.assertTrue(all('Replacement' not in p.read_text() for p in (self.root / 'vault').rglob('*.md')))

    def test_dry_run_uses_output_directory_without_vault_configuration(self):
        self.config.write_text('{}')
        for platform in ['x', 'youtube']:
            self.save(platform, self.record(platform), '--dry-run', '--out-dir', str(self.root / platform))
        self.assertFalse((self.root / 'vault').exists())
        self.assertEqual(len(list((self.root / 'x').rglob('*.md'))), 1)
        self.assertEqual(len(list((self.root / 'youtube').rglob('*.md'))), 1)

    def test_local_destinations_categories_and_heading(self):
        self.config.write_text(json.dumps({'bookmarks_path': str(self.root / 'bookmarks'),
                                          'youtube_path': str(self.root / 'videos'),
                                          'categories': ['research'], 'application_heading': 'Try this'}))
        for platform, folder in [('x', 'bookmarks'), ('youtube', 'videos')]:
            self.save(platform, self.record(platform, category='research'))
            note, = (self.root / folder / 'research').glob('*.md')
            self.assertIn('## Try this', note.read_text())
        self.assertFalse((self.root / 'vault').exists())

    def test_environment_destination_overrides_config(self):
        self.env['OBSIDIAN_BOOKMARKS_PATH'] = str(self.root / 'override')
        self.save('x', self.record('x'))
        self.assertEqual(len(list((self.root / 'override').rglob('*.md'))), 1)
        self.assertFalse((self.root / 'vault').exists())

    def test_invalid_record_cannot_escape_destination(self):
        for platform, key in [('x', 'tweet_id'), ('youtube', 'video_id')]:
            script = 'save-x-post.py' if platform == 'x' else 'save-youtube-note.py'
            for override in [{key: '../escape'}, {'date': '../../escape'}, {'category': '../escape'}, {'tags': 'not-a-list'}]:
                result = self.run_script(script, '--json', record=self.record(platform, **override))
                self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse((self.root / 'vault').exists())

    def test_missing_configuration_fails_before_writing(self):
        self.config.write_text('{}')
        for platform in ['x', 'youtube']:
            script = 'save-x-post.py' if platform == 'x' else 'save-youtube-note.py'
            result = self.run_script(script, '--json', record=self.record(platform))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('config', (result.stdout + result.stderr).lower())

    def test_extractor_is_self_contained_and_uses_path_tool(self):
        tool = self.root / 'yt-dlp'
        tool.write_text('#!' + sys.executable + '\n' + '''import json,sys
from pathlib import Path
if '--dump-json' in sys.argv:
 print(json.dumps({'id':'abcdefghijk','title':'Example','channel':'Example channel','upload_date':'20261031','duration':65}))
else:
 output=Path(sys.argv[sys.argv.index('--output')+1]).parent
 (output/'abcdefghijk.en.vtt').write_text('WEBVTT\\n\\n00:00:00.000 --> 00:00:02.000\\nHello <c>world</c>\\nHello <c>world</c>\\n')
''')
        tool.chmod(0o755)
        self.env['PATH'] = str(self.root) + os.pathsep + self.env.get('PATH', '')
        result = self.run_script('extract-youtube.py', 'https://www.youtube.com/watch?v=abcdefghijk')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        record = json.loads(result.stdout)
        self.assertTrue(record['transcript_available'])
        self.assertEqual(record['transcript'], 'Hello world')
        self.assertEqual(record['duration'], '1:05')

    def test_watch_timeout_returns_error_and_cleans_download_directory(self):
        spec = importlib.util.spec_from_file_location('watch_test', SCRIPTS / 'watch_youtube.py')
        watch = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(watch)
        download = self.root / 'download'
        download.mkdir()
        with patch.object(watch, '_load_extract_youtube', return_value=lambda url: {'success': True, 'transcript': 'Kept'}), \
             patch.object(watch.tempfile, 'mkdtemp', return_value=str(download)), \
             patch.object(watch.subprocess, 'run', side_effect=subprocess.TimeoutExpired('yt-dlp', 300)):
            result = watch.watch_youtube('https://www.youtube.com/watch?v=abcdefghijk')
        self.assertIn('watch_error', result)
        self.assertEqual(result['transcript'], 'Kept')
        self.assertFalse(download.exists())

    def test_explicit_missing_config_is_reported(self):
        self.config.unlink()
        result = self.run_script('save-x-post.py', '--json', record=self.record('x'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Configuration file does not exist', result.stderr)


    def test_frame_extractor_uses_supported_ffmpeg_timing_option(self):
        ffprobe = self.root / 'ffprobe'
        ffprobe.write_text('#!' + sys.executable + '\nimport sys\nprint("2.0" if "format=duration" in sys.argv else "160")\n')
        ffmpeg = self.root / 'ffmpeg'
        ffmpeg.write_text('#!' + sys.executable + '\n' + "import sys\nfrom pathlib import Path\nif '-vsync' in sys.argv: raise SystemExit(2)\nPath(sys.argv[-1].replace('%03d','001')).write_bytes(b'frame')\n")
        for tool in [ffprobe, ffmpeg]:
            tool.chmod(0o755)
        self.env['PATH'] = str(self.root) + os.pathsep + self.env.get('PATH', '')
        self.env['TMPDIR'] = str(self.root)
        video = self.root / 'video.mp4'
        video.write_bytes(b'synthetic input')
        result = subprocess.run(['bash', str(SCRIPTS / 'extract_frames.sh'), str(video),
                                 '--max-frames', '2', '--output-dir', str(self.root / 'frames')],
                                capture_output=True, text=True, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['frame_count'], 1)



if __name__ == '__main__':
    unittest.main()
