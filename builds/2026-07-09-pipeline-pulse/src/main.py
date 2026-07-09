"""Pipeline Pulse — nightly build pipeline health & PR backlog dashboard.

Reconciles builds/index.md against the actual git history of this repo to show
which builds have landed on the default branch versus which are still stuck in
an open branch/PR, then renders a self-contained HTML dashboard.

Usage:
    python3 src/main.py [--repo-path PATH] [--index-path PATH]
                         [--owner OWNER] [--repo REPO] [--output PATH]
                         [--fetch] [--no-ai]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

import ai_brief
import catalog_parser
import git_inspector
import pipeline_stats
import report_html


def build_dashboard(
    repo_path: str,
    index_path: str,
    owner: str | None,
    repo: str | None,
    use_ai: bool,
    today: date,
    do_fetch: bool = False,
) -> tuple[str, pipeline_stats.Summary]:
    if do_fetch:
        subprocess.run(["git", "fetch", "origin"], cwd=repo_path, check=False)

    records = catalog_parser.parse_catalog(index_path)
    default_branch = git_inspector.detect_default_branch(repo_path)

    if owner is None or repo is None:
        detected = git_inspector.detect_owner_repo(repo_path)
        if detected:
            owner, repo = owner or detected[0], repo or detected[1]

    folders_on_default = git_inspector.list_build_folders_at_ref(
        repo_path, f"origin/{default_branch}"
    )
    branches = git_inspector.list_remote_branches(repo_path, default_branch)
    folder_branch_map = git_inspector.build_folder_branch_map(repo_path, default_branch, branches)

    statuses = pipeline_stats.reconcile(records, folders_on_default, folder_branch_map, today)
    summary = pipeline_stats.summarize(statuses)

    brief = ai_brief.deterministic_brief(summary) if not use_ai else ai_brief.generate_brief(summary)

    html = report_html.render(statuses, summary, brief, owner, repo, default_branch)
    return html, summary


def print_text_summary(summary: pipeline_stats.Summary) -> None:
    print(f"Pipeline Pulse — {summary['total']} builds tracked")
    print(f"  Merged:  {summary['merged_count']} ({summary['merged_pct']:.0f}%)")
    print(f"  Backlog: {summary['backlog_count']} ({summary['backlog_pct']:.0f}%)")
    if summary["oldest_unmerged"]:
        o = summary["oldest_unmerged"]
        print(f"  Oldest unmerged: \"{o['title']}\" ({o['date']}, {o['backlog_days']} days)")
    coverage = summary["rating_coverage_pct"]
    avg = summary["average_rating"]
    avg_text = f"{avg:.1f}/10" if avg is not None else "n/a"
    print(f"  Rating coverage: {coverage:.0f}% (avg {avg_text})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-path", default=None, help="Path inside the target git repo (default: cwd)")
    parser.add_argument("--index-path", default=None, help="Path to builds/index.md (default: <repo>/builds/index.md)")
    parser.add_argument("--owner", default=None, help="GitHub owner (auto-detected from origin remote if omitted)")
    parser.add_argument("--repo", default=None, help="GitHub repo name (auto-detected from origin remote if omitted)")
    parser.add_argument("--output", default=None, help="Output HTML path (default: <build folder>/output/pipeline_pulse.html)")
    parser.add_argument("--fetch", action="store_true", help="Run 'git fetch origin' before analyzing")
    parser.add_argument("--no-ai", action="store_true", help="Skip the Anthropic API call and use the deterministic briefing")
    args = parser.parse_args(argv)

    start_path = args.repo_path or str(Path.cwd())
    try:
        repo_path = git_inspector.find_repo_root(start_path)
    except git_inspector.GitError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    index_path = args.index_path or str(Path(repo_path) / "builds" / "index.md")
    output_path = args.output or str(Path(__file__).resolve().parent.parent / "output" / "pipeline_pulse.html")

    try:
        html, summary = build_dashboard(
            repo_path=repo_path,
            index_path=index_path,
            owner=args.owner,
            repo=args.repo,
            use_ai=not args.no_ai,
            today=date.today(),
            do_fetch=args.fetch,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except git_inspector.GitError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(html, encoding="utf-8")

    print_text_summary(summary)
    print(f"\nDashboard written to {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
