"""Qualtrics Survey Data Inspector — CLI entry point."""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from src.parser import parse_csv
from src.quality import compute_quality, QualityThresholds
from src.report import generate_text_report, generate_html_report, export_clean_csv
from src.config import (
    load_config, apply_config_defaults,
    get_scales_from_config, get_attention_answers_from_config,
)


def _extract_config_path(argv: list) -> Optional[str]:
    """Quick argv scan to find --config before full argparse run."""
    for i, arg in enumerate(argv):
        if arg == "--config" and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith("--config="):
            return arg[len("--config="):]
    return None


def _load_survey(path: str):
    file_path = Path(path)
    if not file_path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    content = file_path.read_text(encoding="utf-8-sig")
    return parse_csv(content), file_path.name


def _load_scales(path: str) -> dict:
    scales_path = Path(path)
    if not scales_path.exists():
        print(f"Error: scales file not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(scales_path, encoding="utf-8") as f:
        return json.load(f)


def _build_thresholds(args) -> QualityThresholds:
    return QualityThresholds(
        fast_response_seconds=args.threshold,
        missing_column_warn=args.missing_warn,
        missing_column_flag=args.missing_flag,
        missing_respondent_flag=args.missing_respondent,
        outlier_z_threshold=args.outlier_z,
        low_item_total_r=args.low_r,
    )


def cmd_inspect(args):
    """Run quality inspection and print a report."""
    survey, name = _load_survey(args.file)
    thresholds = _build_thresholds(args)
    config = getattr(args, "_config", {})

    # Scales: CLI flag > config [scales] > auto-detect
    if args.scales:
        scale_groups = _load_scales(args.scales)
    else:
        scale_groups = get_scales_from_config(config)

    # Attention answers: CLI flag > config [attention]
    if args.attention_answers:
        aa_path = Path(args.attention_answers)
        if not aa_path.exists():
            print(f"Error: attention answers file not found: {args.attention_answers}", file=sys.stderr)
            sys.exit(1)
        with open(aa_path, encoding="utf-8") as f:
            attention_answers = json.load(f)
    else:
        attention_answers = get_attention_answers_from_config(config)

    quality = compute_quality(
        survey,
        scale_groups=scale_groups,
        timing_threshold=args.threshold,
        thresholds=thresholds,
        detect_conditions=not args.no_conditions,
        expected_attention_answers=attention_answers,
    )

    text = generate_text_report(quality, survey, source_name=name)
    print(text)

    if args.html:
        html_path = Path(args.html)
        html_content = generate_html_report(quality, survey, source_name=name)
        html_path.write_text(html_content, encoding="utf-8")
        print(f"HTML report written to: {args.html}", file=sys.stderr)

    if args.excel:
        try:
            from src.excel_export import export_excel
            excel_bytes = export_excel(
                quality, survey, source_name=name,
                attention_results=quality.attention_results,
                careless_index=quality.careless_index,
            )
            Path(args.excel).write_bytes(excel_bytes)
            print(f"Excel report written to: {args.excel}", file=sys.stderr)
        except ImportError:
            print("Error: openpyxl is required for Excel export. Run: pip install openpyxl", file=sys.stderr)
            sys.exit(1)


def cmd_clean(args):
    """Export a cleaned CSV with QI_Flags column."""
    survey, name = _load_survey(args.file)
    thresholds = _build_thresholds(args)
    config = getattr(args, "_config", {})

    if args.scales:
        scale_groups = _load_scales(args.scales)
    else:
        scale_groups = get_scales_from_config(config)

    quality = compute_quality(
        survey,
        scale_groups=scale_groups,
        timing_threshold=args.threshold,
        thresholds=thresholds,
    )

    cleaned = export_clean_csv(
        survey,
        quality,
        exclude_incomplete=not args.keep_incomplete,
        exclude_fast=not args.keep_fast,
        exclude_straight_liners=not args.keep_straight_liners,
        exclude_high_missing=args.exclude_high_missing,
    )

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(cleaned, encoding="utf-8")
        print(f"Clean CSV written to: {args.output}", file=sys.stderr)
    else:
        print(cleaned)


def _add_shared_args(p):
    """Add threshold flags shared by inspect and clean subcommands."""
    p.add_argument("--threshold", type=int, default=60, metavar="SECONDS",
                   help="Fast-response threshold in seconds (default: 60)")
    p.add_argument("--scales", metavar="SCALES.json",
                   help="JSON file mapping scale names to column lists")
    p.add_argument("--missing-warn", type=float, default=0.05, metavar="RATE",
                   help="Column missing rate to warn at (default: 0.05)")
    p.add_argument("--missing-flag", type=float, default=0.20, metavar="RATE",
                   help="Column missing rate to flag seriously (default: 0.20)")
    p.add_argument("--missing-respondent", type=float, default=0.20, metavar="RATE",
                   help="Per-respondent missing item rate to flag (default: 0.20)")
    p.add_argument("--outlier-z", type=float, default=3.0, metavar="THRESHOLD",
                   help="Z-score threshold for outlier detection (default: 3.0)")
    p.add_argument("--low-r", type=float, default=0.20, metavar="R",
                   help="Item-total correlation below which items are flagged (default: 0.20)")


def main():
    # Load config early so we can set argparse defaults before the full parse
    config_path = _extract_config_path(sys.argv[1:])
    try:
        config = load_config(config_path)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(
        prog="qi",
        description="Qualtrics Survey Data Inspector — quality-check a CSV export",
    )
    parser.add_argument(
        "--config", metavar="qi.toml",
        help="Config file path (default: qi.toml in current directory if present)",
    )
    sub = parser.add_subparsers(dest="command")

    # inspect subcommand
    p_inspect = sub.add_parser("inspect", help="Print a quality report")
    p_inspect.add_argument("file", help="Path to Qualtrics CSV export")
    p_inspect.add_argument("--html", metavar="OUTPUT.html",
                           help="Also write a self-contained HTML report")
    p_inspect.add_argument("--no-conditions", action="store_true",
                           help="Disable automatic condition/group detection")
    p_inspect.add_argument("--attention-answers", metavar="ANSWERS.json",
                           help="JSON file mapping column names to expected answer values")
    p_inspect.add_argument("--excel", metavar="OUTPUT.xlsx",
                           help="Also write an Excel workbook (requires openpyxl)")
    _add_shared_args(p_inspect)
    p_inspect.set_defaults(func=cmd_inspect)

    # clean subcommand
    p_clean = sub.add_parser("clean", help="Export a cleaned CSV")
    p_clean.add_argument("file", help="Path to Qualtrics CSV export")
    p_clean.add_argument("--output", "-o", metavar="OUTPUT.csv",
                         help="Output path (default: stdout)")
    p_clean.add_argument("--keep-incomplete", action="store_true",
                         help="Do not remove incomplete responses")
    p_clean.add_argument("--keep-fast", action="store_true",
                         help="Do not remove fast responses")
    p_clean.add_argument("--keep-straight-liners", action="store_true",
                         help="Do not remove straight-liners")
    p_clean.add_argument("--exclude-high-missing", action="store_true",
                         help="Also remove respondents with > threshold missing items")
    _add_shared_args(p_clean)
    p_clean.set_defaults(func=cmd_clean)

    # Apply config as defaults (CLI flags will still override)
    apply_config_defaults(p_inspect, config)
    apply_config_defaults(p_clean, config)

    args = parser.parse_args()
    args._config = config  # make available to cmd_* handlers

    if not args.command:
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
