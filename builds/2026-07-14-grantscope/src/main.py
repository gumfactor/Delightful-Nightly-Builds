#!/usr/bin/env python3
"""GrantScope — NIH RePORTER funding landscape explorer.

Usage:
    python3 src/main.py sync [--topics KEY ...] [--years N] [--max-results N]
    python3 src/main.py build [--refresh-briefing]
    python3 src/main.py stats [--topic KEY]
    python3 src/main.py search QUERY
    python3 src/main.py list-topics
    python3 src/main.py briefing [--topic KEY]

Run with no ANTHROPIC_API_KEY set to use the deterministic briefing fallback.
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ai_briefing  # noqa: E402
import analysis  # noqa: E402
import api_client  # noqa: E402
import db  # noqa: E402
import html_report  # noqa: E402
import topics as topics_module  # noqa: E402

BUILD_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BUILD_ROOT / "output" / "grantscope.db"
DEFAULT_OUTPUT_PATH = BUILD_ROOT / "output" / "dashboard.html"
DEFAULT_FISCAL_YEARS = list(range(datetime.now(timezone.utc).year - 4, datetime.now(timezone.utc).year + 1))


def _connect(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db.connect(str(db_path))


def cmd_list_topics(args: argparse.Namespace) -> int:
    for topic in topics_module.DEFAULT_TOPICS:
        print(f"{topic['key']:<24} {topic['label']}")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    conn = _connect(Path(args.db))
    keys = args.topics or topics_module.topic_keys()
    total_synced = 0
    had_error = False

    for key in keys:
        try:
            topic = topics_module.get_topic(key)
        except KeyError:
            print(f"Skipping unknown topic '{key}'", file=sys.stderr)
            had_error = True
            continue

        print(f"Syncing '{topic['label']}'...")
        try:
            projects = api_client.fetch_projects(
                topic["key"], topic["search_text"], args.years, max_results=args.max_results
            )
        except api_client.ApiClientError as exc:
            print(f"  Failed to sync '{topic['label']}': {exc}", file=sys.stderr)
            had_error = True
            continue

        count = db.upsert_projects(conn, projects)
        total_synced += count
        print(f"  {count} project(s) synced.")

    conn.close()
    print(f"Done. {total_synced} project record(s) processed across {len(keys)} topic(s).")
    return 1 if (had_error and total_synced == 0) else 0


def _topic_label(key: str) -> str:
    try:
        return topics_module.get_topic(key)["label"]
    except KeyError:
        return key


def _build_topic_data(conn, topic_key: str, api_key: Optional[str]) -> dict:
    rows = db.all_projects(conn, topic=topic_key)
    projects = [dict(row) for row in rows]

    funding_by_year = analysis.funding_by_year(projects)
    top_institutes = analysis.top_institutes(projects)
    top_organizations = analysis.top_organizations(projects)
    mechanisms = analysis.mechanism_breakdown(projects)
    keywords = analysis.extract_keywords(projects)
    stats = analysis.summary_stats(projects)

    briefing = ai_briefing.generate_briefing(
        _topic_label(topic_key), projects, stats, top_institutes, mechanisms, api_key=api_key
    )
    db.save_briefing(conn, topic_key, briefing["text"], briefing["source"])

    return {
        "key": topic_key,
        "label": _topic_label(topic_key),
        "projects": projects,
        "funding_by_year": funding_by_year,
        "top_institutes": top_institutes,
        "top_organizations": top_organizations,
        "mechanisms": mechanisms,
        "keywords": keywords,
        "stats": stats,
        "briefing": briefing,
    }


def cmd_build(args: argparse.Namespace) -> int:
    conn = _connect(Path(args.db))
    api_key = os.environ.get("ANTHROPIC_API_KEY") if not args.no_ai else None

    topic_keys = db.distinct_topics(conn)
    if not topic_keys:
        topic_keys = topics_module.topic_keys()

    if not args.refresh_briefing:
        # Reuse existing briefings when present to avoid unnecessary API calls.
        topics_data = []
        for key in topic_keys:
            existing = db.get_briefing(conn, key)
            rows = db.all_projects(conn, topic=key)
            projects = [dict(row) for row in rows]
            stats = analysis.summary_stats(projects)
            top_institutes = analysis.top_institutes(projects)
            mechanisms = analysis.mechanism_breakdown(projects)
            if existing is not None:
                briefing = {"text": existing["text"], "source": existing["source"]}
            else:
                briefing = ai_briefing.generate_briefing(
                    _topic_label(key), projects, stats, top_institutes, mechanisms, api_key=api_key
                )
                db.save_briefing(conn, key, briefing["text"], briefing["source"])
            topics_data.append({
                "key": key,
                "label": _topic_label(key),
                "projects": projects,
                "funding_by_year": analysis.funding_by_year(projects),
                "top_institutes": top_institutes,
                "top_organizations": analysis.top_organizations(projects),
                "mechanisms": mechanisms,
                "keywords": analysis.extract_keywords(projects),
                "stats": stats,
                "briefing": briefing,
            })
    else:
        topics_data = [_build_topic_data(conn, key, api_key) for key in topic_keys]

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    output_html = html_report.render_dashboard(topics_data, generated_at)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(output_html, encoding="utf-8")
    conn.close()

    print(f"Dashboard written to {out_path}")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    conn = _connect(Path(args.db))
    rows = db.all_projects(conn, topic=args.topic)
    projects = [dict(row) for row in rows]
    stats = analysis.summary_stats(projects)
    mechanisms = analysis.mechanism_breakdown(projects)
    top_institutes = analysis.top_institutes(projects, top_n=5)

    scope = _topic_label(args.topic) if args.topic else "All Topics"
    print(f"GrantScope — {scope}")
    print(f"  Projects: {stats['project_count']}")
    print(f"  Total funding: ${stats['total_amount']:,}")
    year_start, year_end = stats["fiscal_year_range"]
    if year_start:
        print(f"  Fiscal years: {year_start}-{year_end}")
    print(f"  Distinct institutes: {stats['distinct_institutes']}")
    print(f"  Distinct organizations: {stats['distinct_organizations']}")
    if top_institutes:
        print("  Top institutes:")
        for name, info in top_institutes:
            print(f"    {name}: ${info['total_amount']:,} ({info['count']} project(s))")
    if mechanisms:
        print("  Mechanisms:", ", ".join(f"{code} ({count})" for code, count in mechanisms.items()))
    conn.close()
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    conn = _connect(Path(args.db))
    rows = db.search_projects(conn, args.query)
    if not rows:
        print(f"No projects found matching '{args.query}'.")
    for row in rows:
        print(f"[{row['fiscal_year']}] {row['title']} — {row['org_name'] or 'unknown org'} (${(row['award_amount'] or 0):,})")
    conn.close()
    return 0


def cmd_briefing(args: argparse.Namespace) -> int:
    conn = _connect(Path(args.db))
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    keys = [args.topic] if args.topic else db.distinct_topics(conn) or topics_module.topic_keys()

    for key in keys:
        rows = db.all_projects(conn, topic=key)
        projects = [dict(row) for row in rows]
        stats = analysis.summary_stats(projects)
        top_institutes = analysis.top_institutes(projects)
        mechanisms = analysis.mechanism_breakdown(projects)
        briefing = ai_briefing.generate_briefing(
            _topic_label(key), projects, stats, top_institutes, mechanisms, api_key=api_key
        )
        db.save_briefing(conn, key, briefing["text"], briefing["source"])
        print(f"\n=== {_topic_label(key)} ({briefing['source']}) ===")
        print(briefing["text"])

    conn.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="grantscope", description="NIH RePORTER funding landscape explorer.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to the SQLite database.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Fetch and store projects from NIH RePORTER.")
    sync_parser.add_argument("--topics", nargs="+", default=None, help="Topic keys to sync (default: all).")
    sync_parser.add_argument("--years", nargs="+", type=int, default=DEFAULT_FISCAL_YEARS, help="Fiscal years to query.")
    sync_parser.add_argument("--max-results", type=int, default=100, help="Max results per topic.")
    sync_parser.set_defaults(func=cmd_sync)

    build_parser_ = subparsers.add_parser("build", help="Render the HTML dashboard from local data.")
    build_parser_.add_argument("--out", default=str(DEFAULT_OUTPUT_PATH), help="Output HTML path.")
    build_parser_.add_argument("--refresh-briefing", action="store_true", help="Regenerate AI briefings even if cached.")
    build_parser_.add_argument("--no-ai", action="store_true", help="Skip AI briefing calls; use template fallback only.")
    build_parser_.set_defaults(func=cmd_build)

    stats_parser = subparsers.add_parser("stats", help="Print a terminal summary.")
    stats_parser.add_argument("--topic", default=None, help="Restrict to one topic key.")
    stats_parser.set_defaults(func=cmd_stats)

    search_parser = subparsers.add_parser("search", help="Search stored projects.")
    search_parser.add_argument("query", help="Search text (matches title, abstract, org, PI).")
    search_parser.set_defaults(func=cmd_search)

    list_parser = subparsers.add_parser("list-topics", help="List default saved topics.")
    list_parser.set_defaults(func=cmd_list_topics)

    briefing_parser = subparsers.add_parser("briefing", help="Generate/refresh the AI landscape briefing.")
    briefing_parser.add_argument("--topic", default=None, help="Restrict to one topic key.")
    briefing_parser.set_defaults(func=cmd_briefing)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
