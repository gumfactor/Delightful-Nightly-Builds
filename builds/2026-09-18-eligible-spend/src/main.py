#!/usr/bin/env python3
"""Eligible Spend -- Tri-Agency (NSERC/CIHR/SSHRC) grant budget
compliance checker.

Checks an itemized budget CSV against the Tri-Agency Guide on Financial
Administration's public principles and named ineligible items. See
Manual.md for full usage and the disclaimer on what this tool does not
cover.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime

from ai_review import annotate_all
from csv_io import BudgetCsvError, load_budget_csv
from report import render_html, render_terminal, write_flagged_csv
from rules import evaluate_all


def _parse_date_arg(raw: str) -> date:
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid date {raw!r} -- expected YYYY-MM-DD")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eligible-spend",
        description="Check a Tri-Agency grant budget CSV for known-ineligible line items.",
    )
    parser.add_argument("csv_path", help="Path to the itemized budget CSV")
    parser.add_argument("--grant-start", required=True, type=_parse_date_arg, help="Grant period start date (YYYY-MM-DD)")
    parser.add_argument("--grant-end", required=True, type=_parse_date_arg, help="Grant period end date (YYYY-MM-DD)")
    parser.add_argument("--out-dir", default=".", help="Directory to write report.html and flagged_items.csv into (default: current directory)")
    parser.add_argument("--ai", action="store_true", help="Enable optional Claude Haiku review notes (requires ANTHROPIC_API_KEY)")
    return parser


def run(argv: list[str]) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.grant_start > args.grant_end:
        print("Error: --grant-start must be on or before --grant-end", file=sys.stderr)
        return 2

    try:
        lines = load_budget_csv(args.csv_path)
    except FileNotFoundError:
        print(f"Error: input file not found: {args.csv_path}", file=sys.stderr)
        return 2
    except BudgetCsvError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    verdicts = evaluate_all(lines, args.grant_start, args.grant_end)

    ai_notes = {}
    if args.ai:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Note: --ai was passed but ANTHROPIC_API_KEY is not set; using deterministic fallback notes.", file=sys.stderr)
        ai_notes = annotate_all(verdicts, use_ai=True, api_key=api_key)

    print(render_terminal(verdicts, args.grant_start, args.grant_end))

    os.makedirs(args.out_dir, exist_ok=True)
    html_path = os.path.join(args.out_dir, "report.html")
    csv_path = os.path.join(args.out_dir, "flagged_items.csv")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(render_html(verdicts, args.grant_start, args.grant_end, ai_notes))

    flagged_count = write_flagged_csv(verdicts, csv_path)

    print(f"\nReport written to {html_path}")
    print(f"{flagged_count} flagged item(s) written to {csv_path}")

    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
