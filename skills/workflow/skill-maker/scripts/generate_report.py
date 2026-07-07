#!/usr/bin/env python3
"""Generate an HTML report from run_loop.py output.

Takes the JSON output from run_loop.py and generates a visual HTML report
showing each description attempt with check/x for each test case.
Distinguishes between train and test queries.
"""

import argparse
import html
import json
import sys
from pathlib import Path


def generate_html(data: dict, auto_refresh: bool = False, skill_name: str = "") -> str:
    """Generate HTML report from loop output data. If auto_refresh is True, adds a meta refresh tag."""
    history = data.get("history", [])
    title_prefix = html.escape(skill_name + " — ") if skill_name else ""

    # Get all unique queries from train and test sets, with should_trigger info,
    # preserving encounter order but de-duplicated (a query can reappear if
    # generated eval sets ever overlap).
    train_queries: list[dict] = []
    test_queries: list[dict] = []
    if history:
        seen: set[str] = set()
        for r in history[0].get("train_results", history[0].get("results", [])):
            if r["query"] not in seen:
                train_queries.append({"query": r["query"], "should_trigger": r.get("should_trigger", True)})
                seen.add(r["query"])
        for r in history[0].get("test_results", []) or []:
            if r["query"] not in seen:
                test_queries.append({"query": r["query"], "should_trigger": r.get("should_trigger", True)})
                seen.add(r["query"])

    refresh_tag = '    <meta http-equiv="refresh" content="5">\n' if auto_refresh else ""

    # Find the best iteration for highlighting (by test score if test queries
    # exist, else by train score).
    best_iter = None
    if history:
        if test_queries:
            best_iter = max(history, key=lambda h: h.get("test_passed") or 0).get("iteration")
        else:
            best_iter = max(history, key=lambda h: h.get("train_passed", h.get("passed", 0))).get("iteration")

    def score_class(correct: int, total: int) -> str:
        if total > 0:
            ratio = correct / total
            if ratio >= 0.8:
                return "score-good"
            elif ratio >= 0.5:
                return "score-ok"
        return "score-bad"

    def aggregate_runs(results: list[dict]) -> tuple[int, int]:
        correct = 0
        total = 0
        for r in results:
            runs = r.get("runs", 0)
            triggers = r.get("triggers", 0)
            total += runs
            if r.get("should_trigger", True):
                correct += triggers
            else:
                correct += runs - triggers
        return correct, total

    # Pre-compute per-iteration data once.
    iterations = []
    for h in history:
        train_results = h.get("train_results", h.get("results", []))
        test_results = h.get("test_results", []) or []
        train_correct, train_runs = aggregate_runs(train_results)
        test_correct, test_runs = aggregate_runs(test_results)
        iterations.append({
            "iteration": h.get("iteration", "?"),
            "description": h.get("description", ""),
            "train_correct": train_correct,
            "train_runs": train_runs,
            "test_correct": test_correct,
            "test_runs": test_runs,
            "train_by_query": {r["query"]: r for r in train_results},
            "test_by_query": {r["query"]: r for r in test_results},
            "is_best": h.get("iteration") == best_iter,
        })

    html_parts = ["""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
""" + refresh_tag + """    <title>""" + title_prefix + """Skill Description Optimization</title>
    <style>
        :root {
            --bg: #faf9f5;
            --panel: #ffffff;
            --border: #e8e6dc;
            --ink: #141413;
            --muted: #83816f;
            --good: #5a7a3f;
            --good-bg: #eef2e8;
            --bad: #b83b3b;
            --bad-bg: #fceaea;
            --ok: #a16207;
            --ok-bg: #fef3c7;
            --test-accent: #3a6ea8;
            --test-bg: #eef3fa;
        }
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            max-width: 1100px;
            margin: 0 auto;
            padding: 28px 24px 60px;
            background: var(--bg);
            color: var(--ink);
            line-height: 1.5;
        }
        h1 { font-size: 1.4rem; margin: 0 0 18px; }
        h2 { font-size: 1.05rem; margin: 28px 0 10px; }
        .explainer {
            background: var(--panel);
            padding: 14px 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid var(--border);
            color: var(--muted);
            font-size: 0.85rem;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
            margin-bottom: 8px;
        }
        .desc-card {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px 16px;
        }
        .desc-card.best { border-color: var(--good); border-width: 2px; }
        .desc-card .label {
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: var(--muted);
            margin-bottom: 6px;
        }
        .desc-card.best .label { color: var(--good); }
        .desc-card .text { font-size: 0.88rem; }
        .stat-row {
            display: flex;
            gap: 18px;
            align-items: center;
            font-size: 0.85rem;
            color: var(--muted);
            margin: 10px 0 4px;
        }
        .score-pill {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 2px 9px;
            border-radius: 999px;
            font-weight: 700;
            font-size: 0.82rem;
        }
        .score-good { background: var(--good-bg); color: var(--good); }
        .score-ok { background: var(--ok-bg); color: var(--ok); }
        .score-bad { background: var(--bad-bg); color: var(--bad); }

        details.iteration {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 8px;
            padding: 0;
        }
        details.iteration[open] { padding-bottom: 4px; }
        details.iteration.best-row { border-color: var(--good); border-width: 2px; }
        details.iteration summary {
            cursor: pointer;
            padding: 10px 14px;
            display: flex;
            align-items: center;
            gap: 14px;
            font-size: 0.88rem;
            list-style: none;
        }
        details.iteration summary::-webkit-details-marker { display: none; }
        details.iteration summary::before {
            content: "▸";
            color: var(--muted);
            font-size: 0.75rem;
            width: 10px;
        }
        details.iteration[open] summary::before { content: "▾"; }
        .iter-num { font-weight: 700; min-width: 62px; }
        .best-tag {
            font-size: 0.68rem;
            font-weight: 700;
            color: var(--good);
            background: var(--good-bg);
            padding: 1px 7px;
            border-radius: 999px;
        }
        .iteration .desc-body {
            padding: 4px 14px 12px 38px;
            font-size: 0.85rem;
            color: var(--ink);
        }

        .table-container { overflow-x: auto; }
        table {
            border-collapse: collapse;
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 0.82rem;
            width: 100%;
        }
        th, td {
            padding: 7px 10px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }
        th {
            font-weight: 700;
            background: var(--ink);
            color: var(--bg);
            font-size: 0.75rem;
            white-space: nowrap;
        }
        th.iter-col { text-align: center; cursor: help; }
        th.iter-col.best-col { background: var(--good); }
        td.query-cell { max-width: 380px; }
        td.query-cell .q-text { display: block; }
        .polarity-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 7px;
            flex-shrink: 0;
        }
        .dot-positive { background: var(--good); }
        .dot-negative { background: var(--bad); }
        .test-tag {
            font-size: 0.65rem;
            font-weight: 700;
            color: var(--test-accent);
            background: var(--test-bg);
            padding: 1px 6px;
            border-radius: 999px;
            margin-left: 8px;
        }
        td.result-cell {
            text-align: center;
            font-size: 0.95rem;
        }
        td.result-cell.best-col { background: var(--good-bg); }
        .pass { color: var(--good); }
        .fail { color: var(--bad); }
        .rate { display: block; font-size: 0.65rem; color: var(--muted); font-weight: 400; }
        .section-row td {
            background: var(--bg);
            font-weight: 700;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: var(--muted);
            padding: 5px 10px;
        }
        .legend { display: flex; gap: 20px; margin-bottom: 12px; font-size: 0.78rem; color: var(--muted); align-items: center; flex-wrap: wrap; }
        .legend-item { display: flex; align-items: center; gap: 6px; }
    </style>
</head>
<body>
    <h1>""" + title_prefix + """Skill Description Optimization</h1>
    <div class="explainer">
        Claude tests different versions of your skill's description against the queries below, trying to find
        one that triggers correctly on everything. <strong>Train</strong> queries are what it improves against;
        <strong>Test</strong> queries are held out so a good score isn't just memorization. Click an iteration
        below to read its full description. The best-scoring one (highlighted) gets applied to your skill when
        the run finishes.
    </div>
"""]

    # Summary: original vs best, side by side.
    best_test_score = data.get("best_test_score")
    best_train_score = data.get("best_train_score")
    best_score_label = f"{best_test_score} (test)" if best_test_score else f"{best_train_score} (train)" if best_train_score else data.get("best_score", "in progress")
    html_parts.append(f"""
    <div class="summary-grid">
        <div class="desc-card">
            <div class="label">Original description</div>
            <div class="text">{html.escape(data.get('original_description', 'N/A'))}</div>
        </div>
        <div class="desc-card best">
            <div class="label">Best so far &middot; score {html.escape(str(best_score_label))}</div>
            <div class="text">{html.escape(data.get('best_description', 'N/A'))}</div>
        </div>
    </div>
    <div class="stat-row">
        <span><strong>{data.get('iterations_run', len(iterations))}</strong> iterations run</span>
        <span><strong>{data.get('train_size', len(train_queries))}</strong> train queries</span>
        <span><strong>{data.get('test_size', len(test_queries))}</strong> test queries</span>
    </div>
""")

    # Iteration list — collapsible, description shown once per iteration here
    # (not repeated in every table cell).
    html_parts.append('    <h2>Iterations</h2>\n')
    for it in iterations:
        row_class = "best-row" if it["is_best"] else ""
        train_class = score_class(it["train_correct"], it["train_runs"])
        test_class = score_class(it["test_correct"], it["test_runs"]) if it["test_runs"] else None
        open_attr = " open" if it["is_best"] else ""
        test_pill = (
            f'<span class="score-pill {test_class}">test {it["test_correct"]}/{it["test_runs"]}</span>'
            if it["test_runs"] else ""
        )
        best_tag = '<span class="best-tag">BEST</span>' if it["is_best"] else ""
        html_parts.append(f"""    <details class="iteration {row_class}"{open_attr}>
        <summary>
            <span class="iter-num">Iter {it['iteration']}</span>
            <span class="score-pill {train_class}">train {it['train_correct']}/{it['train_runs']}</span>
            {test_pill}
            {best_tag}
        </summary>
        <div class="desc-body">{html.escape(it['description'])}</div>
    </details>
""")

    # Legend for the per-query table
    html_parts.append("""
    <h2>Per-query results</h2>
    <div class="legend">
        <span class="legend-item"><span class="polarity-dot dot-positive"></span> Should trigger</span>
        <span class="legend-item"><span class="polarity-dot dot-negative"></span> Should NOT trigger</span>
        <span class="legend-item"><span class="test-tag">TEST</span> held-out query</span>
        <span class="legend-item">Hover a column header for that iteration's full description</span>
    </div>
""")

    # Table: queries as ROWS, iterations as COLUMNS — reading across a row
    # shows whether that one query's pass/fail changed as the description
    # evolved, without needing one column per query (which forces awkward
    # wrapped/rotated headers once there are more than a handful of queries).
    html_parts.append('    <div class="table-container">\n    <table>\n        <thead>\n            <tr>\n                <th>Query</th>\n')
    for it in iterations:
        best_col = " best-col" if it["is_best"] else ""
        title = html.escape(it["description"])
        html_parts.append(f'                <th class="iter-col{best_col}" title="{title}">It.{it["iteration"]}</th>\n')
    html_parts.append('            </tr>\n        </thead>\n        <tbody>\n')

    def render_query_rows(queries: list[dict], is_test: bool):
        for qinfo in queries:
            dot = "dot-positive" if qinfo["should_trigger"] else "dot-negative"
            test_tag = '<span class="test-tag">TEST</span>' if is_test else ""
            html_parts.append(f'            <tr>\n                <td class="query-cell"><span class="polarity-dot {dot}"></span><span class="q-text">{html.escape(qinfo["query"])}</span>{test_tag}</td>\n')
            for it in iterations:
                lookup = it["test_by_query"] if is_test else it["train_by_query"]
                r = lookup.get(qinfo["query"], {})
                did_pass = r.get("pass", False)
                triggers = r.get("triggers", 0)
                runs = r.get("runs", 0)
                icon = "✓" if did_pass else "✗"
                css_class = "pass" if did_pass else "fail"
                best_col = " best-col" if it["is_best"] else ""
                html_parts.append(f'                <td class="result-cell {css_class}{best_col}">{icon}<span class="rate">{triggers}/{runs}</span></td>\n')
            html_parts.append('            </tr>\n')

    if train_queries:
        html_parts.append(f'            <tr class="section-row"><td colspan="{len(iterations) + 1}">Train queries</td></tr>\n')
        render_query_rows(train_queries, is_test=False)
    if test_queries:
        html_parts.append(f'            <tr class="section-row"><td colspan="{len(iterations) + 1}">Test queries (held out)</td></tr>\n')
        render_query_rows(test_queries, is_test=True)

    html_parts.append("""        </tbody>
    </table>
    </div>
</body>
</html>
""")

    return "".join(html_parts)


def main():
    parser = argparse.ArgumentParser(description="Generate HTML report from run_loop output")
    parser.add_argument("input", help="Path to JSON output from run_loop.py (or - for stdin)")
    parser.add_argument("-o", "--output", default=None, help="Output HTML file (default: stdout)")
    parser.add_argument("--skill-name", default="", help="Skill name to include in the report title")
    args = parser.parse_args()

    if args.input == "-":
        data = json.load(sys.stdin)
    else:
        data = json.loads(Path(args.input).read_text())

    html_output = generate_html(data, skill_name=args.skill_name)

    if args.output:
        Path(args.output).write_text(html_output)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(html_output)


if __name__ == "__main__":
    main()
