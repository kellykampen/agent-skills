import concurrent.futures
from pathlib import Path
import subprocess
import tempfile
import unittest
from config import git
from lifecycle import run


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.remote = self.base / 'remote.git'
        self.root = self.base / 'checkout'
        subprocess.run(['git', 'init', '--bare', '--initial-branch=main', str(self.remote)], check=True, capture_output=True)
        subprocess.run(['git', 'clone', str(self.remote), str(self.root)], check=True, capture_output=True)
        git(self.root, 'config', 'user.email', 'test@example.com')
        git(self.root, 'config', 'user.name', 'Test')
        (self.root / 'file').write_text('initial')
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-m', 'initial')
        git(self.root, 'push', '-u', 'origin', 'main')
        (self.root / '.git/info/exclude').write_text('.worktree-state/\n')

    def advance(self):
        publisher = self.base / 'publisher'
        subprocess.run(['git', 'clone', str(self.remote), str(publisher)], check=True, capture_output=True)
        git(publisher, 'config', 'user.email', 'test@example.com')
        git(publisher, 'config', 'user.name', 'Test')
        (publisher / 'new').write_text('remote')
        git(publisher, 'add', '.')
        git(publisher, 'commit', '-m', 'advance')
        git(publisher, 'push')

    def test_stale_base_existing_checkout(self):
        git(self.root, 'switch', '-c', 'topic')
        self.advance()
        run(self.root, 'setup')
        self.assertEqual(git(self.root, 'rev-parse', 'HEAD'), git(self.root, 'rev-parse', 'origin/main'))
        self.assertEqual(git(self.root, 'rev-parse', 'main'), git(self.root, 'rev-parse', 'origin/main'))
        self.assertEqual(git(self.root, 'branch', '--show-current'), 'topic')

    def test_local_commits_and_divergence(self):
        git(self.root, 'switch', '-c', 'topic')
        (self.root / 'local').write_text('keep')
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-m', 'local')
        head = git(self.root, 'rev-parse', 'HEAD')
        run(self.root, 'setup')
        self.assertEqual(head, git(self.root, 'rev-parse', 'HEAD'))
        self.advance()
        with self.assertRaises(RuntimeError):
            run(self.root, 'setup')
        self.assertEqual(head, git(self.root, 'rev-parse', 'HEAD'))

    def test_dirty_fetch_failure(self):
        (self.root / 'file').write_text('dirty')
        with self.assertRaisesRegex(RuntimeError, 'Dirty'):
            run(self.root, 'setup')
        self.assertEqual((self.root / 'file').read_text(), 'dirty')
        (self.root / 'file').write_text('initial')
        git(self.root, 'remote', 'set-url', 'origin', str(self.base / 'missing'))
        with self.assertRaisesRegex(RuntimeError, 'fetch'):
            run(self.root, 'setup')

    def test_concurrent_setup_sibling_safe_cleanup(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda _: run(self.root, 'setup'), range(2)))
        sibling = self.base / 'sibling'
        run(self.root, 'setup', sibling, 'sibling')
        run(sibling, 'setup')
        for command in ['start', 'stop', 'teardown', 'cleanup', 'cleanup']:
            run(self.root, command)
        self.assertTrue((sibling / '.worktree-state/owner.json').exists())
        state = self.root / '.worktree-state'
        state.symlink_to(sibling / '.worktree-state', target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, 'symlink'):
            run(self.root, 'cleanup')
