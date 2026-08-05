"""Impact Ledger — track a researcher's own OpenAlex citation history over time.

Usage:
    python3 src/main.py search-author "Jane Doe"
    python3 src/main.py sync --author-id A5023888391 [--mailto you@example.com]
    python3 src/main.py history --author-id A5023888391
    python3 src/main.py render --author-id A5023888391 [--out dashboard.html] [--ai]
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import ai
    import db
    import dashboard
    import openalex
else:
    from . import ai, db, dashboard, openalex

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "impact_ledger.db"


def today_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")


def cmd_search_author(args: argparse.Namespace) -> int:
    try:
        candidates = openalex.search_authors(args.query, mailto=args.mailto)
    except openalex.OpenAlexError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not candidates:
        print(f"No OpenAlex authors found matching '{args.query}'.")
        return 0

    print(f"Candidates for '{args.query}':\n")
    for candidate in candidates:
        print(
            f"  {candidate['author_id']:<15} {candidate['display_name']}"
            f" — {candidate['institution'] or 'no affiliation listed'}"
            f" ({candidate['works_count']} works, {candidate['cited_by_count']} citations)"
        )
    print("\nUse the author_id you recognize with: sync --author-id <ID>")
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    conn = db.connect(args.db_path)
    sync_date = args.sync_date or today_utc()

    try:
        author = openalex.get_author(args.author_id, mailto=args.mailto)
    except openalex.OpenAlexError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    db.upsert_author(conn, author, sync_date)

    work_count = 0
    try:
        for work in openalex.iter_author_works(args.author_id, mailto=args.mailto):
            db.upsert_work_snapshot(conn, author["author_id"], work, sync_date)
            work_count += 1
    except openalex.OpenAlexError as exc:
        print(f"Error while fetching works: {exc}", file=sys.stderr)
        return 1

    print(f"Synced {author['display_name']} ({author['author_id']}) — {work_count} works on {sync_date}.")
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    conn = db.connect(args.db_path)
    dates = db.distinct_sync_dates(conn, args.author_id)

    if not dates:
        print(f"No sync history for author {args.author_id}. Run 'sync --author-id {args.author_id}' first.")
        return 0

    if len(dates) == 1:
        print(f"Only one snapshot so far ({dates[0]}) — sync again later to see trends.")

    trend = db.citation_trend(conn, args.author_id)
    print(f"Citation history for {args.author_id}:\n")
    for point in trend:
        print(f"  {point['sync_date']}  total citations: {point['total_citations']}")

    rising = db.rising_papers(conn, args.author_id)
    if rising:
        print("\nRising papers since previous snapshot:")
        for paper in rising:
            print(f"  +{paper['velocity']:<4} {paper['title']}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    conn = db.connect(args.db_path)
    author = db.get_author(conn, args.author_id)

    if author is None:
        print(f"No data for author {args.author_id}. Run 'sync --author-id {args.author_id}' first.", file=sys.stderr)
        return 1

    trend = db.citation_trend(conn, args.author_id)
    papers = db.latest_snapshot(conn, args.author_id)
    rising = db.rising_papers(conn, args.author_id)

    ai_notes: dict[str, str] = {}
    if args.ai:
        for paper in rising:
            ai_notes[paper["work_id"]] = ai.generate_note(
                title=paper["title"],
                abstract=paper.get("abstract", ""),
                previous_count=paper["previous_cited_by_count"],
                latest_count=paper["cited_by_count"],
                latest_date=paper["latest_date"],
            )

    html = dashboard.render_dashboard(author, trend, papers, rising, ai_notes)
    out_path = Path(args.out)
    out_path.write_text(html, encoding="utf-8")
    print(f"Dashboard written to {out_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="impact-ledger", description=__doc__)
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="Path to the SQLite database file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search-author", help="Find OpenAlex author IDs by name")
    search_parser.add_argument("query", help="Author name to search for")
    search_parser.add_argument("--mailto", default=None, help="Optional email for OpenAlex's polite pool")
    search_parser.set_defaults(func=cmd_search_author)

    sync_parser = subparsers.add_parser("sync", help="Fetch and snapshot an author's works")
    sync_parser.add_argument("--author-id", required=True, help="OpenAlex author ID, e.g. A5023888391")
    sync_parser.add_argument("--mailto", default=None, help="Optional email for OpenAlex's polite pool")
    sync_parser.add_argument("--sync-date", default=None, help="Override the UTC sync date (for testing)")
    sync_parser.set_defaults(func=cmd_sync)

    history_parser = subparsers.add_parser("history", help="Show citation history from local snapshots")
    history_parser.add_argument("--author-id", required=True, help="OpenAlex author ID")
    history_parser.set_defaults(func=cmd_history)

    render_parser = subparsers.add_parser("render", help="Render the HTML dashboard")
    render_parser.add_argument("--author-id", required=True, help="OpenAlex author ID")
    render_parser.add_argument("--out", default="dashboard.html", help="Output HTML file path")
    render_parser.add_argument("--ai", action="store_true", help="Generate AI commentary for rising papers")
    render_parser.set_defaults(func=cmd_render)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
