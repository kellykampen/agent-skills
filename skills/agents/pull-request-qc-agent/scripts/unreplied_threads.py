#!/usr/bin/env python3
"""
unreplied_threads.py — list the review comments on a PR that nobody has replied
to yet, so the bot fixes/answers each one exactly once.

Why this exists: a PR's review comments accumulate replies over time. Re-fetching
"all comments" and re-handling them re-replies to threads already answered (noise,
and it looks like the bot is spinning). The signal that actually matters is "which
top-level review threads still have no reply" — that's what this prints.

Uses `gh`, which substitutes {owner}/{repo} from the current repo's remote, so run
it from inside the repo. Reads review comments (the inline, file-anchored kind);
issue-level PR comments are a separate endpoint and usually don't need per-thread
replies.

Usage:
  unreplied_threads.py <PR_NUMBER>            # human-readable list
  unreplied_threads.py <PR_NUMBER> --json     # JSON array for programmatic use

Output fields per thread: id, path, line, author, created_at, body (trimmed).
Reply to one with:
  gh api repos/{owner}/{repo}/pulls/<PR>/comments/<id>/replies -f body="..."
"""
import json
import subprocess
import sys


def gh_json(args):
    out = subprocess.run(
        ["gh", "api", "--paginate", *args],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.exit(f"gh failed: {out.stderr.strip()}")
    # --paginate may concatenate multiple JSON arrays; normalize to one list.
    txt = out.stdout.strip()
    if not txt:
        return []
    chunks, depth, buf, items = [], 0, "", []
    # Simple split on top-level array boundaries: gh prints `[...][...]`.
    for part in txt.replace("][", "]\x00[").split("\x00"):
        items.extend(json.loads(part))
    return items


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    pr = sys.argv[1]
    as_json = "--json" in sys.argv[2:]

    comments = gh_json([f"repos/{{owner}}/{{repo}}/pulls/{pr}/comments"])
    replied_to = {c.get("in_reply_to_id") for c in comments if c.get("in_reply_to_id")}
    top_level = [c for c in comments if not c.get("in_reply_to_id")]
    unreplied = [c for c in top_level if c["id"] not in replied_to]

    rows = [
        {
            "id": c["id"],
            "path": c.get("path"),
            "line": c.get("line") or c.get("original_line"),
            "author": c.get("user", {}).get("login"),
            "created_at": c.get("created_at"),
            "body": c.get("body", "").split("<details>")[0].strip()[:800],
        }
        for c in sorted(unreplied, key=lambda x: x["created_at"])
    ]

    if as_json:
        print(json.dumps(rows, indent=2))
        return

    print(f"{len(rows)} unreplied review thread(s) on PR #{pr} "
          f"({len(comments)} comments, {len(top_level)} top-level):")
    for i, r in enumerate(rows, 1):
        print(f"\n[{i}] id={r['id']}  {r['path']}:{r['line']}  by {r['author']}  {r['created_at']}")
        print(r["body"])


if __name__ == "__main__":
    main()
