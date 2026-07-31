"""CLI entry point for the BIDS Dataset Organizer & Validator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .ai_summary import generate_ai_summary
from .fixer import apply_fixes, compute_padding_fixes
from .report import build_report_dict, render_html, render_json, render_text
from .scanner import validate_dataset


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bids-check",
        description="Validate a directory against core BIDS naming rules.",
    )
    parser.add_argument("dataset_path", help="Path to the dataset root directory")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually rename files to fix zero-padding inconsistencies "
        "(default is dry-run: fixes are only reported)",
    )
    parser.add_argument(
        "--ai-summary",
        action="store_true",
        help="Send structural findings to Claude for a plain-English action list "
        "(requires ANTHROPIC_API_KEY)",
    )
    parser.add_argument("--json-report", metavar="PATH", help="Write a JSON report to PATH")
    parser.add_argument("--html-report", metavar="PATH", help="Write an HTML report to PATH")
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    dataset_path = Path(args.dataset_path)
    try:
        result = validate_dataset(dataset_path)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    fix_results = []
    if args.apply or True:
        # Padding fixes are always computed so the report can show what
        # --apply would do (or did do); only --apply performs the rename.
        plans = compute_padding_fixes(result.files)
        if plans:
            fix_results = apply_fixes(plans, dataset_path, dry_run=not args.apply)

    ai_summary = None
    if args.ai_summary:
        ai_summary = generate_ai_summary(result.findings)

    report = build_report_dict(result, ai_summary=ai_summary)
    report["fixes"] = [
        {
            "old_path": r.plan.old_relpath,
            "new_path": r.plan.new_relpath,
            "reason": r.plan.reason,
            "status": r.status,
        }
        for r in fix_results
    ]

    print(render_text(report))
    if fix_results:
        applied = sum(1 for r in fix_results if r.status == "applied")
        planned = sum(1 for r in fix_results if r.status == "planned")
        if applied:
            print(f"\nApplied {applied} padding fix(es).")
        if planned:
            print(
                f"\n{planned} padding fix(es) available — re-run with --apply to perform them."
            )

    if args.json_report:
        Path(args.json_report).write_text(render_json(report))
    if args.html_report:
        Path(args.html_report).write_text(render_html(report))

    return 1 if report["summary"]["errors"] > 0 else 0


if __name__ == "__main__":
    sys.exit(run())
