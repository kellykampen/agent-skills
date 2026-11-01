"""No service ownership registry is needed: this repository starts no processes."""
from pathlib import Path
import json
import shutil
from config import git
from freshness import refresh
from locking import repository_lock


def run(root, command, destination=None, branch=None):
    state = root / '.worktree-state'
    if command == 'setup':
        with repository_lock(root):
            base = refresh(root)
            if destination:
                if not branch:
                    raise RuntimeError('New checkout requires an explicit branch name.')
                git(root, 'worktree', 'add', '-b', branch, str(Path(destination).resolve()), base)
                return
            state.mkdir(exist_ok=True)
            (state / 'owner.json').write_text(json.dumps({'checkout': str(root)}))
    elif command in ('start', 'stop', 'teardown'):
        print(f'{command}: backend-free repository; no ports or services to manage. State preserved.')
    elif command == 'cleanup':
        if state.is_symlink():
            raise RuntimeError('Refusing symlink state directory')
        if state.exists():
            owner = json.loads((state / 'owner.json').read_text())
            if owner != {'checkout': str(root)}:
                raise RuntimeError('State ownership mismatch; refusing cleanup')
            shutil.rmtree(state)
    else:
        raise RuntimeError(f'Unknown lifecycle command: {command}')
