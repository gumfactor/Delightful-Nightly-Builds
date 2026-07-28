"""Voiceprint CLI: analyze, batch, and history commands."""

from __future__ import annotations

import argparse
import glob
import os
import sys
from datetime import datetime, timezone

from . import ai_review, heuristics, report, scoring
from .storage import HistoryStore

DEFAULT_DB_PATH = "voiceprint.db"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _run_analysis(path: str, use_ai: bool, db_path: str) -> dict:
    text = _read_text_file(path)
    analysis = heuristics.analyze_text(text)
    score_result = scoring.compute_score(analysis)

    store = HistoryStore(db_path)
    store.record_run(
        path,
        now_iso(),
        analysis["word_count"],
        score_result["score"],
        score_result["flag_count"],
        {"breakdown": score_result["breakdown"]},
    )

    review = None
    if use_ai:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        worst = ai_review.pick_worst_paragraphs(analysis["paragraphs"])
        review = ai_review.get_review(worst, score_result["breakdown"], api_key=api_key)

    history = store.get_history(path)
    return {
        "analysis": analysis,
        "score_result": score_result,
        "review": review,
        "history": history,
    }


def cmd_analyze(args: argparse.Namespace) -> int:
    if not os.path.isfile(args.path):
        print(f"error: file not found: {args.path}", file=sys.stderr)
        return 1

    result = _run_analysis(args.path, args.ai, args.db)

    if args.json:
        print(
            report.render_json(
                args.path, result["analysis"], result["score_result"], result["review"]
            )
        )
    else:
        print(
            report.render_terminal(
                args.path,
                result["analysis"],
                result["score_result"],
                result["review"],
                use_color=sys.stdout.isatty(),
            )
        )

    if args.html:
        html_content = report.render_html(
            args.path,
            result["analysis"],
            result["score_result"],
            result["review"],
            result["history"],
        )
        with open(args.html, "w", encoding="utf-8") as handle:
            handle.write(html_content)
        print(f"HTML report written to {args.html}", file=sys.stderr)

    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    if not os.path.isdir(args.directory):
        print(f"error: directory not found: {args.directory}", file=sys.stderr)
        return 1

    patterns = ["*.md", "*.txt"]
    paths = sorted(
        {
            p
            for pattern in patterns
            for p in glob.glob(os.path.join(args.directory, pattern))
        }
    )
    if not paths:
        print(f"No .md or .txt files found in {args.directory}", file=sys.stderr)
        return 0

    exit_code = 0
    for path in paths:
        result = _run_analysis(path, args.ai, args.db)
        print(
            report.render_terminal(
                path,
                result["analysis"],
                result["score_result"],
                result["review"],
                use_color=sys.stdout.isatty(),
            )
        )
        print()

        if args.html_dir:
            os.makedirs(args.html_dir, exist_ok=True)
            out_name = os.path.splitext(os.path.basename(path))[0] + ".html"
            out_path = os.path.join(args.html_dir, out_name)
            html_content = report.render_html(
                path,
                result["analysis"],
                result["score_result"],
                result["review"],
                result["history"],
            )
            with open(out_path, "w", encoding="utf-8") as handle:
                handle.write(html_content)

    return exit_code


def cmd_history(args: argparse.Namespace) -> int:
    store = HistoryStore(args.db)
    history = store.get_history(args.path)
    if not history:
        print(f"No history recorded for {args.path}")
        return 0

    print(f"History for {args.path} ({len(history)} run(s)):")
    previous_score = None
    for entry in history:
        delta = ""
        if previous_score is not None:
            change = entry["score"] - previous_score
            sign = "+" if change >= 0 else ""
            delta = f" ({sign}{change:.1f})"
        bar_len = max(0, min(50, round(entry["score"] / 2)))
        bar = "#" * bar_len
        print(f"  {entry['run_at']}  {entry['score']:5.1f}{delta}  {bar}")
        previous_score = entry["score"]

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="voiceprint",
        description="Audit a writing draft for AI-tell and formulaic prose patterns.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze a single file")
    analyze.add_argument("path", help="Path to a Markdown/text draft")
    analyze.add_argument("--ai", action="store_true", help="Request a Claude second opinion")
    analyze.add_argument("--json", action="store_true", help="Print JSON instead of terminal report")
    analyze.add_argument("--html", metavar="OUTFILE", help="Write an HTML report to this path")
    analyze.add_argument("--db", default=DEFAULT_DB_PATH, help="History database path")
    analyze.set_defaults(func=cmd_analyze)

    batch = subparsers.add_parser("batch", help="Analyze every .md/.txt file in a directory")
    batch.add_argument("directory", help="Directory of drafts")
    batch.add_argument("--ai", action="store_true", help="Request a Claude second opinion per file")
    batch.add_argument("--html-dir", metavar="DIR", help="Write one HTML report per file into DIR")
    batch.add_argument("--db", default=DEFAULT_DB_PATH, help="History database path")
    batch.set_defaults(func=cmd_batch)

    history = subparsers.add_parser("history", help="Show score history for a file")
    history.add_argument("path", help="Path to a previously analyzed file")
    history.add_argument("--db", default=DEFAULT_DB_PATH, help="History database path")
    history.set_defaults(func=cmd_history)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
