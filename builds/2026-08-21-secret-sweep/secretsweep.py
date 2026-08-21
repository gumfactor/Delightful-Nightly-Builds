#!/usr/bin/env python3
"""Secret Sweep — find committed secrets in your own local git repos.

Usage:
    python3 secretsweep.py scan [repo ...] [--ai-review]
    python3 secretsweep.py history [repo ...] [--ai-review] [--max-commits N]
    python3 secretsweep.py list [--repo PATH ...] [--severity critical|high|all] [--status new|acknowledged|all]
    python3 secretsweep.py report [--repo PATH ...] --format json|html [--output PATH]
    python3 secretsweep.py ack FINDING_ID

Run `python3 secretsweep.py --help` for the full option list.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import db, git_ops, report, scanner  # noqa: E402

DEFAULT_DB_PATH = str(Path.home() / ".secretsweep" / "findings.db")


def _resolve_repo_paths(raw_paths: list[str] | None) -> list[str]:
    paths = raw_paths or ["."]
    resolved = []
    for p in paths:
        abs_path = str(Path(p).resolve())
        if not git_ops.is_git_repo(abs_path):
            print(f"warning: '{p}' is not a git repository — skipping", file=sys.stderr)
            continue
        resolved.append(abs_path)
    return resolved


def _persist(conn, findings: list[dict]) -> None:
    for finding in findings:
        db.upsert_finding(conn, finding)


def cmd_scan(args: argparse.Namespace) -> int:
    conn = db.connect(args.db)
    repo_paths = _resolve_repo_paths(args.repos)
    if not repo_paths:
        print("No valid git repositories to scan.", file=sys.stderr)
        return 1
    all_findings: list[dict] = []
    for repo_path in repo_paths:
        found = scanner.scan_working_tree(repo_path)
        if args.ai_review:
            scanner.apply_ai_review(found, api_key=args.api_key)
        all_findings.extend(found)
        _persist(conn, found)
    print(f"Scanned {len(repo_paths)} repo(s) (working tree). {len(all_findings)} finding(s).")
    print(_terminal_view(conn, [r for r in repo_paths]))
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    conn = db.connect(args.db)
    repo_paths = _resolve_repo_paths(args.repos)
    if not repo_paths:
        print("No valid git repositories to scan.", file=sys.stderr)
        return 1
    all_findings: list[dict] = []
    for repo_path in repo_paths:
        found = scanner.scan_history(repo_path, max_commits=args.max_commits)
        if args.ai_review:
            scanner.apply_ai_review(found, api_key=args.api_key)
        all_findings.extend(found)
        _persist(conn, found)
    print(f"Scanned {len(repo_paths)} repo(s) (history). {len(all_findings)} finding(s).")
    print(_terminal_view(conn, repo_paths))
    return 0


def _terminal_view(conn, repo_paths: list[str] | None) -> str:
    rows: list[dict] = []
    if repo_paths:
        for repo_path in repo_paths:
            rows.extend(report.row_to_dict(r) for r in db.get_findings(conn, repo_path=repo_path))
    else:
        rows.extend(report.row_to_dict(r) for r in db.get_findings(conn))
    return report.render_terminal(rows)


def cmd_list(args: argparse.Namespace) -> int:
    conn = db.connect(args.db)
    repo_paths = [str(Path(p).resolve()) for p in args.repo] if args.repo else None
    rows: list[dict] = []
    if repo_paths:
        for repo_path in repo_paths:
            rows.extend(report.row_to_dict(r) for r in db.get_findings(conn, repo_path=repo_path))
    else:
        rows.extend(report.row_to_dict(r) for r in db.get_findings(conn))

    if args.severity != "all":
        rows = [r for r in rows if r["severity"] == args.severity]
    if args.status != "all":
        rows = [r for r in rows if r["status"] == args.status]

    print(report.render_terminal(rows))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    conn = db.connect(args.db)
    repo_paths = [str(Path(p).resolve()) for p in args.repo] if args.repo else None
    rows: list[dict] = []
    if repo_paths:
        for repo_path in repo_paths:
            rows.extend(report.row_to_dict(r) for r in db.get_findings(conn, repo_path=repo_path))
    else:
        rows.extend(report.row_to_dict(r) for r in db.get_findings(conn))

    if args.format == "json":
        output = report.render_json(rows)
    else:
        output = report.render_html(rows, db.utc_now_iso())

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Wrote {args.format} report to {args.output}")
    else:
        print(output)
    return 0


def cmd_ack(args: argparse.Namespace) -> int:
    conn = db.connect(args.db)
    ok = db.ack_finding(conn, args.finding_id)
    if ok:
        print(f"Acknowledged finding #{args.finding_id}.")
        return 0
    print(f"No finding with id #{args.finding_id}.", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="secretsweep", description="Find committed secrets in your local git repos.")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite findings database path")
    parser.add_argument("--api-key", default=None, help="Anthropic API key (defaults to $ANTHROPIC_API_KEY)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_p = subparsers.add_parser("scan", help="Scan the current working tree of one or more repos")
    scan_p.add_argument("repos", nargs="*", help="Repo path(s); defaults to the current directory")
    scan_p.add_argument("--ai-review", action="store_true", help="Get a Claude Haiku second opinion on each finding")
    scan_p.set_defaults(func=cmd_scan)

    history_p = subparsers.add_parser("history", help="Scan full commit history of one or more repos")
    history_p.add_argument("repos", nargs="*", help="Repo path(s); defaults to the current directory")
    history_p.add_argument("--ai-review", action="store_true", help="Get a Claude Haiku second opinion on each finding")
    history_p.add_argument("--max-commits", type=int, default=None, help="Cap the number of commits walked")
    history_p.set_defaults(func=cmd_history)

    list_p = subparsers.add_parser("list", help="Print stored findings to the terminal")
    list_p.add_argument("--repo", action="append", help="Filter to this repo path (repeatable)")
    list_p.add_argument("--severity", choices=["critical", "high", "all"], default="all")
    list_p.add_argument("--status", choices=["new", "acknowledged", "all"], default="all")
    list_p.set_defaults(func=cmd_list)

    report_p = subparsers.add_parser("report", help="Render a JSON or HTML report from stored findings")
    report_p.add_argument("--repo", action="append", help="Filter to this repo path (repeatable)")
    report_p.add_argument("--format", choices=["json", "html"], default="html")
    report_p.add_argument("--output", default=None, help="Write to this file instead of stdout")
    report_p.set_defaults(func=cmd_report)

    ack_p = subparsers.add_parser("ack", help="Acknowledge a finding so it stops counting as 'new'")
    ack_p.add_argument("finding_id", type=int)
    ack_p.set_defaults(func=cmd_ack)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
