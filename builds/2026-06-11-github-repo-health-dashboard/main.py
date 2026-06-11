#!/usr/bin/env python3
"""GitHub Repository Health Dashboard — entry point."""
import argparse
import os
import sys

from src.github_client import fetch_repos
from src.health import enrich_repos, filter_repos
from src.formatter import format_table, format_json


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Show a health dashboard for your GitHub repositories.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Requires GITHUB_TOKEN environment variable.\n"
            "\n"
            "Examples:\n"
            "  python3 main.py                          # top 30 repos, table output\n"
            "  python3 main.py --limit 10               # show 10 repos\n"
            "  python3 main.py --include-archived       # include archived repos\n"
            "  python3 main.py --format json            # JSON output for scripting\n"
            "  python3 main.py --org my-org --limit 50  # list an organisation's repos\n"
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=30,
        metavar="N",
        help="Maximum number of repositories to display (default: 30)",
    )
    parser.add_argument(
        "--include-archived",
        action="store_true",
        default=False,
        help="Include archived repositories (excluded by default)",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        dest="output_format",
        help="Output format: table (default) or json",
    )
    parser.add_argument(
        "--org",
        metavar="ORG",
        default=None,
        help="List repos for a GitHub organisation instead of your account",
    )

    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("Error: GITHUB_TOKEN environment variable is not set.", file=sys.stderr)
        print("Set it with: export GITHUB_TOKEN=ghp_yourtoken", file=sys.stderr)
        return 1

    try:
        raw_repos = fetch_repos(token, limit=args.limit, org=args.org)
    except RuntimeError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    repos = enrich_repos(raw_repos)
    repos = filter_repos(repos, include_archived=args.include_archived)

    if args.output_format == "json":
        print(format_json(repos))
    else:
        print(format_table(repos))

    return 0


if __name__ == "__main__":
    sys.exit(main())
