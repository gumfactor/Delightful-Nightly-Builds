"""Command-line interface for Waymark."""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path
from typing import Sequence

from . import db as db_module
from . import enrich as enrich_module
from . import git_reader
from . import render as render_module
from . import scorer


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _resolve_db_path(args: argparse.Namespace) -> Path:
    if args.db:
        return Path(args.db).expanduser()
    return db_module.default_db_path()


def cmd_index(args: argparse.Namespace) -> int:
    conn = db_module.connect(_resolve_db_path(args))
    try:
        known = db_module.known_commit_hashes(conn, args.label)
        try:
            commits = git_reader.read_commits(Path(args.repo_path), exclude_hashes=known)
        except git_reader.NotAGitRepoError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        records = []
        for commit in commits:
            score = scorer.score_commit(commit)
            tags = scorer.extract_tags(commit)
            summary = scorer.deterministic_summary(commit)
            records.append(
                {
                    **commit,
                    "decision_score": score,
                    "tags": tags,
                    "summary": summary,
                    "ai_summary": None,
                }
            )

        inserted = db_module.insert_commits(conn, args.label, records)
        db_module.upsert_repo(conn, args.label, str(Path(args.repo_path).expanduser().resolve()), _now_iso())
        print(f"Indexed {inserted} new commit(s) for '{args.label}' ({len(known)} already known).")
        return 0
    finally:
        conn.close()


def cmd_search(args: argparse.Namespace) -> int:
    conn = db_module.connect(_resolve_db_path(args))
    try:
        results = db_module.search_commits(
            conn,
            query=args.query,
            repo_label=args.repo,
            tag=args.tag,
            since=args.since,
            min_score=args.min_score,
        )
        if not results:
            print("No matching commits.")
            return 0
        for row in results:
            summary = row["ai_summary"] or row["summary"]
            print(f"[{row['decision_score']:>2}] {row['repo_label']}/{row['commit_hash'][:8]}  {summary}")
        return 0
    finally:
        conn.close()


def cmd_render(args: argparse.Namespace) -> int:
    conn = db_module.connect(_resolve_db_path(args))
    try:
        commits = db_module.all_commits(conn)
        output_path = Path(args.output) if args.output else Path.home() / ".waymark" / "dashboard.html"
        result_path = render_module.render_dashboard(commits, output_path)
        print(f"Rendered {len(commits)} commit(s) to {result_path}")
        return 0
    finally:
        conn.close()


def cmd_list_repos(args: argparse.Namespace) -> int:
    conn = db_module.connect(_resolve_db_path(args))
    try:
        rows = db_module.list_repos(conn)
        if not rows:
            print("No repos indexed yet.")
            return 0
        for row in rows:
            print(
                f"{row['label']:<20} {row['commit_count']:>6} commits  "
                f"{row['decision_count'] or 0:>4} decision-worthy  last indexed {row['last_indexed_at']}"
            )
        return 0
    finally:
        conn.close()


def cmd_enrich(args: argparse.Namespace) -> int:
    if not enrich_module.is_available():
        print("ANTHROPIC_API_KEY is not set; nothing to enrich (deterministic summaries already stored).")
        return 0

    conn = db_module.connect(_resolve_db_path(args))
    try:
        candidates = db_module.commits_needing_enrichment(conn, args.repo, args.limit)
        if not candidates:
            print("No commits need enrichment.")
            return 0

        enriched = 0
        for row in candidates:
            commit = dict(row)
            try:
                summary = enrich_module.enrich_commit(commit)
            except enrich_module.EnrichmentError as exc:
                print(f"warning: enrichment failed for {commit['commit_hash'][:8]}: {exc}", file=sys.stderr)
                continue
            db_module.set_ai_summary(conn, commit["repo_label"], commit["commit_hash"], summary)
            enriched += 1

        print(f"Enriched {enriched} of {len(candidates)} candidate commit(s).")
        return 0
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="waymark",
        description="Mine git commit history into a searchable cross-project decision knowledge base.",
    )
    parser.add_argument("--db", help="Path to the SQLite database (default: ~/.waymark/waymark.db)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Index a git repository")
    index_parser.add_argument("repo_path", help="Path to the local git repository")
    index_parser.add_argument("--label", required=True, help="Short label to identify this repo")
    index_parser.set_defaults(func=cmd_index)

    search_parser = subparsers.add_parser("search", help="Search indexed commits")
    search_parser.add_argument("query", nargs="?", default=None, help="Text to search for")
    search_parser.add_argument("--repo", default=None, help="Filter by repo label")
    search_parser.add_argument("--tag", default=None, help="Filter by tag")
    search_parser.add_argument("--since", default=None, help="Only commits on/after this ISO date")
    search_parser.add_argument("--min-score", type=int, default=0, help="Minimum decision score")
    search_parser.set_defaults(func=cmd_search)

    render_parser = subparsers.add_parser("render", help="Render the HTML dashboard")
    render_parser.add_argument("--output", default=None, help="Output HTML path (default: ~/.waymark/dashboard.html)")
    render_parser.set_defaults(func=cmd_render)

    list_parser = subparsers.add_parser("list-repos", help="List indexed repos")
    list_parser.set_defaults(func=cmd_list_repos)

    enrich_parser = subparsers.add_parser("enrich", help="AI-enrich high-scoring commit summaries")
    enrich_parser.add_argument("--repo", default=None, help="Only enrich commits from this repo label")
    enrich_parser.add_argument("--limit", type=int, default=20, help="Maximum commits to enrich this run")
    enrich_parser.set_defaults(func=cmd_enrich)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
