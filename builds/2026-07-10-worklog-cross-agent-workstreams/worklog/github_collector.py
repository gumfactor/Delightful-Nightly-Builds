"""GitHub issues + pull requests collector via the REST API (urllib, no SDK dependency)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Optional

API_BASE = "https://api.github.com"
USER_AGENT = "worklog-cross-agent-workstreams/1.0"


@dataclass
class GitHubItem:
    kind: str  # "issue" or "pr"
    number: int
    title: str
    state: str  # "open" or "closed"
    merged: bool
    url: str
    updated_at: str
    body: str = ""


@dataclass
class GitHubResult:
    skipped: bool
    reason: str = ""
    items: list = field(default_factory=list)


def _request(url: str, token: str) -> list:
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", USER_AGENT)
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def collect_github_activity(
    owner: str,
    repo: str,
    token: Optional[str] = None,
    per_page: int = 50,
) -> GitHubResult:
    """Fetch issues and PRs for owner/repo. Degrades gracefully instead of raising."""
    token = token if token is not None else os.environ.get("GITHUB_TOKEN", "")
    if not token:
        return GitHubResult(skipped=True, reason="GITHUB_TOKEN not set; git-only mode")

    items: list[GitHubItem] = []

    try:
        issues_raw = _request(
            f"{API_BASE}/repos/{owner}/{repo}/issues?state=all&per_page={per_page}", token
        )
    except urllib.error.HTTPError as exc:
        return GitHubResult(skipped=True, reason=f"GitHub API error {exc.code}: {exc.reason}")
    except urllib.error.URLError as exc:
        return GitHubResult(skipped=True, reason=f"GitHub API unreachable: {exc.reason}")

    for raw in issues_raw:
        if "pull_request" in raw:
            continue  # handled by the /pulls call below
        items.append(
            GitHubItem(
                kind="issue",
                number=raw["number"],
                title=raw.get("title", ""),
                state=raw.get("state", "open"),
                merged=False,
                url=raw.get("html_url", ""),
                updated_at=raw.get("updated_at", ""),
                body=raw.get("body") or "",
            )
        )

    try:
        prs_raw = _request(
            f"{API_BASE}/repos/{owner}/{repo}/pulls?state=all&per_page={per_page}", token
        )
    except (urllib.error.HTTPError, urllib.error.URLError):
        prs_raw = []

    for raw in prs_raw:
        items.append(
            GitHubItem(
                kind="pr",
                number=raw["number"],
                title=raw.get("title", ""),
                state=raw.get("state", "open"),
                merged=bool(raw.get("merged_at")),
                url=raw.get("html_url", ""),
                updated_at=raw.get("updated_at", ""),
                body=raw.get("body") or "",
            )
        )

    return GitHubResult(skipped=False, items=items)
