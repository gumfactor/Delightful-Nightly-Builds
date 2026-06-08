#!/usr/bin/env python3
"""Git Standup Reporter — daily digest of pushed and unpushed commits."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.config import load_config
from src.github_api import get_user_repos, get_commits_since as github_get_commits
from src.local_git import find_git_repos, get_repo_name, get_unpushed_commits
from src.dedup import merge_commits
from src.journal import append_entry
from src.standup import format_standup


def main() -> None:
    config_path = Path(__file__).parent / "standup.toml"
    cfg = load_config(config_path)

    hours: int = cfg["hours"]
    fmt: str = cfg["format"]
    username: str = cfg["github_username"]
    exclude: list[str] = cfg["exclude_repos"]
    journal_path: str = cfg["journal_path"]
    local_roots: list[str] = cfg["local_roots"]
    token: str = os.environ.get("GITHUB_TOKEN", "")

    # --- GitHub: all repos, all pushed commits in window ---
    github_by_repo: dict = {}
    if username and token:
        try:
            repos = get_user_repos(username, token, exclude)
            for repo in repos:
                commits = github_get_commits(username, repo, token, hours)
                if commits:
                    github_by_repo[repo] = commits
        except Exception as exc:
            print(f"Warning: GitHub API error — {exc}", file=sys.stderr)
    elif username and not token:
        print("Warning: GITHUB_TOKEN not set — skipping GitHub API.", file=sys.stderr)

    # --- Local: scan roots, get unpushed commits only ---
    local_by_repo: dict = {}
    if local_roots:
        for path in find_git_repos(local_roots):
            name = get_repo_name(path)
            if name in exclude:
                continue
            commits = get_unpushed_commits(path, hours)
            if commits:
                local_by_repo[name] = commits

    # --- Merge and deduplicate by SHA ---
    combined = merge_commits(github_by_repo, local_by_repo)

    output = format_standup(combined, hours, fmt)
    print(output, end="")

    # --- Append to JSONL journal ---
    if journal_path:
        try:
            append_entry(journal_path, combined, hours, output)
        except Exception as exc:
            print(f"Warning: Could not write journal — {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
