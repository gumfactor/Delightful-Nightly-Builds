"""Grant Horizon CLI.

    python3 src/main.py sync
    python3 src/main.py report [--ai]

Reads topics and fiscal-year range from config.json (relative to this
build folder) unless overridden with --topics / --fy-start / --fy-end.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import briefing
import render
import storage
from reporter_client import default_http_post, fetch_all_projects

BUILD_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = BUILD_ROOT / "config.json"
DEFAULT_DB_PATH = BUILD_ROOT / "output" / "grant_horizon.db"
DEFAULT_OUTPUT_DIR = BUILD_ROOT / "output"


def load_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_args(argv: list) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="grant-horizon", description="NIH RePORTER funding-landscape tracker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="path to config.json")
    common.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="path to the SQLite database")
    common.add_argument("--topics", type=str, default=None, help="comma-separated topic override")
    common.add_argument("--fy-start", type=int, default=None, help="override fiscal_year_start")
    common.add_argument("--fy-end", type=int, default=None, help="override fiscal_year_end")

    subparsers.add_parser("sync", parents=[common], help="fetch and store the latest data")
    report_parser = subparsers.add_parser("report", parents=[common], help="render the dashboard + CSV export")
    report_parser.add_argument("--ai", action="store_true", help="generate an AI briefing per topic")
    report_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)

    args = parser.parse_args(argv)

    if args.fy_start is not None and args.fy_end is not None and args.fy_start > args.fy_end:
        raise ValueError(f"fy-start ({args.fy_start}) must not be after fy-end ({args.fy_end})")

    return args


def resolve_topics_and_years(args: argparse.Namespace) -> tuple:
    config = load_config(args.config)
    topics = args.topics.split(",") if args.topics else config["topics"]
    topics = [t.strip() for t in topics if t.strip()]
    fy_start = args.fy_start if args.fy_start is not None else config["fiscal_year_start"]
    fy_end = args.fy_end if args.fy_end is not None else config["fiscal_year_end"]
    if fy_start > fy_end:
        raise ValueError(f"fiscal_year_start ({fy_start}) must not be after fiscal_year_end ({fy_end})")
    return topics, fy_start, fy_end


def run_sync(args: argparse.Namespace) -> None:
    topics, fy_start, fy_end = resolve_topics_and_years(args)
    fiscal_years = list(range(fy_start, fy_end + 1))
    conn = storage.connect(args.db)
    total_written = 0
    for topic in topics:
        print(f"Syncing topic: {topic} (FY{fy_start}-FY{fy_end})...")
        projects = fetch_all_projects(topic, fiscal_years, default_http_post)
        written = storage.upsert_projects(conn, projects)
        seen_project_nums = {p.project_num for p in projects}
        deleted = storage.reconcile_topic(conn, topic, fiscal_years, seen_project_nums)
        total_written += written
        print(f"  {written} projects upserted.")
        if deleted:
            print(f"  {deleted} stale project(s) removed (no longer returned for this topic/fiscal-year range).")
    print(f"Sync complete. {total_written} project rows written across {len(topics)} topics.")
    conn.close()


def run_report(args: argparse.Namespace) -> None:
    topics, fy_start, fy_end = resolve_topics_and_years(args)
    conn = storage.connect(args.db)
    all_projects = storage.filtered_projects(conn, topics, fy_start, fy_end)
    conn.close()

    api_key = os.environ.get("ANTHROPIC_API_KEY") if args.ai else None
    briefings = {}
    if args.ai:
        for topic in topics:
            topic_projects = [p for p in all_projects if p.topic == topic]
            briefings[topic] = briefing.generate_briefing(topic, topic_projects, api_key=api_key)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    data = render.build_dashboard_data(all_projects, topics, fy_start, fy_end, generated_at, briefings)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    dashboard_path = args.output_dir / "dashboard.html"
    dashboard_path.write_text(render.render_dashboard(data), encoding="utf-8")

    csv_path = args.output_dir / "projects_export.csv"
    csv_path.write_text(render.render_projects_csv(all_projects), encoding="utf-8")

    print(f"Tracked projects: {len(all_projects)}")
    print(f"Total tracked funding: ${data['hero']['total_funding']:,.0f}")
    for topic_row in data["topics"]:
        print(f"  {topic_row['topic']}: {topic_row['project_count']} projects, "
              f"${topic_row['total_funding']:,.0f}")
    print(f"Dashboard written to {dashboard_path}")
    print(f"CSV export written to {csv_path}")


def main(argv: list = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    try:
        args = parse_args(argv)
        if args.command == "sync":
            run_sync(args)
        elif args.command == "report":
            run_report(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
