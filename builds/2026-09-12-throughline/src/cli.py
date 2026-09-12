"""Argparse CLI for Throughline: lookup, sync, cluster, narrative, growth, render, papers."""
from __future__ import annotations

import argparse
import sys

from . import cluster as cluster_mod
from . import narrative as narrative_mod
from . import render as render_mod
from . import storage
from .semantic_scholar import SemanticScholarError, fetch_author_papers, search_authors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="throughline", description="Personal research-corpus knowledge base")
    parser.add_argument("--db", default="throughline.db", help="Path to the local SQLite database")
    sub = parser.add_subparsers(dest="command", required=True)

    lookup_p = sub.add_parser("lookup", help="Search Semantic Scholar for a candidate author id")
    lookup_p.add_argument("name")

    sync_p = sub.add_parser("sync", help="Fetch a confirmed author's papers into the local database")
    sync_p.add_argument("--author-id", required=True)
    sync_p.add_argument("--name", required=True, help="Author display name to store locally")

    sub.add_parser("cluster", help="Recompute thematic clusters from the local paper corpus")

    narrative_p = sub.add_parser("narrative", help="Generate a summary for each cluster")
    narrative_p.add_argument("--ai", action="store_true", help="Use Claude Haiku (requires ANTHROPIC_API_KEY)")

    sub.add_parser("growth", help="Show citation-count growth since the first sync")

    render_p = sub.add_parser("render", help="Write the self-contained HTML dashboard")
    render_p.add_argument("--output", default="throughline_dashboard.html")

    sub.add_parser("papers", help="List all locally stored papers")

    return parser


def cmd_lookup(args, search_fn=search_authors) -> int:
    try:
        candidates = search_fn(args.name)
    except (ValueError, SemanticScholarError) as exc:
        print(f"Error: {exc}")
        return 1

    if not candidates:
        print(f"No authors found matching '{args.name}'.")
        return 0

    print(f"Found {len(candidates)} candidate(s) for '{args.name}':\n")
    for candidate in candidates:
        print(f"  id={candidate.author_id}  {candidate.name}  "
              f"({candidate.paper_count} papers, {candidate.citation_count} citations)")
        if candidate.affiliations:
            print(f"    affiliations: {', '.join(candidate.affiliations)}")
        if candidate.sample_titles:
            print(f"    sample titles: {'; '.join(candidate.sample_titles)}")
    print("\nConfirm the correct author id, then run:")
    print(f'  throughline sync --author-id <id> --name "{args.name}"')
    return 0


def cmd_sync(args, conn, fetch_fn=fetch_author_papers) -> int:
    try:
        papers = fetch_fn(args.author_id)
    except (ValueError, SemanticScholarError) as exc:
        print(f"Error: {exc}")
        return 1

    storage.set_author(conn, args.author_id, args.name)
    count = storage.upsert_papers(conn, papers)
    print(f"Synced {count} paper(s) for {args.name} (author id {args.author_id}).")
    return 0


def cmd_cluster(args, conn) -> int:
    papers = storage.list_papers(conn)
    if not papers:
        print("No papers in the local database yet. Run 'sync' first.")
        return 1

    clusters = cluster_mod.cluster_papers(list(papers))
    storage.replace_clusters(conn, clusters)
    print(f"Computed {len(clusters)} cluster(s) from {len(papers)} paper(s).")
    for c in clusters:
        print(f"  - {c['label']} ({len(c['paper_ids'])} papers)")
    return 0


def cmd_narrative(args, conn, generate_fn=narrative_mod.generate_narrative) -> int:
    clusters = storage.list_clusters(conn)
    if not clusters:
        print("No clusters yet. Run 'cluster' first.")
        return 1

    for c in clusters:
        text, source = generate_fn(c, use_ai=args.ai)
        storage.set_narrative(conn, c["id"], text, source)
        preview = text if len(text) <= 120 else text[:117] + "..."
        print(f"[{source}] {c['label']}: {preview}")
    return 0


def cmd_growth(args, conn) -> int:
    growth = storage.citation_growth(conn)
    if not growth:
        print("No citation snapshots yet. Run 'sync' first.")
        return 1

    print(f"{'Title':<50} {'First':>6} {'Latest':>6} {'Delta':>6}")
    for row in growth:
        title = row["title"] if len(row["title"]) <= 48 else row["title"][:45] + "..."
        print(f"{title:<50} {row['first_count']:>6} {row['latest_count']:>6} {row['delta']:>+6}")
    return 0


def cmd_render(args, conn) -> int:
    papers = storage.list_papers(conn)
    if not papers:
        print("No papers in the local database yet. Run 'sync' first.")
        return 1

    author = storage.get_author(conn)
    author_name = author["name"] if author else "Unknown author"
    clusters = storage.list_clusters(conn)
    growth = storage.citation_growth(conn)

    html = render_mod.render_dashboard(author_name, storage.now_iso(), clusters, list(papers), growth)
    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write(html)
    print(f"Wrote dashboard to {args.output}")
    return 0


def cmd_papers(args, conn) -> int:
    papers = storage.list_papers(conn)
    if not papers:
        print("No papers in the local database yet. Run 'sync' first.")
        return 0

    for paper in papers:
        year = paper["year"] if paper["year"] else "n.d."
        print(f"[{year}] {paper['title']} ({paper['citation_count']} citations)")
    return 0


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "lookup":
        return cmd_lookup(args)

    conn = storage.connect(args.db)
    try:
        if args.command == "sync":
            return cmd_sync(args, conn)
        if args.command == "cluster":
            return cmd_cluster(args, conn)
        if args.command == "narrative":
            return cmd_narrative(args, conn)
        if args.command == "growth":
            return cmd_growth(args, conn)
        if args.command == "render":
            return cmd_render(args, conn)
        if args.command == "papers":
            return cmd_papers(args, conn)
        parser.error(f"unknown command {args.command!r}")
        return 2
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
