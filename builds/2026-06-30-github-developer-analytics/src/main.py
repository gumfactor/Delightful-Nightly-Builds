"""CLI entry point: fetch GitHub data → aggregate → render HTML dashboard."""

import argparse
import os
import sys
from datetime import timezone, datetime

# Allow running from repo root or from src/
sys.path.insert(0, os.path.dirname(__file__))

from github_client import GitHubClient
from analytics import aggregate
from renderer import render_dashboard


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a GitHub Developer Analytics HTML dashboard.",
    )
    parser.add_argument(
        "--output",
        default="dashboard.html",
        help="Output HTML file path (default: dashboard.html)",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=12,
        help="Number of months of history to analyse (default: 12)",
    )
    parser.add_argument(
        "--max-repos",
        type=int,
        default=50,
        help="Maximum number of repos to include (default: 50)",
    )
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("ERROR: GITHUB_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    client = GitHubClient(token=token)

    print("Fetching authenticated user…")
    user = client.get_authenticated_user()
    login = user.get("login", "")
    if not login:
        print("ERROR: Could not determine GitHub username.", file=sys.stderr)
        sys.exit(1)
    print(f"  User: {login}")

    print(f"Fetching repos (up to {args.max_repos})…")
    repos = client.get_repos(max_repos=args.max_repos)
    print(f"  Found {len(repos)} repos")

    since_iso = client.build_since_iso(args.months)
    print(f"Fetching commits since {since_iso[:10]}…")

    commits_by_repo: dict[str, list[datetime]] = {}
    languages_by_repo: dict[str, dict[str, int]] = {}

    for i, repo in enumerate(repos):
        name = repo["name"]
        owner = repo["owner"]["login"]
        print(f"  [{i + 1}/{len(repos)}] {name}", end="\r", flush=True)

        raw_commits = client.get_commits(owner, name, login, since_iso)
        datetimes = []
        for commit in raw_commits:
            dt = client.parse_commit_timestamp(commit)
            if dt is not None:
                datetimes.append(dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt)
        commits_by_repo[name] = datetimes

        lang_data = client.get_languages(owner, name)
        if lang_data:
            languages_by_repo[name] = lang_data

    print()
    total = sum(len(v) for v in commits_by_repo.values())
    print(f"  {total} commits collected across {len(repos)} repos")

    print("Aggregating analytics…")
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = aggregate(
        commits_by_repo,
        languages_by_repo,
        months_back=args.months,
        generated_at=generated_at,
    )

    print(f"Rendering dashboard → {args.output}")
    render_dashboard(payload, args.output)
    print(f"Done. Open {args.output} in your browser.")


if __name__ == "__main__":
    main()
