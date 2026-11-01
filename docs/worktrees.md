# Development and worktrees

Requires Git, Python 3 and Node 22. This repository contains skills and Python scripts, not an application. Convex references describe other projects; there is no Convex app/example backend. No dependencies, package manager, environment credentials, ports or services are required.

From the checkout root, run `python3 scripts/worktree/setup.py`. Setup requires a clean checkout, fetches origin and discovers its live default branch. It fast-forwards only and preserves local commits. Dirty files, fetch failures and divergence stop with an error. A stale local base is updated only when not checked out in a sibling. Run setup separately in that sibling when clean. No resets, stashes, branch switches or topic-to-base merges occur.

To create a linked checkout from the freshly fetched base:

```sh
python3 scripts/worktree/setup.py ../agent-skills-task chore/OSS-123-task
```

Setup uses a shared Git-common-directory flock. Generated owner metadata stays in ignored `.worktree-state/` inside its checkout. Run `python3 scripts/worktree/start.py`, `stop.py`, or `teardown.py` (each under scripts/worktree/) for repeatable no-op lifecycle operations: there are no managed processes. Stop and teardown preserve state. `python3 scripts/worktree/cleanup.py` explicitly removes only checkout-owned state, rejecting ownership mismatch and symlink roots. No user files, Git checkouts, sibling resources or databases are removed. Environment configuration is never copied. Use Git worktree removal separately after preserving all work. CI uses a fresh checkout and runs tests directly without interactive hooks.

Run these focused checks sequentially:

```sh
python3 scripts/validate_skills.py
python3 -m unittest discover -s tests -v
NODE_OPTIONS=--max-old-space-size=512 node --test --test-concurrency=1 scripts/pr-standard.test.mjs scripts/enforce-pr-standard.test.mjs
python3 -m unittest discover -s scripts/worktree -p 'test_*.py' -v
```

All CI compute uses UbiCloud Linux. Inspect current-head Actions job labels, runner identity and conclusion; queued jobs do not prove runner integration. Never substitute GitHub-hosted compute. Metadata activates after trusted files reach base. Verify required-status protection and plan support separately; this PR does not assert those are enabled.

All local Node test suites must hold `/home/cloudagent/.cache/fantastic-heavy.lock` for the entire subprocess tree: `flock -w 3600 /home/cloudagent/.cache/fantastic-heavy.lock env NODE_OPTIONS=--max-old-space-size=512 node --test --test-concurrency=1 <specific test files>`. Do not nest this lock.
