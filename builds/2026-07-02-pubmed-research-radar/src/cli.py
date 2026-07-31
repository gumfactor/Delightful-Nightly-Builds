"""Command-line entrypoint for the PubMed Research Radar.

Commands:
    topics list
    topics add <name> <query>
    topics remove <name>
    fetch [--days N] [--max-per-topic N] [--db PATH]
    report [--output PATH] [--db PATH]
    search <query> [--db PATH]
    stats [--db PATH]
"""

from __future__ import annotations

import argparse
import sys

from src import db as db_module
from src.ai_scoring import score_article
from src.config import DEFAULT_DB_PATH, DEFAULT_FETCH_DAYS, DEFAULT_MAX_PER_TOPIC, DEFAULT_TOPICS
from src.pubmed import PubMedError, fetch_articles, search_pmids
from src.report import write_report


def _ensure_seeded(conn) -> None:
    """Seed the default topics on first use if the topics table is empty."""
    if not db_module.list_topics(conn):
        for topic in DEFAULT_TOPICS:
            db_module.add_topic(conn, topic.name, topic.query)


def cmd_topics_list(args: argparse.Namespace) -> int:
    conn = db_module.connect(args.db)
    _ensure_seeded(conn)
    for topic in db_module.list_topics(conn):
        print(f"[{topic['id']}] {topic['name']}  —  {topic['query']}")
    return 0


def cmd_topics_add(args: argparse.Namespace) -> int:
    conn = db_module.connect(args.db)
    if db_module.get_topic_by_name(conn, args.name) is not None:
        print(f"Topic '{args.name}' already exists.", file=sys.stderr)
        return 1
    db_module.add_topic(conn, args.name, args.query)
    print(f"Added topic '{args.name}'.")
    return 0


def cmd_topics_remove(args: argparse.Namespace) -> int:
    conn = db_module.connect(args.db)
    if db_module.remove_topic(conn, args.name):
        print(f"Removed topic '{args.name}'.")
        return 0
    print(f"No topic named '{args.name}'.", file=sys.stderr)
    return 1


def cmd_fetch(args: argparse.Namespace) -> int:
    conn = db_module.connect(args.db)
    _ensure_seeded(conn)
    topics = db_module.list_topics(conn)
    new_count = 0
    for topic in topics:
        try:
            pmids = search_pmids(topic["query"], days=args.days, retmax=args.max_per_topic)
            articles = fetch_articles(pmids)
        except PubMedError as exc:
            print(f"Skipping '{topic['name']}': {exc}", file=sys.stderr)
            continue
        for article in articles:
            if db_module.upsert_article(conn, topic["id"], article):
                new_count += 1
        print(f"{topic['name']}: {len(articles)} fetched")

    for row in db_module.get_unscored_articles(conn):
        topic = next((t for t in topics if t["id"] == row["topic_id"]), None)
        topic_name = topic["name"] if topic else "Unknown"
        topic_query = topic["query"] if topic else ""
        result = score_article(topic_name, topic_query, dict(row))
        db_module.set_scoring(
            conn,
            row["pmid"],
            result.relevance_score,
            result.ai_summary,
            result.methodology_tag,
            result.scoring_method,
        )

    print(f"Done. {new_count} new articles stored.")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    conn = db_module.connect(args.db)
    write_report(conn, args.output)
    print(f"Report written to {args.output}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    conn = db_module.connect(args.db)
    results = db_module.search_articles(conn, args.query)
    if not results:
        print("No matches.")
        return 0
    for row in results:
        score = f"{row['relevance_score']:.1f}" if row["relevance_score"] is not None else "?"
        print(f"[{score}] {row['title']} ({row['pub_date']})")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    conn = db_module.connect(args.db)
    stats = db_module.get_stats(conn)
    print(f"Total articles: {stats['total']}")
    print(f"Unscored: {stats['unscored']}")
    for entry in stats["per_topic"]:
        print(f"  {entry['topic']}: {entry['count']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="radar", description="PubMed Research Radar")
    subparsers = parser.add_subparsers(dest="command", required=True)

    topics_parser = subparsers.add_parser("topics", help="Manage saved search topics")
    topics_sub = topics_parser.add_subparsers(dest="topics_command", required=True)

    topics_list_parser = topics_sub.add_parser("list", help="List saved topics")
    topics_list_parser.add_argument("--db", default=DEFAULT_DB_PATH)
    topics_list_parser.set_defaults(func=cmd_topics_list)

    topics_add_parser = topics_sub.add_parser("add", help="Add a saved topic")
    topics_add_parser.add_argument("name")
    topics_add_parser.add_argument("query")
    topics_add_parser.add_argument("--db", default=DEFAULT_DB_PATH)
    topics_add_parser.set_defaults(func=cmd_topics_add)

    topics_remove_parser = topics_sub.add_parser("remove", help="Remove a saved topic")
    topics_remove_parser.add_argument("name")
    topics_remove_parser.add_argument("--db", default=DEFAULT_DB_PATH)
    topics_remove_parser.set_defaults(func=cmd_topics_remove)

    fetch_parser = subparsers.add_parser("fetch", help="Fetch new articles for all topics")
    fetch_parser.add_argument("--days", type=int, default=DEFAULT_FETCH_DAYS)
    fetch_parser.add_argument("--max-per-topic", type=int, default=DEFAULT_MAX_PER_TOPIC)
    fetch_parser.add_argument("--db", default=DEFAULT_DB_PATH)
    fetch_parser.set_defaults(func=cmd_fetch)

    report_parser = subparsers.add_parser("report", help="Render the HTML report")
    report_parser.add_argument("--output", default="report.html")
    report_parser.add_argument("--db", default=DEFAULT_DB_PATH)
    report_parser.set_defaults(func=cmd_report)

    search_parser = subparsers.add_parser("search", help="Full-text search stored articles")
    search_parser.add_argument("query")
    search_parser.add_argument("--db", default=DEFAULT_DB_PATH)
    search_parser.set_defaults(func=cmd_search)

    stats_parser = subparsers.add_parser("stats", help="Show quick counts")
    stats_parser.add_argument("--db", default=DEFAULT_DB_PATH)
    stats_parser.set_defaults(func=cmd_stats)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
