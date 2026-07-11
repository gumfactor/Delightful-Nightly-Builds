"""TrialScope CLI — Behavioral & Reaction-Time Data QC Explorer.

Usage:
    python src/trialscope.py <input.csv> --out-dir <output_dir> [options]
"""
from __future__ import annotations

import argparse
import os
import sys

from ai_summary import generate_methods_paragraph, _deterministic_paragraph
from parsing import ColumnResolutionError, parse_csv
from qc import QCConfig, flag_trials, learning_curve, recommend_exclusions, summarize_conditions, summarize_subjects
from report import render_report, write_cleaned_csv, write_exclusions_csv


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compute QC diagnostics and an interactive report for trial-level behavioral data."
    )
    parser.add_argument("input_csv", help="Path to a trial-level CSV file (one row per trial).")
    parser.add_argument("--out-dir", default="trialscope_output", help="Directory to write report/CSV output.")

    for role in ("subject", "condition", "block", "trial", "rt", "accuracy"):
        parser.add_argument(f"--{role}-col", default=None, help=f"Explicit column name for the {role} role.")

    parser.add_argument("--rt-floor-ms", type=float, default=150.0, help="Anticipatory-response RT floor in ms.")
    parser.add_argument("--rt-ceiling-ms", type=float, default=5000.0, help="Absolute RT outlier ceiling in ms.")
    parser.add_argument("--sd-outlier", type=float, default=3.0, help="Subject-level SD multiplier for outliers.")
    parser.add_argument("--chance-rate", type=float, default=0.5, help="Chance performance rate (0-1).")
    parser.add_argument("--chance-alpha", type=float, default=0.05, help="Alpha for the chance-level binomial test.")
    parser.add_argument("--min-completion", type=float, default=0.8, help="Minimum fraction of expected trials.")
    parser.add_argument("--expected-trials", type=int, default=None, help="Expected trial count per subject.")
    parser.add_argument("--exclude-threshold", type=int, default=2, help="Flag count that triggers exclusion.")
    parser.add_argument("--no-ai", action="store_true", help="Skip the Anthropic API call; always use the template.")

    return parser


def run(argv: list[str]) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    overrides = {
        role: getattr(args, f"{role}_col")
        for role in ("subject", "condition", "block", "trial", "rt", "accuracy")
    }

    try:
        parse_result = parse_csv(args.input_csv, overrides)
    except ColumnResolutionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(f"Error: input file not found: {args.input_csv}", file=sys.stderr)
        return 1

    config = QCConfig(
        rt_floor_ms=args.rt_floor_ms,
        rt_ceiling_ms=args.rt_ceiling_ms,
        sd_outlier=args.sd_outlier,
        chance_rate=args.chance_rate,
        chance_alpha=args.chance_alpha,
        min_completion=args.min_completion,
        expected_trials=args.expected_trials,
        exclude_threshold=args.exclude_threshold,
    )

    trials = parse_result.trials
    trial_flags = flag_trials(trials, config)
    subjects = summarize_subjects(trials, trial_flags, config)
    conditions = summarize_conditions(trials)
    excluded = recommend_exclusions(subjects, config)
    curves = learning_curve(trials)

    if args.no_ai:
        methods_paragraph = _deterministic_paragraph(subjects, conditions, excluded, config)
        methods_source = "template"
    else:
        methods_paragraph, methods_source = generate_methods_paragraph(subjects, conditions, excluded, config)

    os.makedirs(args.out_dir, exist_ok=True)

    report_html = render_report(
        subjects, conditions, trials, excluded, methods_paragraph, methods_source, config, curves,
        parse_result.warnings,
    )
    report_path = os.path.join(args.out_dir, "report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_html)

    write_cleaned_csv(os.path.join(args.out_dir, "cleaned_data.csv"), trials, trial_flags)
    write_exclusions_csv(os.path.join(args.out_dir, "exclusions.csv"), excluded)

    print(f"Report written to {report_path}")
    print(f"{len(subjects)} subjects, {len(excluded)} recommended exclusions, {len(trials)} trials.")
    if parse_result.warnings:
        print(f"Warning: {parse_result.warnings} malformed cell(s) were coerced during parsing.")

    return 0


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
