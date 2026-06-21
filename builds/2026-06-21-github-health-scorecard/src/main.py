#!/usr/bin/env python3
import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ai_summary import generate_insights
from github_client import get_latest_ci_run, list_repos
from report import render_html
from scorer import enrich_repo


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a GitHub Repository Health Scorecard HTML dashboard."
    )
    parser.add_argument(
        "--output",
        default="github_health_report.html",
        help="Output HTML file path (default: github_health_report.html)",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip AI insights even if ANTHROPIC_API_KEY is set",
    )
    parser.add_argument(
        "--max-repos",
        type=int,
        default=0,
        help="Limit repos fetched for testing (0 = no limit)",
    )
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("Error: GITHUB_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    api_key = "" if args.no_ai else os.environ.get("ANTHROPIC_API_KEY", "")

    print("Fetching repositories…", flush=True)
    raw_repos = list_repos(token)
    if args.max_repos:
        raw_repos = raw_repos[: args.max_repos]

    active_repos = [r for r in raw_repos if not r.get("archived", False)]
    print(f"  {len(raw_repos)} repos found, {len(active_repos)} active", flush=True)

    now = datetime.now(timezone.utc)
    owner = raw_repos[0]["owner"]["login"] if raw_repos else ""

    enriched: list[dict] = []
    print("Fetching CI status…", flush=True)
    for i, repo in enumerate(active_repos, 1):
        ci_run = get_latest_ci_run(owner, repo["name"], token)
        enriched.append(enrich_repo(repo, ci_run, now))
        if i % 10 == 0:
            print(f"  {i}/{len(active_repos)} done", flush=True)

    enriched.sort(key=lambda r: r["health_score"])

    ai_insights = ""
    if api_key:
        print("Generating AI insights…", flush=True)
        ai_insights = generate_insights(enriched, api_key)
        if ai_insights:
            print("  AI insights generated.", flush=True)
        else:
            print("  AI insights unavailable (API unreachable or key invalid).", flush=True)

    generated_at = now.strftime("%Y-%m-%d %H:%M UTC")
    html = render_html(enriched, generated_at, ai_insights)

    out_path = Path(args.output)
    out_path.write_text(html, encoding="utf-8")
    print(f"\nReport written to: {out_path.resolve()}")
    print(f"Open in browser: file://{out_path.resolve()}")


if __name__ == "__main__":
    main()
