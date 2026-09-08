"""Secrets Sentinel CLI — walk git history for committed credentials.

Usage:
    python -m src.main <path> [<path> ...] [options]

Each <path> is either a repo (contains .git) or a directory to search for
repos under. See Manual.md for the full option reference.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from src.classifier import Finding, build_findings, classify_with_ai
from src.report import render_html, render_json, render_terminal
from src.scanner import discover_repos, scan_repo


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="secrets-sentinel",
        description="Scan git commit history for committed credentials.",
    )
    parser.add_argument("paths", nargs="+", help="Repo path(s) or directory/directories to search for repos under")
    parser.add_argument(
        "--current-branch-only",
        action="store_true",
        help="Scan only the checked-out branch instead of all local branches",
    )
    parser.add_argument("--max-commits", type=int, default=None, help="Cap commits scanned per repo")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI triage even if ANTHROPIC_API_KEY is set")
    parser.add_argument("--html-out", type=Path, default=None, help="Write an HTML report to this path")
    parser.add_argument("--json-out", type=Path, default=None, help="Write a JSON report to this path")
    parser.add_argument(
        "--fail-on-high",
        action="store_true",
        help="Exit with status 1 if any high-confidence finding exists (for CI gating)",
    )
    return parser


def resolve_repos(paths: list[str]) -> list[Path]:
    repos: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if (path / ".git").exists():
            repos.append(path)
        else:
            repos.extend(discover_repos(path))
    # De-duplicate while preserving order.
    seen: set[Path] = set()
    unique_repos = []
    for repo in repos:
        resolved = repo.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_repos.append(repo)
    return unique_repos


def run_scan(
    paths: list[str],
    all_branches: bool = True,
    max_commits: int | None = None,
    use_ai: bool = True,
    ai_client: object | None = None,
) -> list[Finding]:
    """Scan every discovered repo and return all findings, with AI triage applied."""
    all_findings: list[Finding] = []
    for repo_path in resolve_repos(paths):
        hits = scan_repo(repo_path, all_branches=all_branches, max_commits=max_commits)
        all_findings.extend(build_findings(hits, repo_path))

    client = ai_client if use_ai else None
    classify_with_ai(all_findings, client=client)
    return all_findings


def _make_anthropic_client():
    import anthropic

    return anthropic.Anthropic()


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    ai_client = None
    if not args.no_ai and os.environ.get("ANTHROPIC_API_KEY"):
        ai_client = _make_anthropic_client()

    findings = run_scan(
        args.paths,
        all_branches=not args.current_branch_only,
        max_commits=args.max_commits,
        use_ai=not args.no_ai,
        ai_client=ai_client,
    )

    print(render_terminal(findings))

    if args.html_out:
        render_html(findings, args.html_out)
        print(f"\nHTML report written to {args.html_out}")
    if args.json_out:
        render_json(findings, args.json_out)
        print(f"JSON report written to {args.json_out}")

    if args.fail_on_high and any(f.tier == "high" for f in findings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
