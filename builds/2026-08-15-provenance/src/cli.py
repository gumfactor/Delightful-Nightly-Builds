"""Provenance CLI — batch Canadian-ownership classification.

    python -m src.cli classify businesses.csv --out enriched.csv
    python -m src.cli classify businesses.csv --ai-enrich --render report.html
    python -m src.cli history "Acme Ltd."
"""

from __future__ import annotations

import argparse
import os
import sys

from src import batch, report, store


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="provenance",
        description="Batch-classify a CSV of business names as Canadian, foreign, or uncertain.",
    )
    subparsers = parser.add_subparsers(dest="command")

    classify_parser = subparsers.add_parser("classify", help="Classify a CSV of businesses.")
    classify_parser.add_argument("input_csv", help="CSV with at least a 'name' column.")
    classify_parser.add_argument("--out", default=None, help="Output CSV path (default: <input>.enriched.csv).")
    classify_parser.add_argument("--db", default="provenance.db", help="SQLite cache/history path.")
    classify_parser.add_argument("--refresh", action="store_true", help="Ignore the cache and re-resolve every row.")
    classify_parser.add_argument("--ai-enrich", action="store_true", help="Add a Claude Haiku note to uncertain rows.")
    classify_parser.add_argument("--render", default=None, help="Also write a self-contained HTML report to this path.")

    history_parser = subparsers.add_parser("history", help="Show every resolution recorded for a business.")
    history_parser.add_argument("business_name")
    history_parser.add_argument("--db", default="provenance.db", help="SQLite cache/history path.")

    return parser


def _default_output_path(input_csv: str) -> str:
    root, _ext = os.path.splitext(input_csv)
    return f"{root}.enriched.csv"


def _run_classify(args: argparse.Namespace) -> int:
    rows = batch.read_input_csv(args.input_csv)
    if not rows:
        print("No rows found in input CSV.")
        return 1

    input_fieldnames = list(rows[0].keys())
    if "name" not in input_fieldnames:
        print("Input CSV must have a 'name' column.")
        return 1

    conn = store.connect(args.db)
    try:
        output_rows, stats = batch.classify_batch(
            rows,
            conn,
            refresh=args.refresh,
            ai_enrich_enabled=args.ai_enrich,
        )
    finally:
        conn.close()

    out_path = args.out or _default_output_path(args.input_csv)
    batch.write_output_csv(out_path, output_rows, input_fieldnames)

    print(f"Classified {stats['total']} businesses ({stats['skipped']} skipped for missing name).")
    print(f"  Canadian: {stats['canadian']}  Foreign: {stats['foreign']}  Uncertain: {stats['uncertain']}")
    print(f"  Cache hits: {stats['cache_hits']}  Cache misses: {stats['cache_misses']}")
    print(f"Wrote {out_path}")

    uncertain_rows = [row for row in output_rows if row["verdict"] == "uncertain"]
    if uncertain_rows:
        print("\nWorth a human look (uncertain):")
        for row in uncertain_rows[:10]:
            print(f"  - {row.get('name')}: {row.get('evidence')}")

    if args.render:
        html = report.render_html(output_rows, stats)
        with open(args.render, "w", encoding="utf-8") as handle:
            handle.write(html)
        print(f"Wrote {args.render}")

    return 0


def _run_history(args: argparse.Namespace) -> int:
    conn = store.connect(args.db)
    try:
        rows = store.get_history(conn, args.business_name)
    finally:
        conn.close()

    if not rows:
        print(f"No history found for '{args.business_name}'.")
        return 1

    for row in rows:
        print(f"[{row['resolved_at']}] {row['verdict']} (confidence {row['confidence']:.2f}) — {row['evidence']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "classify":
        return _run_classify(args)
    if args.command == "history":
        return _run_history(args)

    parser.print_usage()
    return 1


if __name__ == "__main__":
    sys.exit(main())
