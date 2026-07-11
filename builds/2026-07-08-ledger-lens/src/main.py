"""Ledger Lens CLI — categorize a bank/credit-card CSV export into a spending report."""

from __future__ import annotations

import argparse
import csv
import json
import sys

try:
    from . import ai_client, analyze, categorize, parser as txn_parser, report_html, report_terminal
except ImportError:  # allow running as `python src/main.py` (no package context)
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src import ai_client, analyze, categorize, parser as txn_parser, report_html, report_terminal


def load_budgets(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write_cleaned_csv(path: str, transactions: list) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Date", "Description", "Amount", "Category", "Recurring"])
        for txn in sorted(transactions, key=lambda t: t.date):
            writer.writerow([
                txn.date.isoformat(), txn.description, f"{txn.amount:.2f}",
                txn.category, "yes" if txn.recurring else "no",
            ])


def run_analysis(args: argparse.Namespace) -> dict:
    parsed = txn_parser.parse_csv(args.input, invert_sign=args.invert_sign)
    transactions = parsed.transactions

    if not transactions:
        raise SystemExit(
            f"No valid transactions found in '{args.input}' "
            f"({parsed.skipped_rows} row(s) skipped as malformed)."
        )

    categorize.categorize_transactions(transactions, use_ai=not args.no_ai)

    summary = analyze.compute_summary(transactions)
    monthly = analyze.compute_monthly_breakdown(transactions)
    category_breakdown = analyze.compute_category_breakdown(transactions)
    top_merchants = analyze.compute_top_merchants(transactions)
    recurring = analyze.detect_recurring(transactions)

    budget_status = None
    if args.budgets:
        budgets = load_budgets(args.budgets)
        budget_status = analyze.compare_budgets(category_breakdown, budgets, summary["months_covered"])

    insights = None
    if not args.no_ai and ai_client.is_configured():
        insights = ai_client.generate_insights({
            "summary": summary, "categories": category_breakdown, "monthly": monthly,
        })
    if not insights:
        insights = analyze.generate_fallback_insights(summary, category_breakdown, monthly)

    return {
        "transactions": transactions,
        "skipped_rows": parsed.skipped_rows,
        "summary": summary,
        "monthly": monthly,
        "categories": category_breakdown,
        "top_merchants": top_merchants,
        "recurring": recurring,
        "budget_status": budget_status,
        "insights": insights,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ledger-lens",
        description="Categorize a bank/credit-card CSV export into a spending report.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_cmd = subparsers.add_parser("analyze", help="Analyze a transaction CSV export.")
    analyze_cmd.add_argument("input", help="Path to the transaction CSV file.")
    analyze_cmd.add_argument("--budgets", help="Path to a budgets.json (category -> monthly cap).")
    analyze_cmd.add_argument("--html", help="Write a self-contained HTML dashboard to this path.")
    analyze_cmd.add_argument("--json", action="store_true", help="Print JSON to stdout instead of a terminal summary.")
    analyze_cmd.add_argument("--out-csv", help="Write a cleaned CSV (with Category/Recurring columns) to this path.")
    analyze_cmd.add_argument("--currency-symbol", default="$", help="Currency symbol for display (default: $).")
    analyze_cmd.add_argument("--invert-sign", action="store_true", help="Treat positive amounts as expenses (some card issuers).")
    analyze_cmd.add_argument("--no-ai", action="store_true", help="Disable Claude enrichment even if ANTHROPIC_API_KEY is set.")

    return parser


def main(argv: list | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        try:
            result = run_analysis(args)
        except txn_parser.ParseError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        except (json.JSONDecodeError, FileNotFoundError) as exc:
            print(f"Error reading budgets file: {exc}", file=sys.stderr)
            return 1

        if args.out_csv:
            write_cleaned_csv(args.out_csv, result["transactions"])

        if args.html:
            html_output = report_html.render_html(
                result["summary"], result["monthly"], result["categories"],
                result["top_merchants"], result["recurring"], result["transactions"],
                result["budget_status"], result["insights"], args.currency_symbol,
            )
            with open(args.html, "w", encoding="utf-8") as fh:
                fh.write(html_output)

        if args.json:
            payload = {
                "summary": result["summary"],
                "monthly": result["monthly"],
                "categories": result["categories"],
                "top_merchants": result["top_merchants"],
                "recurring": result["recurring"],
                "budget_status": result["budget_status"],
                "insights": result["insights"],
                "skipped_rows": result["skipped_rows"],
            }
            print(json.dumps(payload, indent=2))
        else:
            print(report_terminal.render_terminal(
                result["summary"], result["categories"], result["top_merchants"],
                result["recurring"], result["budget_status"], result["insights"],
                args.currency_symbol,
            ))

        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
