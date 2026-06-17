"""Qualtrics Survey Data Inspector — CLI entry point."""

import argparse
import json
import sys
from pathlib import Path

from src.parser import parse_csv
from src.quality import compute_quality
from src.report import generate_text_report, generate_html_report, export_clean_csv


def _load_survey(path: str):
    """Read and parse a survey CSV file."""
    file_path = Path(path)
    if not file_path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    content = file_path.read_text(encoding="utf-8-sig")
    return parse_csv(content), file_path.name


def cmd_inspect(args):
    """Run quality inspection and print a report."""
    survey, name = _load_survey(args.file)

    scale_groups = None
    if args.scales:
        scales_path = Path(args.scales)
        if not scales_path.exists():
            print(f"Error: scales file not found: {args.scales}", file=sys.stderr)
            sys.exit(1)
        with open(scales_path, encoding="utf-8") as f:
            scale_groups = json.load(f)

    quality = compute_quality(survey, scale_groups=scale_groups, timing_threshold=args.threshold)
    text = generate_text_report(quality, survey, source_name=name)
    print(text)

    if args.html:
        html_path = Path(args.html)
        html_content = generate_html_report(quality, survey, source_name=name)
        html_path.write_text(html_content, encoding="utf-8")
        print(f"\nHTML report written to: {args.html}", file=sys.stderr)


def cmd_clean(args):
    """Export a cleaned CSV with QI_Flags column."""
    survey, name = _load_survey(args.file)

    scale_groups = None
    if hasattr(args, "scales") and args.scales:
        with open(args.scales, encoding="utf-8") as f:
            scale_groups = json.load(f)

    quality = compute_quality(survey, scale_groups=scale_groups, timing_threshold=args.threshold)

    cleaned = export_clean_csv(
        survey,
        quality,
        exclude_incomplete=not args.keep_incomplete,
        exclude_fast=not args.keep_fast,
        exclude_straight_liners=not args.keep_straight_liners,
    )

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(cleaned, encoding="utf-8")
        removed = survey.respondent_count - cleaned.count("\n") + 1
        print(f"Clean CSV written to: {args.output}", file=sys.stderr)
    else:
        print(cleaned)


def main():
    parser = argparse.ArgumentParser(
        prog="qi",
        description="Qualtrics Survey Data Inspector — quality-check a CSV export",
    )
    sub = parser.add_subparsers(dest="command")

    # inspect subcommand
    p_inspect = sub.add_parser("inspect", help="Print a quality report")
    p_inspect.add_argument("file", help="Path to Qualtrics CSV export")
    p_inspect.add_argument("--html", metavar="OUTPUT.html",
                           help="Also write a self-contained HTML report")
    p_inspect.add_argument("--threshold", type=int, default=60, metavar="SECONDS",
                           help="Minimum acceptable response time in seconds (default: 60)")
    p_inspect.add_argument("--scales", metavar="SCALES.json",
                           help="JSON file mapping scale names to column lists")
    p_inspect.set_defaults(func=cmd_inspect)

    # clean subcommand
    p_clean = sub.add_parser("clean", help="Export a cleaned CSV")
    p_clean.add_argument("file", help="Path to Qualtrics CSV export")
    p_clean.add_argument("--output", "-o", metavar="OUTPUT.csv",
                         help="Output path (default: stdout)")
    p_clean.add_argument("--threshold", type=int, default=60, metavar="SECONDS",
                         help="Fast-response threshold in seconds (default: 60)")
    p_clean.add_argument("--keep-incomplete", action="store_true",
                         help="Do not remove incomplete responses")
    p_clean.add_argument("--keep-fast", action="store_true",
                         help="Do not remove fast responses")
    p_clean.add_argument("--keep-straight-liners", action="store_true",
                         help="Do not remove straight-liners")
    p_clean.set_defaults(func=cmd_clean)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
