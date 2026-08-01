"""ItemScope command-line interface."""

from __future__ import annotations

import argparse
import sys

from itemscope import ai, report, stats
from itemscope.parser import ItemScopeParseError, load_answer_key, load_response_csv, score_matrix

WORST_ITEM_COUNT_FOR_AI = 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="itemscope",
        description="Classical test theory item analysis for exam/quiz response CSVs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a response CSV")
    analyze_parser.add_argument("input_csv", help="Path to the response CSV")
    analyze_parser.add_argument(
        "--key", dest="key_csv", default=None, help="Path to an item,answer CSV (raw-option input)"
    )
    analyze_parser.add_argument(
        "--student-id-col", dest="student_id_col", default=None,
        help="Name of the student ID column (auto-detected if omitted)",
    )
    analyze_parser.add_argument(
        "--format", choices=["text", "json", "html"], default="html",
        help="Output format (default: html)",
    )
    analyze_parser.add_argument(
        "--output", "-o", default=None, help="Write output to this file instead of stdout",
    )
    analyze_parser.add_argument(
        "--ai", action="store_true",
        help="Generate AI suggestions for the worst-scoring items (requires ANTHROPIC_API_KEY)",
    )
    return parser


def _worst_items(test_stats: stats.TestStats, n: int) -> list[stats.ItemStats]:
    def severity(item: stats.ItemStats) -> tuple[int, float]:
        return (-len(item.flags), item.discrimination if item.discrimination is not None else 1.0)

    flagged = [item for item in test_stats.items if item.flags]
    return sorted(flagged, key=severity)[:n]


def run_analyze(args: argparse.Namespace) -> int:
    try:
        matrix = load_response_csv(args.input_csv, student_id_col=args.student_id_col)
        key = load_answer_key(args.key_csv) if args.key_csv else None
        scored = score_matrix(matrix, key)
    except ItemScopeParseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    test_stats = stats.analyze(scored)

    suggestions = {}
    if args.ai:
        for item in _worst_items(test_stats, WORST_ITEM_COUNT_FOR_AI):
            text, source = ai.generate_item_suggestion(item)
            suggestions[item.item_id] = {"text": text, "source": source}

    if args.format == "text":
        output = report.render_text(test_stats)
        if suggestions:
            output += "\n\nAI suggestions:\n"
            for item_id, s in suggestions.items():
                output += f"  {item_id} ({s['source']}): {s['text']}\n"
    elif args.format == "json":
        data = report.to_dict(test_stats)
        data["ai_suggestions"] = suggestions
        import json as _json

        output = _json.dumps(data, indent=2)
    else:
        output = report.render_html(test_stats)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
        print(f"Wrote report to {args.output}")
    else:
        print(output)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "analyze":
        return run_analyze(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
