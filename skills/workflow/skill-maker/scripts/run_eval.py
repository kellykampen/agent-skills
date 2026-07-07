#!/usr/bin/env python3
"""Run trigger evaluation for a skill description.

Tests whether a skill's description causes Claude to trigger (read the skill)
for a set of queries. Outputs results as JSON.
"""

import argparse
import json
import os
import select
import signal
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from scripts.utils import parse_skill_md, replace_description


def find_project_root() -> Path:
    """Find the project root by walking up from cwd looking for .claude/.

    Mimics how Claude Code discovers its project root, so `claude -p` sees
    the same project-level context a real session would.
    """
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir():
            return parent
    return current


class SkillDescriptionSwap:
    """Temporarily swaps a real, installed skill's description to a candidate
    under test, guaranteeing the original is restored no matter how the
    process exits.

    GOTCHA — why this exists: an earlier version of this script avoided
    touching the real skill at all, instead creating a throwaway proxy file
    under .claude/commands/ with a unique per-run name and checking whether
    the model's tool call referenced that unique name. That's unreliable
    whenever the skill already exists for real (which `main()` requires —
    skill_path must already have a SKILL.md): the model correctly prefers
    invoking the REAL, already-installed skill by its real name over an
    unrelated ephemeral command file, so the substring-match against the
    proxy's synthetic name silently undercounted every true trigger — every
    should-trigger query would read as a miss, regardless of how the
    description was worded, because the check was looking for the wrong
    thing. Swapping the real file's description (and always restoring it)
    tests the actual triggering mechanism directly instead of a proxy for it
    that the model doesn't reliably use.

    Because a crash mid-run could leave the user's real skill permanently
    stuck with a test description, this writes an on-disk `.bak` as a last
    resort in addition to the in-memory original and installs signal/atexit
    handlers — belt and suspenders, since SIGKILL can't be caught by any of
    these and the on-disk backup is the only recourse for that case.
    """

    def __init__(self, skill_path: Path):
        self.skill_md_path = skill_path / "SKILL.md"
        self.backup_path = skill_path / "SKILL.md.bak"
        self.original_content = self.skill_md_path.read_text()
        self._restored = False
        self._prev_handlers: dict[int, object] = {}

    def __enter__(self):
        self.backup_path.write_text(self.original_content)
        for sig in (signal.SIGINT, signal.SIGTERM):
            self._prev_handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, self._on_signal)
        return self

    def swap_to(self, candidate_description: str):
        self.skill_md_path.write_text(replace_description(self.original_content, candidate_description))

    def _on_signal(self, signum, frame):
        self.restore()
        sys.exit(1)

    def restore(self):
        if not self._restored:
            self.skill_md_path.write_text(self.original_content)
            if self.backup_path.exists():
                self.backup_path.unlink()
            self._restored = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        for sig, handler in self._prev_handlers.items():
            signal.signal(sig, handler)
        self.restore()
        return False


