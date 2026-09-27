#!/usr/bin/env python3
"""Parity CLI — reconciles Teamwork.com tasks against a Coda tracking table.

Subcommands:
  sync      Fetch both sources (live, or --demo fixtures) and persist a run.
  history   Print all past sync runs.
  render    Render the dashboard HTML from the latest persisted run.
  briefing  Print a one-paragraph aggregate summary of the latest run.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from briefing import generate_briefing
from coda_client import CodaClient
from dashboard import render_dashboard
from matcher import reconcile
from store import connect, history as store_history, latest_run_items, save_run
from teamwork_client import TeamworkClient

BUILD_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BUILD_DIR / "parity.db"
FIXTURES_DIR = BUILD_DIR / "tests" / "fixtures"


class ConfigError(RuntimeError):
    pass


def load_config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.is_file():
        raise ConfigError(f"Config file not found: {config_path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Config file is not valid JSON: {exc}") from exc


def fetch_live(config: dict) -> tuple[list[dict], list[dict]]:
    domain = os.environ.get("TEAMWORK_DOMAIN")
    teamwork_key = os.environ.get("TEAMWORK_API_KEY")
    coda_key = os.environ.get("CODA_API_KEY")
    if not (domain and teamwork_key and coda_key):
        raise ConfigError(
            "Live sync requires TEAMWORK_DOMAIN, TEAMWORK_API_KEY, and CODA_API_KEY "
            "environment variables. Use --demo to run against bundled fixtures instead."
        )

    teamwork = TeamworkClient(domain=domain, api_key=teamwork_key)
    coda = CodaClient(api_key=coda_key)

    teamwork_items = teamwork.fetch_tasks_for_projects(config["teamwork"]["project_ids"])
    coda_cfg = config["coda"]
    coda_items = coda.fetch_rows(
        doc_id=coda_cfg["doc_id"],
        table_id=coda_cfg["table_id"],
        title_column=coda_cfg["title_column"],
        status_column=coda_cfg["status_column"],
        done_values=coda_cfg["done_values"],
    )
    return teamwork_items, coda_items


def fetch_demo() -> tuple[list[dict], list[dict]]:
    teamwork_items = json.loads((FIXTURES_DIR / "teamwork_tasks.json").read_text())
    coda_items = json.loads((FIXTURES_DIR / "coda_rows.json").read_text())
    return teamwork_items, coda_items


def cmd_sync(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    threshold = config.get("match_threshold", 0.5)

    if args.demo:
        teamwork_items, coda_items = fetch_demo()
    else:
        teamwork_items, coda_items = fetch_live(config)

    results = reconcile(teamwork_items, coda_items, threshold=threshold)
    conn = connect(args.db)
    run_id = save_run(conn, results)
    conn.close()

    counts: dict[str, int] = {}
    for r in results:
        counts[r.bucket] = counts.get(r.bucket, 0) + 1
    print(f"Sync run #{run_id} saved: {counts}")
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    conn = connect(args.db)
    runs = store_history(conn)
    conn.close()
    if not runs:
        print("No sync runs recorded yet. Run `parity sync` first.")
        return 0
    print(f"{'Run':<5} {'When (UTC)':<26} {'Matched':<9} {'Conflicts':<11} {'TW-only':<9} {'Coda-only':<10}")
    for run in runs:
        print(
            f"{run.id:<5} {run.run_at:<26} {run.matched_ok:<9} "
            f"{run.status_conflict:<11} {run.teamwork_only:<9} {run.coda_only:<10}"
        )
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    conn = connect(args.db)
    runs = store_history(conn)
    _, items = latest_run_items(conn)
    conn.close()
    if not runs:
        print("No sync runs recorded yet. Run `parity sync` first.")
        return 1
    html = render_dashboard(runs, items)
    Path(args.out).write_text(html)
    print(f"Dashboard written to {args.out}")
    return 0


def cmd_briefing(args: argparse.Namespace) -> int:
    conn = connect(args.db)
    runs = store_history(conn)
    conn.close()
    if not runs:
        print("No sync runs recorded yet. Run `parity sync` first.")
        return 1
    text = generate_briefing(runs[-1], runs)
    print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="parity")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to the SQLite database file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Fetch both sources and persist a run")
    sync_parser.add_argument("--config", required=True, help="Path to config.json")
    sync_parser.add_argument("--demo", action="store_true", help="Use bundled fixtures instead of live APIs")
    sync_parser.set_defaults(func=cmd_sync)

    history_parser = subparsers.add_parser("history", help="Print all past sync runs")
    history_parser.set_defaults(func=cmd_history)

    render_parser = subparsers.add_parser("render", help="Render the dashboard from the latest run")
    render_parser.add_argument("--out", default="dashboard.html", help="Output HTML path")
    render_parser.set_defaults(func=cmd_render)

    briefing_parser = subparsers.add_parser("briefing", help="Print an aggregate-only summary")
    briefing_parser.set_defaults(func=cmd_briefing)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ConfigError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
