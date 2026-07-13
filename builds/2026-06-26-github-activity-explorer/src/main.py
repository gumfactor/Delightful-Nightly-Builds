"""
GitHub Developer Activity Explorer — CLI entry point.

Usage:
    python src/main.py [--months 12] [--output dashboard.html] [--no-ai] [--verbose]

Requires:
    GITHUB_TOKEN  — GitHub personal access token (read:user, repo scope)
    ANTHROPIC_API_KEY — Anthropic API key (skipped if --no-ai)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch GitHub commit history and generate an activity dashboard."
    )
    parser.add_argument(
        "--months",
        type=int,
        default=12,
        help="How many months of history to fetch (default: 12)",
    )
    parser.add_argument(
        "--output",
        default="dashboard.html",
        help="Output HTML file path (default: dashboard.html)",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip AI insights generation",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress to stdout",
    )
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("Error: GITHUB_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    from .fetcher import fetch_all_commits
    from .analyzer import compute_stats
    from .renderer import render_dashboard

    if args.verbose:
        print(f"Fetching last {args.months} months of commit history...")

    try:
        username, commits = fetch_all_commits(
            token=token,
            months=args.months,
            verbose=args.verbose,
        )
    except Exception as exc:
        print(f"Error fetching commits: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"Analysing {len(commits)} commits...")

    stats = compute_stats(commits, username=username, months=args.months)

    insights = ""
    if not args.no_ai:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            print(
                "Warning: ANTHROPIC_API_KEY not set; skipping AI insights.",
                file=sys.stderr,
            )
        else:
            from .ai_insights import generate_insights
            if args.verbose:
                print("Generating AI developer profile...")
            insights = generate_insights(stats, api_key)

    if not insights:
        insights = (
            "AI insights were not generated. "
            "Set ANTHROPIC_API_KEY and re-run without --no-ai."
        )

    output_path = str(Path(args.output).resolve())
    render_dashboard(stats, insights, output_path)

    print(f"Dashboard written to: {output_path}")
    print(
        f"Stats: {stats['total_commits']} commits over {stats['active_days']} active days"
        f" ({args.months} months)"
    )


if __name__ == "__main__":
    main()
