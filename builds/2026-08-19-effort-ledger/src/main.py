"""Effort Ledger CLI — audits a grant budget CSV and an effort-commitment CSV."""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ai_narrative import build_aggregate_summary, generate_ai_briefing
from src.budget_audit import audit_budget
from src.effort_audit import audit_effort
from src.loader import load_budget_csv, load_effort_csv
from src.models import AuditConfig, Flag
from src.report import render_html


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="effort-ledger",
        description="Audit a grant budget CSV and an effort-commitment CSV for indirect-cost "
        "math errors and cross-grant effort overcommitment.",
    )
    parser.add_argument("--budget", required=True, help="Path to budget.csv")
    parser.add_argument("--effort", required=True, help="Path to effort.csv")
    parser.add_argument(
        "--far-rate",
        required=True,
        type=float,
        help="F&A/indirect rate as a decimal, e.g. 0.55 for 55%%",
    )
    parser.add_argument(
        "--exempt-categories",
        default="Equipment",
        help="Comma-separated budget categories fully excluded from MTDC (default: Equipment)",
    )
    parser.add_argument(
        "--subcontract-threshold",
        type=float,
        default=25000.0,
        help="Dollars of each subcontract line included in MTDC (default: 25000)",
    )
    parser.add_argument(
        "--effort-cap",
        type=float,
        default=100.0,
        help="Percent effort ceiling before a window is flagged (default: 100)",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=1.00,
        help="Dollar tolerance before an indirect-cost mismatch is flagged (default: 1.00)",
    )
    parser.add_argument("--output", default="report.html", help="Path to write the HTML report")
    parser.add_argument(
        "--ai", action="store_true", help="Enable the optional aggregate-only Claude Haiku narrative"
    )
    return parser


def run_audit(args: argparse.Namespace) -> dict:
    config = AuditConfig(
        far_rate=args.far_rate,
        mtdc_exempt_categories=frozenset(
            c.strip() for c in args.exempt_categories.split(",") if c.strip()
        ),
        subcontract_exempt_threshold=args.subcontract_threshold,
        effort_cap_percent=args.effort_cap,
        tolerance=args.tolerance,
    )

    budget_lines, budget_load_flags = load_budget_csv(args.budget)
    effort_lines, effort_load_flags = load_effort_csv(args.effort)

    budget_audit_flags, summaries = audit_budget(budget_lines, config)
    budget_grant_ids = {bl.grant_id for bl in budget_lines}
    effort_audit_flags, windows = audit_effort(effort_lines, budget_grant_ids, config)

    budget_flags: list[Flag] = budget_load_flags + budget_audit_flags
    effort_flags: list[Flag] = effort_load_flags + effort_audit_flags
    all_flags: list[Flag] = budget_flags + effort_flags

    ai_briefing = ""
    if args.ai:
        aggregate = build_aggregate_summary(all_flags, summaries, windows)
        ai_briefing = generate_ai_briefing(aggregate, os.environ.get("ANTHROPIC_API_KEY"))

    return {
        "config": config,
        "budget_lines": budget_lines,
        "effort_lines": effort_lines,
        "flags": all_flags,
        "budget_flags": budget_flags,
        "effort_flags": effort_flags,
        "summaries": summaries,
        "windows": windows,
        "ai_briefing": ai_briefing,
    }


def _flags_by_row(flags: list[Flag]) -> dict[int, list[str]]:
    by_row: dict[int, list[str]] = {}
    for f in flags:
        for row_number in f.row_numbers:
            by_row.setdefault(row_number, []).append(f.code)
    return by_row


def write_annotated_budget_csv(path: str, budget_lines, flags: list[Flag]) -> None:
    by_row = _flags_by_row(flags)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["grant_id", "grant_name", "fiscal_year", "category", "description", "direct_cost", "Flags"]
        )
        for bl in budget_lines:
            writer.writerow(
                [
                    bl.grant_id,
                    bl.grant_name,
                    bl.fiscal_year,
                    bl.category,
                    bl.description,
                    bl.direct_cost,
                    ";".join(by_row.get(bl.row_number, [])),
                ]
            )


def write_annotated_effort_csv(path: str, effort_lines, flags: list[Flag]) -> None:
    by_row = _flags_by_row(flags)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "person_name",
                "grant_id",
                "grant_name",
                "period_start",
                "period_end",
                "percent_effort",
                "Flags",
            ]
        )
        for el in effort_lines:
            writer.writerow(
                [
                    el.person_name,
                    el.grant_id,
                    el.grant_name,
                    el.period_start.isoformat(),
                    el.period_end.isoformat(),
                    el.percent_effort,
                    ";".join(by_row.get(el.row_number, [])),
                ]
            )


def print_text_summary(result: dict) -> None:
    flags = result["flags"]
    errors = [f for f in flags if f.severity.value == "error"]
    warnings = [f for f in flags if f.severity.value == "warning"]
    infos = [f for f in flags if f.severity.value == "info"]

    print(f"Effort Ledger — audited {len(result['summaries'])} grant/fiscal-year group(s)")
    print(f"  {len(errors)} error(s), {len(warnings)} warning(s), {len(infos)} info")
    for f in errors + warnings:
        print(f"  [{f.severity.value.upper()}] {f.code}: {f.message}")
    if result["ai_briefing"]:
        print("\nAI Briefing:")
        print(f"  {result['ai_briefing']}")


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    result = run_audit(args)

    html = render_html(
        result["summaries"],
        result["flags"],
        result["windows"],
        result["effort_lines"],
        result["ai_briefing"],
    )
    Path(args.output).write_text(html, encoding="utf-8")

    output_dir = Path(args.output).parent
    write_annotated_budget_csv(
        str(output_dir / "budget_flagged.csv"), result["budget_lines"], result["budget_flags"]
    )
    write_annotated_effort_csv(
        str(output_dir / "effort_flagged.csv"), result["effort_lines"], result["effort_flags"]
    )

    print_text_summary(result)
    print(f"\nReport written to {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
