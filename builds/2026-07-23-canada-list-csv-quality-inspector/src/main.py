"""CLI entry point for the Canada List CSV Quality Inspector.

Usage (run from the build folder root, so the `src` package resolves):
    python -m src.main <input.csv> [--schema config.json] [--out-dir DIR] [--no-ai]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from src import ai_enrichment
from src.duplicates import find_all_duplicate_clusters
from src.qc_engine import (
    Flag,
    build_row_records,
    check_required_columns_present,
    decode_csv_bytes,
    parse_csv,
)
from src.report_html import render_html_report
from src.schema import Schema

SEVERITY_RANK = {"error": 2, "warning": 1, "info": 0}


def run_qc(csv_bytes: bytes, schema: Schema, use_ai: bool = True) -> dict:
    """Run the full QC pipeline over raw CSV bytes and return the report dict
    used by every output format (terminal, JSON, HTML, cleaned CSV).
    """
    decode_result = decode_csv_bytes(csv_bytes)
    header, rows_with_flags, structural_flags = parse_csv(decode_result.text)

    file_level_flags = list(decode_result.file_flags) + list(structural_flags)

    if header:
        file_level_flags += check_required_columns_present(header, schema)

    row_records = build_row_records(rows_with_flags, header, schema) if header else []

    duplicate_clusters = find_all_duplicate_clusters(row_records, header) if header else []
    _apply_duplicate_flags(row_records, duplicate_clusters)

    if use_ai and ai_enrichment.is_ai_available():
        _enrich_clusters_with_ai(duplicate_clusters, row_records, header)
        _enrich_unmapped_ownership_status(row_records, schema)

    total_rows = len(row_records)
    error_rows = sum(1 for r in row_records if r.recommended_action == "drop")
    warning_rows = sum(1 for r in row_records if r.recommended_action == "review")
    clean_rows = total_rows - error_rows - warning_rows

    summary = {
        "total_rows": total_rows,
        "error_rows": error_rows,
        "warning_rows": warning_rows,
        "clean_rows": clean_rows,
        "duplicate_cluster_count": len(duplicate_clusters),
        "file_level_flags": [f.to_dict() for f in file_level_flags],
    }

    return {
        "summary": summary,
        "header": header,
        "rows": [r.to_dict() for r in row_records],
        "duplicate_clusters": [c.to_dict() for c in duplicate_clusters],
        "generated_with_ai": use_ai and ai_enrichment.is_ai_available(),
    }


def _apply_duplicate_flags(row_records, duplicate_clusters) -> None:
    """Fold duplicate-cluster membership into each row's own QC_Flags so the
    cleaned CSV and Recommended_Action reflect duplicates, not just the
    separate duplicate_clusters section of the report. Duplicates are
    "warning" severity (review), never auto-"error" (drop) — a human should
    confirm before removing a row, since apparent duplicates can turn out to
    be legitimate (e.g. two locations of the same franchise).
    """
    rows_by_index = {r.row_index: r for r in row_records}
    for cluster in duplicate_clusters:
        code = "exact_duplicate" if cluster.match_basis == "exact_row" else "near_duplicate"
        for index in cluster.row_indices:
            record = rows_by_index.get(index)
            if record is None:
                continue
            others = [i for i in cluster.row_indices if i != index]
            record.flags.append(
                Flag(
                    code=code,
                    severity="warning",
                    message=f"Possible duplicate of row(s) {others} (cluster {cluster.cluster_id}).",
                )
            )


def _enrich_clusters_with_ai(duplicate_clusters, row_records, header) -> None:
    name_col = next((c for c in header if c.strip().lower() == "business_name"), None)
    if name_col is None:
        return
    rows_by_index = {r.row_index: r for r in row_records}
    for cluster in duplicate_clusters:
        if cluster.match_basis == "exact_row":
            continue  # exact duplicates need no AI judgment call
        names = [
            rows_by_index[i].raw_fields.get(name_col, "")
            for i in cluster.row_indices
            if i in rows_by_index
        ]
        confirmed, reasoning = ai_enrichment.confirm_duplicate_cluster(names)
        cluster.ai_confirmed = confirmed
        cluster.ai_reasoning = reasoning


def _enrich_unmapped_ownership_status(row_records, schema: Schema) -> None:
    for record in row_records:
        for flag in record.flags:
            if flag.code == "unmapped_ownership_status":
                value = record.raw_fields.get(flag.column, "")
                suggestion, reasoning = ai_enrichment.suggest_ownership_status_mapping(
                    value, schema.ownership_status_values
                )
                if suggestion:
                    flag.message += f" AI suggests: '{suggestion}' ({reasoning})"


def write_cleaned_csv(report: dict, output_path: Path) -> None:
    header = report["header"]
    fieldnames = list(header) + ["QC_Flags", "Recommended_Action"]
    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in report["rows"]:
            out_row = dict(row["fields"])
            out_row["QC_Flags"] = "; ".join(f"{f['severity']}:{f['code']}" for f in row["flags"]) or ""
            out_row["Recommended_Action"] = row["recommended_action"]
            writer.writerow(out_row)


def write_json_report(report: dict, output_path: Path) -> None:
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def write_html_report(report: dict, output_path: Path, source_filename: str) -> None:
    output_path.write_text(render_html_report(report, source_filename), encoding="utf-8")


def print_terminal_summary(report: dict, use_color: bool = True) -> None:
    summary = report["summary"]

    def colorize(text: str, code: str) -> str:
        if not use_color:
            return text
        return f"\033[{code}m{text}\033[0m"

    lines = [
        "Canada List CSV Quality Inspector",
        "=" * 40,
        f"Total rows:        {summary['total_rows']}",
        colorize(f"Errors (drop):      {summary['error_rows']}", "91"),
        colorize(f"Warnings (review):  {summary['warning_rows']}", "93"),
        colorize(f"Clean rows (keep):  {summary['clean_rows']}", "92"),
        f"Duplicate clusters: {summary['duplicate_cluster_count']}",
    ]
    if summary["file_level_flags"]:
        lines.append("")
        lines.append("File-level issues:")
        for flag in summary["file_level_flags"]:
            lines.append(f"  [{flag['severity']}] {flag['code']}: {flag['message']}")
    print("\n".join(lines))


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a business-directory CSV before ingestion into The Canada List."
    )
    parser.add_argument("input_csv", help="Path to the CSV file to inspect.")
    parser.add_argument(
        "--schema", help="Path to an optional JSON file overriding the default schema."
    )
    parser.add_argument(
        "--out-dir",
        default="canlist_qc_output",
        help="Directory to write the report and cleaned CSV to (default: ./canlist_qc_output).",
    )
    parser.add_argument(
        "--no-ai", action="store_true", help="Disable Claude enrichment even if a key is set."
    )
    return parser


def main(argv: list | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    input_path = Path(args.input_csv)
    if not input_path.is_file():
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        return 1

    schema = Schema.default()
    if args.schema:
        schema_path = Path(args.schema)
        if not schema_path.is_file():
            print(f"Error: schema file not found: {schema_path}", file=sys.stderr)
            return 1
        schema = Schema.from_dict(json.loads(schema_path.read_text(encoding="utf-8")))

    csv_bytes = input_path.read_bytes()
    report = run_qc(csv_bytes, schema, use_ai=not args.no_ai)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    write_cleaned_csv(report, out_dir / "cleaned.csv")
    write_json_report(report, out_dir / "report.json")
    write_html_report(report, out_dir / "report.html", input_path.name)

    print_terminal_summary(report, use_color=sys.stdout.isatty())
    print(f"\nReports written to: {out_dir}/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
