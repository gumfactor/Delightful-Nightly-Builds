"""Command-line entry points: sync, report, history."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

from . import ai_summary, analysis, github_client, report as report_module, storage

DEFAULT_DB = "landing_pattern.db"


def cmd_sync(args: argparse.Namespace) -> int:
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: no GitHub token. Pass --token or set GITHUB_TOKEN.", file=sys.stderr)
        return 1

    try:
        prs = github_client.fetch_repo_prs_full(args.repo, token)
    except github_client.GitHubAPIError as exc:
        print(f"Error fetching PRs: {exc}", file=sys.stderr)
        return 1

    computed = analysis.build_report(prs, args.repo, analysis.utcnow())
    conn = storage.connect(args.db)
    try:
        run_id = storage.save_snapshot(conn, computed)
    finally:
        conn.close()

    print(f"Synced {len(prs)} open PR(s) for {args.repo} — snapshot #{run_id}")
    return 0


def _load_report(args: argparse.Namespace) -> dict[str, Any] | None:
    conn = storage.connect(args.db)
    try:
        if getattr(args, "run_id", None) is not None:
            return storage.snapshot_by_id(conn, args.run_id)
        return storage.latest_snapshot(conn, args.repo)
    finally:
        conn.close()


def cmd_report(args: argparse.Namespace) -> int:
    computed = _load_report(args)
    if computed is None:
        print(
            f"Error: no snapshot found for {args.repo}. Run 'sync --repo {args.repo}' first.",
            file=sys.stderr,
        )
        return 1

    ai_notes: dict[int, str] = {}
    if args.ai:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        for pr in computed["blocked"]:
            ai_notes[pr["number"]] = ai_summary.summarize_blocked_pr(pr, api_key)

    if args.format == "json":
        output = report_module.render_json(computed)
    elif args.format == "html":
        output = report_module.render_html(computed, ai_notes)
    else:
        output = report_module.render_text(computed, ai_notes)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(output)
        print(f"Wrote {args.format} report to {args.output}")
    else:
        print(output)
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    conn = storage.connect(args.db)
    try:
        entries = storage.history_for_pr(conn, args.repo, args.pr)
    finally:
        conn.close()

    if not entries:
        print(f"No snapshot history for #{args.pr} on {args.repo}.")
        return 0

    for entry in entries:
        print(f"{entry['synced_at']}  {entry['label']:<20}  {entry['age_days']}d old")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="landing-pattern", description="PR merge-order and conflict-risk planner"
    )
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to the snapshot SQLite database")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Fetch open PRs and store a snapshot")
    sync_parser.add_argument("--repo", required=True, help="owner/name")
    sync_parser.add_argument("--token", default=None, help="GitHub token (default: GITHUB_TOKEN)")
    sync_parser.set_defaults(func=cmd_sync)

    report_parser = subparsers.add_parser("report", help="Render the latest snapshot")
    report_parser.add_argument("--repo", required=True, help="owner/name")
    report_parser.add_argument(
        "--format", choices=["text", "json", "html"], default="text", help="Output format"
    )
    report_parser.add_argument("--output", default=None, help="Write to this file instead of stdout")
    report_parser.add_argument(
        "--ai", action="store_true", help="Add Claude-generated notes to blocked PRs"
    )
    report_parser.add_argument(
        "--run-id", type=int, default=None, help="Render a specific snapshot instead of the latest"
    )
    report_parser.set_defaults(func=cmd_report)

    history_parser = subparsers.add_parser("history", help="Show a PR's readiness trend")
    history_parser.add_argument("--repo", required=True, help="owner/name")
    history_parser.add_argument("--pr", type=int, required=True, help="PR number")
    history_parser.set_defaults(func=cmd_history)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
