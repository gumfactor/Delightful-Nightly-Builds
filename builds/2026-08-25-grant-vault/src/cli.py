"""Grant Vault command-line interface."""

import argparse
import os
import sys

from src import ingest as ingest_module
from src import render as render_module
from src import search as search_module
from src import store

_DEFAULT_DB = "grantvault.db"
_DEFAULT_OUTPUT = "grant_vault_dashboard.html"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="grantvault",
        description="A personal knowledge base of reusable grant-writing language.",
    )
    parser.add_argument(
        "--db", default=_DEFAULT_DB, help=f"SQLite database path (default: {_DEFAULT_DB})"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser(
        "ingest", help="Ingest a grant document file or a folder of them"
    )
    ingest_parser.add_argument("path", help="Path to a .txt/.md file or a folder of them")
    ingest_parser.add_argument(
        "--ai",
        action="store_true",
        help="Use the Anthropic API (requires ANTHROPIC_API_KEY) for summaries and tags",
    )

    search_parser = subparsers.add_parser("search", help="Search stored grant language")
    search_parser.add_argument("query", nargs="?", default="", help="Search text")
    search_parser.add_argument("--section", default=None, help="Filter by section type")
    search_parser.add_argument("--tag", default=None, help="Filter by tag")
    search_parser.add_argument(
        "--min-reuse", type=int, default=None, help="Minimum reusability score (0-10)"
    )

    subparsers.add_parser("stats", help="Show summary statistics")

    render_parser = subparsers.add_parser("render", help="Generate the HTML dashboard")
    render_parser.add_argument(
        "--output", default=_DEFAULT_OUTPUT, help=f"Output HTML path (default: {_DEFAULT_OUTPUT})"
    )

    return parser


def _run_ingest(args, conn) -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY") if args.ai else None
    if args.ai and not api_key:
        print("Warning: --ai was set but ANTHROPIC_API_KEY is not in the environment; "
              "continuing with deterministic tags only.")

    try:
        summary = ingest_module.ingest_path(args.path, conn, use_ai=args.ai, api_key=api_key)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(
        f"Ingested {summary['documents_processed']} document(s), "
        f"skipped {summary['documents_skipped']} unchanged, "
        f"inserted {summary['chunks_inserted']} chunk(s)."
    )
    return 0


def _run_search(args, conn) -> int:
    results = search_module.search(
        conn,
        query=args.query,
        section=args.section,
        tag=args.tag,
        min_reuse=args.min_reuse,
    )
    if not results:
        print("No matching chunks found.")
        return 0

    for chunk in results:
        preview = chunk["text"][:150].replace("\n", " ")
        if len(chunk["text"]) > 150:
            preview += "..."
        print(
            f"[{chunk['section_type']}] {chunk['reuse_tier']} "
            f"({chunk['reuse_score']}/10) — {chunk['document_path']}"
        )
        print(f"  {preview}")
        print(f"  tags: {', '.join(chunk['tags'])}")
        print()
    return 0


def _run_stats(_args, conn) -> int:
    chunks = store.get_all_chunks(conn)
    document_paths = {chunk["document_path"] for chunk in chunks}

    print(f"Documents: {len(document_paths)}")
    print(f"Chunks: {len(chunks)}")

    by_section: dict = {}
    by_tier: dict = {}
    tag_counts: dict = {}
    for chunk in chunks:
        by_section[chunk["section_type"]] = by_section.get(chunk["section_type"], 0) + 1
        by_tier[chunk["reuse_tier"]] = by_tier.get(chunk["reuse_tier"], 0) + 1
        for tag in chunk["tags"]:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    print("\nBy section:")
    for section, count in sorted(by_section.items(), key=lambda item: -item[1]):
        print(f"  {section}: {count}")

    print("\nBy reusability tier:")
    for tier in ("High", "Medium", "Low"):
        print(f"  {tier}: {by_tier.get(tier, 0)}")

    top_tags = sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))[:10]
    if top_tags:
        print("\nTop tags:")
        for tag, count in top_tags:
            print(f"  #{tag}: {count}")

    return 0


def _run_render(args, conn) -> int:
    render_module.render_html(conn, args.output)
    print(f"Dashboard written to {args.output}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    conn = store.init_db(args.db)

    try:
        if args.command == "ingest":
            return _run_ingest(args, conn)
        if args.command == "search":
            return _run_search(args, conn)
        if args.command == "stats":
            return _run_stats(args, conn)
        if args.command == "render":
            return _run_render(args, conn)
        parser.error(f"Unknown command: {args.command}")
        return 2
    finally:
        conn.close()
