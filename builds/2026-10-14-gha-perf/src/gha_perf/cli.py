"""Command-line entry point."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import ai
from .analyze import analyze
from .api import GitHubClient, GitHubError, Transport, urllib_transport
from .collect import collect, list_repos
from .render import render_html


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gha-perf", description="Analyse GitHub Actions performance across repos.")
    parser.add_argument("--repos", help="comma-separated owner/name list (default: all repos you can access)")
    parser.add_argument("--days", type=int, default=30, help="look-back window in days (default 30)")
    parser.add_argument("--max-runs", type=int, default=300, help="max runs fetched per repo (default 300)")
    parser.add_argument("--jobs-per-workflow", type=int, default=15, help="runs per workflow to fetch job/step detail for (default 15)")
    parser.add_argument("--include-forks", action="store_true")
    parser.add_argument("--ai", action="store_true", help="add a Claude briefing (needs ANTHROPIC_API_KEY)")
    parser.add_argument("-o", "--output", default="gha-perf-report.html", help="HTML output path")
    parser.add_argument("--json", dest="json_path", help="also write the analysis as JSON")
    return parser


def run(argv: list[str], env: dict[str, str] | None = None, transport: Transport = urllib_transport,
        ai_post: ai.Post = ai._urllib_post) -> int:
    args = build_parser().parse_args(argv)
    env = os.environ if env is None else env
    if args.days < 1 or args.max_runs < 1 or args.jobs_per_workflow < 0:
        print("error: --days and --max-runs must be >= 1, --jobs-per-workflow >= 0", file=sys.stderr)
        return 2
    token = env.get("GITHUB_TOKEN") or env.get("GH_TOKEN")
    if not token:
        print("error: set GITHUB_TOKEN (needs repo + actions:read scope)", file=sys.stderr)
        return 2

    client = GitHubClient(token, transport)
    log = lambda message: print(message, file=sys.stderr)  # noqa: E731
    try:
        repos = [r.strip() for r in args.repos.split(",") if r.strip()] if args.repos else list_repos(client, args.include_forks)
    except GitHubError as error:
        print(f"error: could not list repositories: {error}", file=sys.stderr)
        return 1
    if not repos:
        print("error: no repositories to analyse", file=sys.stderr)
        return 1

    runs, errors = collect(client, repos, args.days, args.max_runs, args.jobs_per_workflow, log=log)
    report = analyze(runs, args.days, errors=errors)

    summary = None
    if args.ai:
        summary = ai.summarize(report, env.get("ANTHROPIC_API_KEY"), ai_post)
        if summary is None:
            log("AI briefing unavailable (no ANTHROPIC_API_KEY or request failed); continuing without it")

    Path(args.output).write_text(render_html(report, summary), encoding="utf-8")
    if args.json_path:
        Path(args.json_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
    stats = report["summary"]
    print(f"{stats['runs']} runs across {stats['repos']} repos, {stats['wasted_min']:.0f} wasted min "
          f"({stats['wasted_pct']:.0%}); {len(report['findings'])} findings -> {args.output} [{client.requests_made} API calls]")
    return 0
