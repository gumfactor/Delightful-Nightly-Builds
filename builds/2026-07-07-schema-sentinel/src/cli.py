"""Argparse-based CLI: `diff` and `history` subcommands."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional, Set

import ai_summary
import diff as diff_mod
import git_history
import infer
import report_html

ANSI = {
    "breaking": "\033[91m",
    "risky": "\033[93m",
    "safe": "\033[92m",
    "reset": "\033[0m",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schema-sentinel",
        description="Detect and classify structural drift in JSON/JSONL/CSV data files.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--ignore-fields", default="", help="Comma-separated field paths to exclude from the report"
    )
    common.add_argument(
        "--json", action="store_true", help="Emit machine-readable JSON instead of a colored terminal report"
    )
    common.add_argument("--html", metavar="PATH", help="Write a self-contained dark-mode HTML report to PATH")
    common.add_argument(
        "--fail-on",
        choices=["breaking", "risky"],
        default="breaking",
        help="Exit non-zero if a change at or above this severity is found",
    )
    common.add_argument(
        "--ai-summary",
        action="store_true",
        help="Generate a plain-English migration summary (uses ANTHROPIC_API_KEY if set, otherwise a deterministic fallback)",
    )

    diff_parser = subparsers.add_parser("diff", parents=[common], help="Compare two data files directly")
    diff_parser.add_argument("old_file")
    diff_parser.add_argument("new_file")

    history_parser = subparsers.add_parser("history", parents=[common], help="Walk a tracked file's git history")
    history_parser.add_argument("path")
    history_parser.add_argument("--repo", default=".", help="Path to the git repository (default: current directory)")
    history_parser.add_argument("--limit", type=int, default=None, help="Limit to the N most recent revisions")

    return parser


def _parse_ignore_fields(raw: str) -> Set[str]:
    return {field.strip() for field in raw.split(",") if field.strip()}


def _run_diff(args: argparse.Namespace, ignore_fields: Set[str]) -> dict:
    old_records = infer.load_records(args.old_file)
    new_records = infer.load_records(args.new_file)
    old_schema = infer.infer_schema(old_records)
    new_schema = infer.infer_schema(new_records)
    entries = diff_mod.diff_schemas(old_schema, new_schema, ignore_fields)
    summary = ai_summary.generate_summary(entries) if args.ai_summary else None
    return {
        "mode": "diff",
        "old_label": args.old_file,
        "new_label": args.new_file,
        "entries": entries,
        "overall_severity": diff_mod.overall_severity(entries),
        "ai_summary": summary,
    }


def _run_history(args: argparse.Namespace, ignore_fields: Set[str]) -> dict:
    if not git_history.is_git_repo(args.repo):
        raise git_history.GitHistoryError(f"'{args.repo}' is not a git repository")

    revisions = git_history.list_revisions(args.repo, args.path, args.limit)
    if len(revisions) < 2:
        return {
            "mode": "history",
            "path": args.path,
            "timeline": [],
            "overall_severity": None,
            "ai_summary": None,
            "note": "Fewer than 2 revisions found for this path; nothing to diff.",
        }

    timeline = []
    all_entries: List[dict] = []
    prev_content = git_history.read_file_at_revision(args.repo, revisions[0]["sha"], args.path)
    prev_schema = infer.infer_schema(infer.load_records_from_text(prev_content, args.path))

    for rev in revisions[1:]:
        content = git_history.read_file_at_revision(args.repo, rev["sha"], args.path)
        schema = infer.infer_schema(infer.load_records_from_text(content, args.path))
        entries = diff_mod.diff_schemas(prev_schema, schema, ignore_fields)
        timeline.append({"sha": rev["sha"][:8], "date": rev["date"], "entries": entries})
        all_entries.extend(entries)
        prev_schema = schema

    summary = ai_summary.generate_summary(all_entries) if args.ai_summary else None
    return {
        "mode": "history",
        "path": args.path,
        "timeline": timeline,
        "overall_severity": diff_mod.overall_severity(all_entries),
        "ai_summary": summary,
    }


def _colorize(severity: str, text: str) -> str:
    return f"{ANSI[severity]}{text}{ANSI['reset']}"


def _print_entries(entries: List[dict]) -> None:
    if not entries:
        print("  No structural changes detected.")
        return
    for entry in entries:
        label = _colorize(entry["severity"], f"[{entry['severity'].upper()}]")
        print(f"  {label} {entry['field']}: {entry['detail']}")


def _print_terminal(report: dict) -> None:
    if report["mode"] == "diff":
        print(f"Schema Sentinel — {report['old_label']} -> {report['new_label']}")
        _print_entries(report["entries"])
    else:
        print(f"Schema Sentinel — history of {report['path']}")
        if not report["timeline"]:
            print(report.get("note", "No revisions to compare."))
        for rev in report["timeline"]:
            print(f"\n{rev['sha']} ({rev['date']})")
            _print_entries(rev["entries"])
    if report.get("ai_summary"):
        print("\nMigration Summary:")
        print(report["ai_summary"])


def _emit(report: dict, args: argparse.Namespace) -> None:
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_terminal(report)
    if args.html:
        html_text = report_html.render_html(report)
        with open(args.html, "w", encoding="utf-8") as handle:
            handle.write(html_text)
        print(f"HTML report written to {args.html}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    ignore_fields = _parse_ignore_fields(args.ignore_fields)

    try:
        if args.command == "diff":
            report = _run_diff(args, ignore_fields)
        else:
            report = _run_history(args, ignore_fields)
    except (infer.SchemaInferenceError, git_history.GitHistoryError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    _emit(report, args)

    if report["mode"] == "diff":
        entries = report["entries"]
    else:
        entries = [entry for rev in report["timeline"] for entry in rev["entries"]]

    if diff_mod.exceeds_threshold(entries, args.fail_on):
        return 1
    return 0
