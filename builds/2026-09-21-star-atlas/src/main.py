"""Star Atlas CLI — turn your GitHub stars into a searchable knowledge base."""
from __future__ import annotations

import argparse
import os
import sys
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src import github_client, report, store, tagging

BUILD_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB = str(BUILD_DIR / "star_atlas.db")


def _default_out_path() -> str:
    return str(BUILD_DIR / "dashboard.html")


def cmd_sync(args: argparse.Namespace) -> int:
    token = args.token or os.environ.get("GITHUB_TOKEN")
    api_key = None
    if args.ai:
        api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")

    conn = store.connect(args.db)
    since = None if args.full else store.latest_starred_at(conn)

    try:
        fetched = github_client.fetch_starred(token, since=since)
    except github_client.MissingTokenError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except github_client.GitHubAPIError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    ingested_at = datetime.now(timezone.utc).isoformat()
    for repo in fetched:
        repo_dict = {
            "id": repo.id,
            "full_name": repo.full_name,
            "description": repo.description,
            "html_url": repo.html_url,
            "language": repo.language,
            "topics": repo.topics,
            "stargazers_count": repo.stargazers_count,
            "starred_at": repo.starred_at,
        }
        if args.ai:
            tag, note, source = tagging.ai_enrich(repo_dict, api_key)
        else:
            tag, note = tagging.rule_tag(repo.language, repo.topics, repo.description)
            source = "rule"

        repo_dict.update(tag=tag, note=note, source=source, ingested_at=ingested_at)
        store.upsert_repo(conn, repo_dict)

    print(f"Synced {len(fetched)} repo(s). Total in library: {store.count_repos(conn)}.")
    conn.close()
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    conn = store.connect(args.db)
    results = store.search_repos(
        conn, query=args.query, tag=args.tag, language=args.language, limit=args.limit
    )
    _print_repo_table(results)
    conn.close()
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    conn = store.connect(args.db)
    results = store.list_repos(conn, tag=args.tag, language=args.language, limit=args.limit)
    _print_repo_table(results)
    conn.close()
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    conn = store.connect(args.db)
    s = store.stats(conn)
    print(f"Total repos: {s['total']}")
    print(f"Last synced: {s['latest_starred_at'] or 'never'}")
    print("\nBy tag:")
    for tag, count in s["by_tag"].items():
        print(f"  {tag}: {count}")
    print("\nBy language:")
    for lang, count in s["by_language"].items():
        print(f"  {lang}: {count}")
    conn.close()
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    conn = store.connect(args.db)
    repos = store.list_repos(conn, limit=100000)
    s = store.stats(conn)
    html = report.render_html(repos, s)
    out_path = args.out or _default_out_path()
    Path(out_path).write_text(html, encoding="utf-8")
    print(f"Dashboard written to {out_path}")
    if args.open:
        webbrowser.open(f"file://{Path(out_path).resolve()}")
    conn.close()
    return 0


def _print_repo_table(results: list) -> None:
    if not results:
        print("No repos found.")
        return
    for repo in results:
        print(f"[{repo['tag']}] {repo['full_name']}  ({repo['language'] or 'n/a'}, "
              f"★{repo['stargazers_count']})")
        print(f"    {repo['note']}")
        print(f"    {repo['html_url']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="star-atlas", description="Turn your GitHub stars into a searchable knowledge base."
    )
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to the SQLite database.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_p = subparsers.add_parser("sync", help="Fetch and store starred repos.")
    sync_p.add_argument("--token", default=None, help="GitHub token (else $GITHUB_TOKEN).")
    sync_p.add_argument("--ai", action="store_true", help="Enrich tags/notes via Claude.")
    sync_p.add_argument("--api-key", default=None, help="Anthropic API key (else $ANTHROPIC_API_KEY).")
    sync_p.add_argument("--full", action="store_true", help="Re-fetch all stars, not just new ones.")
    sync_p.set_defaults(func=cmd_sync)

    search_p = subparsers.add_parser("search", help="Search the library.")
    search_p.add_argument("query", help="Text to search for.")
    search_p.add_argument("--tag", default=None)
    search_p.add_argument("--language", default=None)
    search_p.add_argument("--limit", type=int, default=50)
    search_p.set_defaults(func=cmd_search)

    list_p = subparsers.add_parser("list", help="List repos, optionally filtered.")
    list_p.add_argument("--tag", default=None)
    list_p.add_argument("--language", default=None)
    list_p.add_argument("--limit", type=int, default=200)
    list_p.set_defaults(func=cmd_list)

    stats_p = subparsers.add_parser("stats", help="Show library statistics.")
    stats_p.set_defaults(func=cmd_stats)

    render_p = subparsers.add_parser("render", help="Render the HTML dashboard.")
    render_p.add_argument("--out", default=None, help="Output path (default: dashboard.html).")
    render_p.add_argument("--open", action="store_true", help="Open in the default browser.")
    render_p.set_defaults(func=cmd_render)

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
