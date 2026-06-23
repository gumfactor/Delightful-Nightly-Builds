"""Paper Lens — CLI entry point."""
import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running as `python src/main.py` from the build folder
sys.path.insert(0, str(Path(__file__).parent))

from fetcher import fetch_all_topics
from analyzer import analyze_papers
from database import init_db, insert_paper, get_papers, mark_as_read, search_papers, get_today_count
from renderer import render_html

BUILD_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BUILD_DIR / "output"
DATA_DIR = BUILD_DIR / "data"
DB_PATH = DATA_DIR / "papers.db"


def cmd_fetch(args) -> None:
    init_db(DB_PATH)
    print("Fetching papers from arXiv…")
    papers = fetch_all_topics()
    print(f"  Found {len(papers)} papers across all topics")

    # Filter to only new papers (not in DB yet)
    existing = {p["arxiv_id"] for p in get_papers(DB_PATH)}
    new_papers = [p for p in papers if p["arxiv_id"] not in existing]
    print(f"  {len(new_papers)} new (not previously seen)")

    if not new_papers:
        print("No new papers to add. Run `view` to see your inbox.")
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        print(f"  Analyzing {len(new_papers)} papers with Claude Haiku…")
    else:
        print("  ANTHROPIC_API_KEY not set — using defaults (relevance=5, truncated abstract)")

    analysis = analyze_papers(new_papers, api_key)
    today = datetime.now(timezone.utc).isoformat()

    added = 0
    for paper in new_papers:
        meta = analysis.get(paper["arxiv_id"], {})
        record = {
            "arxiv_id": paper["arxiv_id"],
            "title": paper["title"],
            "authors": paper["authors"],
            "abstract": paper["abstract"],
            "published_date": paper["published_date"],
            "fetched_date": today,
            "relevance_score": meta.get("relevance_score"),
            "summary": meta.get("summary"),
            "methodology": meta.get("methodology"),
            "topic_label": meta.get("topic_label"),
        }
        if insert_paper(record, DB_PATH):
            added += 1

    print(f"  Added {added} papers to database.")
    print("Run `python src/main.py view` to open the HTML inbox.")


def cmd_view(args) -> None:
    init_db(DB_PATH)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    papers = get_papers(DB_PATH)
    html_content = render_html(papers)
    out_path = OUTPUT_DIR / "inbox.html"
    out_path.write_text(html_content, encoding="utf-8")
    print(f"Viewer generated: {out_path}")
    print(f"  {len(papers)} papers | Open in your browser.")


def cmd_read(args) -> None:
    init_db(DB_PATH)
    arxiv_id = args.arxiv_id
    if mark_as_read(arxiv_id, DB_PATH):
        print(f"Marked as read: {arxiv_id}")
        print("Run `python src/main.py view` to refresh the HTML viewer.")
    else:
        print(f"Paper not found: {arxiv_id}", file=sys.stderr)
        sys.exit(1)


def cmd_search(args) -> None:
    init_db(DB_PATH)
    query = args.query
    results = search_papers(query, DB_PATH)
    if not results:
        print(f"No papers matching '{query}'.")
        return
    print(f"{len(results)} result(s) for '{query}':\n")
    for p in results:
        score = p.get("relevance_score") or "—"
        read_flag = " [read]" if p.get("is_read") else ""
        print(f"  [{score}/10]{read_flag} {p['title']}")
        print(f"         {p['authors'][:60]} · {p['published_date']}")
        if p.get("summary"):
            print(f"         {p['summary'][:120]}…")
        print()


def cmd_list(args) -> None:
    init_db(DB_PATH)
    papers = get_papers(DB_PATH)
    if not papers:
        print("No papers in database. Run `fetch` first.")
        return
    print(f"{len(papers)} paper(s) in database:\n")
    for p in papers:
        score = p.get("relevance_score") or "—"
        read_flag = " [read]" if p.get("is_read") else ""
        print(f"  [{score}/10]{read_flag} {p['arxiv_id']}  {p['title'][:70]}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Paper Lens — arXiv research paper inbox with AI relevance scoring"
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("fetch", help="Fetch new papers from arXiv and analyze with Claude")
    sub.add_parser("view", help="Generate HTML inbox viewer in output/")
    read_p = sub.add_parser("read", help="Mark a paper as read")
    read_p.add_argument("arxiv_id", help="arXiv ID (e.g. 2410.00001)")
    search_p = sub.add_parser("search", help="Search papers by keyword")
    search_p.add_argument("query", help="Search term")
    sub.add_parser("list", help="List all papers (text output)")

    args = parser.parse_args()

    dispatch = {
        "fetch": cmd_fetch,
        "view": cmd_view,
        "read": cmd_read,
        "search": cmd_search,
        "list": cmd_list,
    }

    if args.command not in dispatch:
        parser.print_help()
        sys.exit(1)

    dispatch[args.command](args)


if __name__ == "__main__":
    main()