def run_single_query(
    query: str,
    skill_name: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> bool:
    """Run a single query against the REAL, currently-installed skill (whose
    description has already been swapped to the candidate under test by the
    caller) and return whether it triggered.

    Uses --include-partial-messages to detect triggering early from stream
    events (content_block_start) rather than waiting for the full assistant
    message, which only arrives after tool execution.
    """
    cmd = [
        "claude",
        "-p", query,
        "--output-format", "stream-json",
        "--verbose",
        "--include-partial-messages",
    ]
    if model:
        cmd.extend(["--model", model])

    # Remove CLAUDECODE env var to allow nesting claude -p inside a
    # Claude Code session. The guard is for interactive terminal conflicts;
    # programmatic subprocess usage is safe.
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        cwd=project_root,
        env=env,
    )

    triggered = False
    start_time = time.time()
    buffer = ""
    pending_tool_name = None
    accumulated_json = ""

    def matches(tool_name: str, json_fragment: str) -> bool:
        if tool_name == "Skill":
            return f'"skill":"{skill_name}"' in json_fragment or f'"skill": "{skill_name}"' in json_fragment
        if tool_name == "Read":
            return f"/{skill_name}/SKILL.md" in json_fragment
        return False

    try:
        while time.time() - start_time < timeout:
            if process.poll() is not None:
                remaining = process.stdout.read()
                if remaining:
                    buffer += remaining.decode("utf-8", errors="replace")
                break

            ready, _, _ = select.select([process.stdout], [], [], 1.0)
            if not ready:
                continue

            chunk = os.read(process.stdout.fileno(), 8192)
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="replace")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if event.get("type") == "stream_event":
                    se = event.get("event", {})
                    se_type = se.get("type", "")

                    if se_type == "content_block_start":
                        cb = se.get("content_block", {})
                        if cb.get("type") == "tool_use":
                            tool_name = cb.get("name", "")
                            if tool_name in ("Skill", "Read"):
                                pending_tool_name = tool_name
                                accumulated_json = ""
                            else:
                                return False

                    elif se_type == "content_block_delta" and pending_tool_name:
                        delta = se.get("delta", {})
                        if delta.get("type") == "input_json_delta":
                            accumulated_json += delta.get("partial_json", "")
                            if matches(pending_tool_name, accumulated_json):
                                return True

                    elif se_type in ("content_block_stop", "message_stop"):
                        if pending_tool_name:
                            return matches(pending_tool_name, accumulated_json)
                        if se_type == "message_stop":
                            return False

                elif event.get("type") == "assistant":
                    message = event.get("message", {})
                    for content_item in message.get("content", []):
                        if content_item.get("type") != "tool_use":
                            continue
                        tool_name = content_item.get("name", "")
                        tool_input = content_item.get("input", {})
                        if tool_name == "Skill" and tool_input.get("skill") == skill_name:
                            triggered = True
                        elif tool_name == "Read" and f"/{skill_name}/SKILL.md" in tool_input.get("file_path", ""):
                            triggered = True
                        return triggered

                elif event.get("type") == "result":
                    return triggered
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()

    return triggered


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    skill_path: Path,
    description: str,
    num_workers: int,
    timeout: int,
    project_root: Path,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: str | None = None,
) -> dict:
    """Run the full eval set against `description` and return results.

    Swaps skill_path's real SKILL.md to `description` for the duration of
    the whole batch (not per-query — every query in one call tests the same
    candidate, so swapping once avoids a restore-mid-batch race across the
    parallel workers) and guarantees restoration on the way out.
    """
    results = []

    with SkillDescriptionSwap(skill_path) as swap:
        swap.swap_to(description)

        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            future_to_info = {}
            for item in eval_set:
                for run_idx in range(runs_per_query):
                    future = executor.submit(
                        run_single_query,
                        item["query"],
                        skill_name,
                        timeout,
                        str(project_root),
                        model,
                    )
                    future_to_info[future] = (item, run_idx)

            query_triggers: dict[str, list[bool]] = {}
            query_items: dict[str, dict] = {}
            for future in as_completed(future_to_info):
                item, _ = future_to_info[future]
                query = item["query"]
                query_items[query] = item
                if query not in query_triggers:
                    query_triggers[query] = []
                try:
                    query_triggers[query].append(future.result())
                except Exception as e:
                    print(f"Warning: query failed: {e}", file=sys.stderr)
                    query_triggers[query].append(False)

    for query, triggers in query_triggers.items():
        item = query_items[query]
        trigger_rate = sum(triggers) / len(triggers)
        should_trigger = item["should_trigger"]
        if should_trigger:
            did_pass = trigger_rate >= trigger_threshold
        else:
            did_pass = trigger_rate < trigger_threshold
        results.append({
            "query": query,
            "should_trigger": should_trigger,
            "trigger_rate": trigger_rate,
            "triggers": sum(triggers),
            "runs": len(triggers),
            "pass": did_pass,
        })

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Run trigger evaluation for a skill description")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--description", default=None, help="Override description to test")
    parser.add_argument("--num-workers", type=int, default=10, help="Number of parallel workers")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout per query in seconds")
    parser.add_argument("--runs-per-query", type=int, default=3, help="Number of runs per query")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold")
    parser.add_argument("--model", default=None, help="Model to use for claude -p (default: user's configured model)")
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text())
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, original_description, content = parse_skill_md(skill_path)
    description = args.description or original_description
    project_root = find_project_root()

    if args.verbose:
        print(f"Evaluating: {description}", file=sys.stderr)

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        skill_path=skill_path,
        description=description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        project_root=project_root,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
    )

    if args.verbose:
        summary = output["summary"]
        print(f"Results: {summary['passed']}/{summary['total']} passed", file=sys.stderr)
        for r in output["results"]:
            status = "PASS" if r["pass"] else "FAIL"
            rate_str = f"{r['triggers']}/{r['runs']}"
            print(f"  [{status}] rate={rate_str} expected={r['should_trigger']}: {r['query'][:70]}", file=sys.stderr)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
