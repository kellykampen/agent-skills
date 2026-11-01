"""Serialize setup across linked checkouts, without an external dependency."""
from contextlib import contextmanager
from pathlib import Path
import fcntl
from config import git


@contextmanager
def repository_lock(root):
    common = Path(git(root, 'rev-parse', '--git-common-dir'))
    if not common.is_absolute():
        common = root / common
    with (common / 'agent-skills-setup.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield
