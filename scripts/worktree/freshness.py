"""Fetch before setup; fast-forward only, never discard local work."""
from config import git


def refresh(root):
    if git(root, 'status', '--porcelain'):
        raise RuntimeError('Dirty checkout: commit your changes before setup; nothing was discarded.')
    try:
        git(root, 'fetch', 'origin')
        git(root, 'remote', 'set-head', 'origin', '--auto')
    except Exception as error:
        raise RuntimeError('Origin fetch/default discovery failed; refusing stale setup.') from error
    base = git(root, 'symbolic-ref', 'refs/remotes/origin/HEAD')
    # Update a stale selected base only when safe. Never mutate a checked-out sibling.
    name = base.rsplit('/', 1)[-1]
    local = f'refs/heads/{name}'
    try:
        old = git(root, 'rev-parse', '--verify', local)
    except Exception:
        old = None
    if old and old != git(root, 'rev-parse', base):
        git(root, 'merge-base', '--is-ancestor', old, base)
        checked = git(root, 'worktree', 'list', '--porcelain')
        current = git(root, 'symbolic-ref', 'HEAD')
        if current != local and f'branch {local}' not in checked:
            git(root, 'update-ref', local, git(root, 'rev-parse', base), old)
    try:
        git(root, 'merge', '--ff-only', base)
    except Exception as error:
        raise RuntimeError('Cannot fast-forward checkout/base. Preserve local commits and resolve divergence explicitly; setup never merges topic work into the base.') from error
    return base
