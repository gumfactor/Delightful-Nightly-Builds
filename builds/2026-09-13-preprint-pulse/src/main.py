#!/usr/bin/env python3
"""Preprint Pulse CLI — arXiv trend analysis + research-digest drafting.

Usage:
    python src/main.py digest --topic "affective neuroscience of empathy"
    python src/main.py trend --topic "large language model agents" --months 12
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from arxiv_client import ArxivClientError, fetch_papers
from ai_writer import draft_sections
from outline_builder import build_outline
from report import render_html, render_markdown, slugify
from trend_engine import compute_trend, rising_keywords


def _split_categories(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    return [c.strip() for c in raw.split(",") if c.strip()]


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--topic", required=True, help="Research topic to search arXiv for")
    parser.add_argument(
        "--categories",
        default=None,
        help='Comma-separated arXiv category codes to filter to, e.g. "q-bio.NC,cs.AI"',
    )
    parser.add_argument("--months", type=int, default=18, help="Trailing window size in months (default: 18)")
    parser.add_argument("--max-results", type=int, default=150, help="Max papers to fetch (default: 150)")
    parser.add_argument("--out", default="./output", help="Output directory (default: ./output)")
    parser.add_argument("--no-cache", action="store_true", help="Skip the local response cache")
    parser.add_argument(
        "--cache-ttl-hours", type=int, default=24, help="Cache freshness window in hours (default: 24)"
    )


def _fetch(args: argparse.Namespace) -> list:
    out_dir = Path(args.out)
    cache_dir = out_dir / "cache"
    try:
        return fetch_papers(
            topic=args.topic,
            categories=_split_categories(args.categories),
            months=args.months,
            max_results=args.max_results,
            cache_dir=cache_dir,
            cache_ttl_hours=args.cache_ttl_hours,
            use_cache=not args.no_cache,
        )
    except ArxivClientError as exc:
        print(f"error: could not fetch from arXiv: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_digest(args: argparse.Namespace) -> None:
    papers = _fetch(args)
    outline = build_outline(papers, args.topic, args.months)

    api_key = os.environ.get("ANTHROPIC_API_KEY") if args.ai else None
    draft = draft_sections(outline, api_key=api_key)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(args.topic)

    md_path = out_dir / f"{slug}.md"
    html_path = out_dir / f"{slug}.html"
    md_path.write_text(render_markdown(outline, draft), encoding="utf-8")
    html_path.write_text(render_html(outline, draft), encoding="utf-8")

    print(f"{outline.total_papers} papers analyzed for \"{args.topic}\"")
    print(f"trend: {outline.trend.direction} (draft source: {draft.source})")
    print(f"markdown draft: {md_path}")
    print(f"html report:    {html_path}")


def cmd_trend(args: argparse.Namespace) -> None:
    papers = _fetch(args)
    now = datetime.now(timezone.utc).date()
    trend = compute_trend(papers, args.months, now)
    keywords = rising_keywords(papers, args.months, now)

    print(f'Topic: "{args.topic}"  ({len(papers)} papers, {args.months}-month window)')
    print(f"Direction: {trend.direction}  (slope: {trend.slope:+.3f} papers/month)")
    if trend.pct_change is not None:
        print(
            f"First half -> second half: {trend.first_half_count} -> "
            f"{trend.second_half_count} ({trend.pct_change:+.1f}%)"
        )
    else:
        print(f"First half -> second half: {trend.first_half_count} -> {trend.second_half_count}")
    print("Rising keywords:", ", ".join(keywords) if keywords else "(none detected)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="preprint-pulse", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    digest_parser = subparsers.add_parser("digest", help="Fetch, analyze, and draft a full digest")
    _add_common_args(digest_parser)
    digest_parser.add_argument(
        "--ai", action="store_true", help="Attempt a Claude Haiku drafting pass (requires ANTHROPIC_API_KEY)"
    )
    digest_parser.set_defaults(func=cmd_digest)

    trend_parser = subparsers.add_parser("trend", help="Quick terminal-only trend check, no draft written")
    _add_common_args(trend_parser)
    trend_parser.set_defaults(func=cmd_trend)

    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
