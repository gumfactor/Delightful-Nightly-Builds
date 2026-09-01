"""Fleet Drift CLI — sync / list / render / history."""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from typing import List, Optional, Sequence

from . import ai, drift, gh_client, pkg_parser, registry, report, req_parser, store


def _today() -> str:
    return datetime.datetime.now(datetime.timezone.utc).date().isoformat()


def _sync(db_path: str, token: str, transport=None) -> int:
    conn = store.connect(db_path)
    kwargs = {"transport": transport} if transport is not None else {}
    repos = gh_client.list_owned_repos(token, **kwargs)
    if not repos:
        print("No repositories found for this token.")
        conn.close()
        return 0

    today = _today()
    latest_cache: dict = {}

    for repo in repos:
        req_text = gh_client.fetch_file_content(token, repo, "requirements.txt", **kwargs)
        if req_text:
            for entry in req_parser.parse_requirements(req_text):
                if entry["pin_kind"] == "unparseable":
                    continue
                key = ("python", entry["name"])
                if key not in latest_cache:
                    latest_cache[key] = registry.fetch_latest_pypi(entry["name"], **kwargs)
                store.upsert_snapshot(
                    conn, repo, "python", entry["name"], entry["pinned_version"],
                    entry["pin_kind"], latest_cache[key], today,
                )

        pkg_text = gh_client.fetch_file_content(token, repo, "package.json", **kwargs)
        if pkg_text:
            for entry in pkg_parser.parse_package_json(pkg_text):
                if entry["pin_kind"] == "unparseable":
                    continue
                key = ("npm", entry["name"])
                if key not in latest_cache:
                    latest_cache[key] = registry.fetch_latest_npm(entry["name"], **kwargs)
                store.upsert_snapshot(
                    conn, repo, "npm", entry["name"], entry["pinned_version"],
                    entry["pin_kind"], latest_cache[key], today,
                )

    store.commit(conn)
    print(f"Synced {len(repos)} repo(s) for {today}. Tracked {len(latest_cache)} unique dependencies.")
    conn.close()
    return 0


def _load_latest(db_path: str):
    conn = store.connect(db_path)
    date = store.latest_snapshot_date(conn)
    if date is None:
        conn.close()
        return None, []
    snapshots = store.snapshots_for_date(conn, date)
    conn.close()
    return date, snapshots


def _cmd_sync(args: argparse.Namespace) -> int:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable is required for sync.", file=sys.stderr)
        return 1
    return _sync(args.db, token)


def _cmd_list(args: argparse.Namespace) -> int:
    date, snapshots = _load_latest(args.db)
    if date is None:
        print("No sync data yet. Run 'sync' first.")
        return 0
    drift_entries = drift.compute_drift(snapshots)
    print(f"Latest sync: {date}")
    print(f"Repos with tracked dependencies: {len({s['repo'] for s in snapshots})}")
    print(f"Drifted dependencies: {len(drift_entries)}")
    for entry in drift_entries:
        versions = ", ".join(f"{repo}@{v}" for repo, v in sorted(entry["repo_versions"].items()))
        print(f"  [{entry['severity'].upper():7s}] {entry['dependency']} ({entry['ecosystem']}): {versions}")
    return 0


def _cmd_render(args: argparse.Namespace) -> int:
    date, snapshots = _load_latest(args.db)
    if date is None:
        print("No sync data yet. Run 'sync' first.")
        return 1
    drift_entries = drift.compute_drift(snapshots)
    staleness_entries = drift.compute_staleness(snapshots)
    repo_summary = drift.repo_staleness_summary(staleness_entries)

    briefing = None
    if args.ai:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        briefing = ai.build_briefing(drift_entries, repo_summary, api_key=api_key)

    repos_scanned = len({s["repo"] for s in snapshots})
    html = report.render(date, repos_scanned, drift_entries, staleness_entries, repo_summary, briefing)
    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write(html)
    print(f"Wrote dashboard to {args.output}")
    return 0


def _cmd_history(args: argparse.Namespace) -> int:
    conn = store.connect(args.db)
    rows = store.history_for_dependency(conn, args.ecosystem, args.dependency)
    conn.close()
    if args.json:
        print(json.dumps(rows, indent=2))
        return 0
    if not rows:
        print(f"No history for {args.dependency} ({args.ecosystem}).")
        return 0
    for row in rows:
        print(f"{row['fetched_at_date']}  {row['repo']:40s} {row['pinned_version']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fleet-drift", description="Cross-repo dependency drift dashboard.")
    parser.add_argument("--db", default="fleet_drift.db", help="SQLite database path (default: fleet_drift.db)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("sync", help="Fetch dependency pins from every owned GitHub repo.")

    sub.add_parser("list", help="Print the latest sync's drift findings to the terminal.")

    render_parser = sub.add_parser("render", help="Render the self-contained HTML dashboard.")
    render_parser.add_argument("--output", default="fleet_drift_report.html", help="Output HTML file path.")
    render_parser.add_argument("--ai", action="store_true", help="Include an AI-generated fix-first briefing.")

    history_parser = sub.add_parser("history", help="Show a dependency's pinned-version history over time.")
    history_parser.add_argument("ecosystem", choices=["python", "npm"])
    history_parser.add_argument("dependency")
    history_parser.add_argument("--json", action="store_true", help="Output as JSON.")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "sync":
        return _cmd_sync(args)
    if args.command == "list":
        return _cmd_list(args)
    if args.command == "render":
        return _cmd_render(args)
    if args.command == "history":
        return _cmd_history(args)
    parser.print_help()
    return 1
