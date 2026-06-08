#!/usr/bin/env python3
"""Git Standup Reporter — summarise recent commits across one or more git repos."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.git_log import get_commits_since, get_default_author, get_repo_name
from src.standup import format_standup


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Summarise recent git commits as a standup report. "
            "Defaults to the current directory and the last 24 hours."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Git repository paths to scan (default: current directory)",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="How many hours back to look (default: 24)",
    )
    parser.add_argument(
        "--author",
        default=None,
        help="Filter commits by author name substring",
    )
    parser.add_argument(
        "--all-authors",
        action="store_true",
        help="Include commits from all authors, skipping the author filter",
    )
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["text", "markdown"],
        default="text",
        help="Output format: text (default) or markdown",
    )

    args = parser.parse_args()

    # Determine author filter: explicit > auto-detected > none (all-authors)
    author: str = ""
    if not args.all_authors:
        if args.author:
            author = args.author
        else:
            for path in args.paths:
                detected = get_default_author(path)
                if detected:
                    author = detected
                    break

    # Collect commits from each path, grouped by repository name
    commits_by_repo: dict = {}
    for path in args.paths:
        name = get_repo_name(path)
        commits = get_commits_since(path, args.hours, author or None)
        commits_by_repo[name] = commits

    output = format_standup(commits_by_repo, args.hours, args.fmt)
    print(output, end="")


if __name__ == "__main__":
    main()
