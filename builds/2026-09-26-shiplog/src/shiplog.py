#!/usr/bin/env python3
"""Shiplog — generate a categorized changelog from a local git repo's history.

Usage:
    python3 shiplog.py generate <repo-path> [--since REF] [--until REF]
        [--format md|html|both] [--out DIR] [--ai-polish] [--repo OWNER/NAME]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_polish import polish_sections
from classify import cancel_reverts, classify_commit, group_sections
from git_log import GitLogError, fetch_commits
from github_enrich import enrich_with_github
from render import ChangelogResult, render_html, render_markdown
from semver import suggest_bump


def build_changelog(
    repo_path: str,
    since: str | None,
    until: str,
    github_repo: str | None,
    github_token: str | None,
    ai_api_key: str | None,
) -> ChangelogResult:
    raw_commits, range_label = fetch_commits(repo_path, since, until)
    total_commits = len(raw_commits)

    commits = [classify_commit(raw) for raw in raw_commits]
    commits, cancelled_pairs = cancel_reverts(commits)
    commits = enrich_with_github(commits, github_repo, github_token)

    sections = group_sections(commits)
    section_text = polish_sections(sections, ai_api_key)
    bump = suggest_bump(sections)

    return ChangelogResult(
        range_label=range_label,
        total_commits=total_commits,
        sections=sections,
        section_text=section_text,
        cancelled_pairs=cancelled_pairs,
        suggested_bump=bump,
    )


def _safe_range_slug(range_label: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in range_label)


def run_generate(args: argparse.Namespace) -> int:
    github_token = os.environ.get("GITHUB_TOKEN") if args.repo else None
    ai_api_key = os.environ.get("ANTHROPIC_API_KEY") if args.ai_polish else None

    try:
        result = build_changelog(
            repo_path=args.repo_path,
            since=args.since,
            until=args.until,
            github_repo=args.repo,
            github_token=github_token,
            ai_api_key=ai_api_key,
        )
    except GitLogError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    out_dir = Path(args.out) if args.out else Path.cwd()
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = _safe_range_slug(result.range_label)

    if args.format in ("md", "both"):
        md_path = out_dir / f"CHANGELOG_{slug}.md"
        md_path.write_text(render_markdown(result), encoding="utf-8")
        print(f"wrote {md_path}")

    if args.format in ("html", "both"):
        html_path = out_dir / f"report_{slug}.html"
        html_path.write_text(render_html(result), encoding="utf-8")
        print(f"wrote {html_path}")

    print(f"suggested bump: {result.suggested_bump} | commits: {result.total_commits} | "
          f"cancelled pairs: {len(result.cancelled_pairs)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="shiplog", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen = subparsers.add_parser("generate", help="Generate a changelog for a local git repo")
    gen.add_argument("repo_path", help="Path to a local git repository")
    gen.add_argument("--since", default=None, help="Lower bound ref or date (default: latest tag, or full history)")
    gen.add_argument("--until", default="HEAD", help="Upper bound ref (default: HEAD)")
    gen.add_argument("--format", choices=["md", "html", "both"], default="both")
    gen.add_argument("--out", default=None, help="Output directory (default: current directory)")
    gen.add_argument("--ai-polish", action="store_true", help="Use ANTHROPIC_API_KEY to write prose summaries")
    gen.add_argument("--repo", default=None, help="owner/name — enables GitHub PR title/label enrichment via GITHUB_TOKEN")
    gen.set_defaults(func=run_generate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
