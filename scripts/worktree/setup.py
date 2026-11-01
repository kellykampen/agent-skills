"""setup entry point; see docs/worktrees.md."""
import sys
from config import root_path
from lifecycle import run

if __name__ == '__main__':
    try:
        run(root_path(), 'setup', *sys.argv[1:])
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
