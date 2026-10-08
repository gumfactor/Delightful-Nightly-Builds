"""lookalike command line interface."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import demo, report
from .ai import AIError, adjudicate
from .cluster import DecisionsError, analyze, load_decisions
from .schema import IntakeError, read_records


def run_pipeline(input_csv: Path, out_dir: Path, decisions_path: Path | None = None, existing_csv: Path | None = None,
                 use_ai: bool = False, transport=None, out=None) -> int:
    out = out or sys.stdout
    records, _headers, warnings = read_records(input_csv, "batch")
    if existing_csv is not None:
        existing, _h, more = read_records(existing_csv, "existing")
        records = existing + records
        warnings += more
    if not records:
        raise IntakeError("no usable rows found in the input")
    decisions = load_decisions(decisions_path)
    analysis = analyze(records, decisions)
    ai_results = None
    if use_ai:
        if transport is None and not os.environ.get("ANTHROPIC_API_KEY"):
            warnings.append("--ai requested but ANTHROPIC_API_KEY is not set; skipping AI suggestions")
        elif analysis.review_pairs:
            try:
                ai_results = adjudicate(analysis.review_pairs, analysis.by_id, transport)
            except AIError as exc:
                warnings.append(str(exc))
    out_dir.mkdir(parents=True, exist_ok=True)
    report.write_csv(out_dir / "deduped.csv", report.deduped_rows(analysis))
    cluster_rows = report.cluster_rows(analysis) or [{"row_id": "", "cluster_id": "", "status": "", "name": "", "flags": ""}]
    report.write_csv(out_dir / "clusters.csv", cluster_rows)
    report.write_json(out_dir / "merge_report.json", report.report_dict(analysis, ai_results))
    (out_dir / "review.html").write_text(report.render_html(analysis, ai_results), encoding="utf-8")
    summary = report.report_dict(analysis, ai_results)["summary"]
    for warning in warnings:
        print(f"warning: {warning}", file=out)
    print(f"{summary['input_rows']} rows in -> {summary['output_rows']} rows out; "
          f"{summary['merged_clusters']} merged clusters, {summary['needs_review_clusters']} flagged for review, "
          f"{summary['review_pairs']} ambiguous pairs, {summary['branch_pairs']} branch pairs kept separate", file=out)
    print(f"wrote {out_dir}/deduped.csv, clusters.csv, merge_report.json, review.html", file=out)
    return 0


def cmd_scan(args, out) -> int:
    return run_pipeline(Path(args.input), Path(args.out), Path(args.decisions) if args.decisions else None,
                        Path(args.existing) if args.existing else None, args.ai, out=out)


def cmd_demo(args, out) -> int:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    sample = out_dir / "sample_businesses.csv"
    sample.write_text(demo.sample_csv(), encoding="utf-8")
    print(f"wrote fictional sample data to {sample}", file=out)
    return run_pipeline(sample, out_dir, out=out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lookalike", description="Find and merge duplicate business records in a CSV.")
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="detect duplicates in a CSV and write the outputs")
    scan.add_argument("input", help="CSV of businesses")
    scan.add_argument("--out", default="out", help="output directory (default: out)")
    scan.add_argument("--decisions", help="decisions.json exported from review.html")
    scan.add_argument("--existing", help="CSV export of the existing directory to match the batch against")
    scan.add_argument("--ai", action="store_true", help="advisory Claude verdicts for ambiguous pairs (needs ANTHROPIC_API_KEY)")
    scan.set_defaults(func=cmd_scan)
    demo_cmd = sub.add_parser("demo", help="run on built-in fictional sample data")
    demo_cmd.add_argument("--out", default="out-demo")
    demo_cmd.set_defaults(func=cmd_demo)
    return parser


def main(argv: list[str] | None = None, out=None) -> int:
    out = out or sys.stdout
    args = build_parser().parse_args(argv)
    try:
        return args.func(args, out)
    except (IntakeError, DecisionsError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
