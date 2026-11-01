"""Backend-free repository layout; no ports, daemons or environment secrets."""
from pathlib import Path
import subprocess


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True, stderr=subprocess.STDOUT).strip()


def root_path():
    return Path(git(Path.cwd(), 'rev-parse', '--show-toplevel')).resolve()
