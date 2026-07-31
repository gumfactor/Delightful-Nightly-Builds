"""ci-pulse: GitHub Actions Performance Analyzer CLI."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Make src importable from project root
sys.path.insert(0, str(Path(__file__).parent))

from analyzer import compute_workflow_stats, compute_weekly_trend, compute_global_stats, rank_by_improvement_potential, format_duration
from fetcher import GitHubClient, filter_repos_with_recent_push, group_runs_by_workflow
from ai_insights import get_insights
from renderer import render_html


def build_report(days: int, no_ai: bool, verbose: bool) -> tuple[str, dict, list, list]:
    """Fetch data and build report. Returns (html, global_stats, workflow_stats, weekly_trend)."""
    client = GitHubClient()
    user = client.get_authenticated_user()
    login = user.get("login", "unknown") if user else "unknown"

    if verbose:
        print(f"Fetching repos for @{login}…")

    repos = client.list_repos()
    active_repos = filter_repos_with_recent_push(repos, since_days=days)

    if verbose:
        print(f"  {len(repos)} repos total, {len(active_repos)} active in last {days}d")

    all_workflow_stats: list[dict] = []
    all_runs_for_trend: list[dict] = []

    for repo in active_repos:
        repo_name = repo["name"]
        owner = repo.get("owner", {}).get("login", login)
        full_name = f"{owner}/{repo_name}"

        runs = client.list_workflow_runs(owner, repo_name, since_days=days)
        if not runs:
            continue

        if verbose:
            print(f"  {full_name}: {len(runs)} runs")

        all_runs_for_trend.extend(runs)
        groups = group_runs_by_workflow(runs)
        for wf_name, wf_runs in groups.items():
            stats = compute_workflow_stats(wf_runs, repo=full_name, workflow_name=wf_name)
            if stats["total_runs"] > 0:
                all_workflow_stats.append(stats)

    global_stats = compute_global_stats(all_workflow_stats)
    weekly_trend = compute_weekly_trend(all_runs_for_trend)
    ranked = rank_by_improvement_potential(all_workflow_stats)

    ai_insights = ""
    if not no_ai:
        if verbose:
            print("Generating AI insights…")
        ai_insights = get_insights(global_stats, ranked[:8])

    html = render_html(global_stats, all_workflow_stats, weekly_trend, ai_insights)
    return html, global_stats, all_workflow_stats, weekly_trend


def print_terminal_summary(global_stats: dict, workflow_stats: list) -> None:
    """Print a brief terminal summary after generating the report."""
    print("\n── ci-pulse summary ─────────────────────────────────────────────")
    print(f"  Runs (30d):      {global_stats.get('total_runs', 0)}")
    print(f"  Failures:        {global_stats.get('total_failures', 0)} "
          f"({global_stats.get('overall_failure_rate', 0)*100:.1f}%)")
    print(f"  CI minutes:      {global_stats.get('total_ci_minutes', 0):.0f}")
    print(f"  Repos with CI:   {global_stats.get('repos_with_ci', 0)}")
    if global_stats.get("slowest_workflow"):
        print(f"  Slowest:         {global_stats['slowest_workflow']}")
    if global_stats.get("most_failed_workflow"):
        print(f"  Most failed:     {global_stats['most_failed_workflow']}")

    if workflow_stats:
        top3 = sorted(workflow_stats, key=lambda s: s["avg_duration_s"], reverse=True)[:3]
        print("\n  Top 3 by duration:")
        for s in top3:
            avg = format_duration(s["avg_duration_s"])
            print(f"    {s['repo']}/{s['workflow_name']}: {avg} avg, {s['failure_rate']*100:.0f}% failures")
    print("─────────────────────────────────────────────────────────────────\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ci-pulse — GitHub Actions Performance Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  python src/main.py\n  python src/main.py --days 60 --output report.html",
    )
    parser.add_argument("--days", type=int, default=30, help="Lookback window in days (default: 30)")
    parser.add_argument("--output", default="", help="Output HTML file path (default: ci-pulse-YYYY-MM-DD.html)")
    parser.add_argument("--no-ai", action="store_true", help="Skip Anthropic AI insights")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print progress")
    args = parser.parse_args()

    output_path = args.output or f"ci-pulse-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.html"

    try:
        html_content, global_stats, workflow_stats, weekly_trend = build_report(
            days=args.days,
            no_ai=args.no_ai,
            verbose=args.verbose,
        )
    except EnvironmentError:
        sys.exit(1)

    Path(output_path).write_text(html_content, encoding="utf-8")
    print(f"Report written to: {output_path}")
    print_terminal_summary(global_stats, workflow_stats)


if __name__ == "__main__":
    main()
