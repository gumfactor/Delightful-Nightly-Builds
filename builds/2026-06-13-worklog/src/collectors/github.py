"""
GitHub activity collector — fetches issues, pull requests, and releases from
the GitHub REST API using GITHUB_TOKEN.  Degrades gracefully when the token
is absent or the remote is not a GitHub repository.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional

from src.ledger import make_event_id


def _extract_github_owner_repo(git_root: Path) -> Optional[tuple[str, str]]:
    """Parse owner/repo from the origin remote URL. Returns None if not GitHub."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=str(git_root),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None
        url = result.stdout.strip()
    except Exception:
        return None

    # Match HTTPS: https://github.com/owner/repo(.git)?
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", url)
    if m:
        return m.group(1), m.group(2)

    # Match SSH: git@github.com:owner/repo(.git)?
    m = re.match(r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", url)
    if m:
        return m.group(1), m.group(2)

    return None


def _github_get(path: str, token: str) -> Any:
    """
    GET from the GitHub API.  Raises urllib.error.HTTPError on failure.
    Returns parsed JSON.
    """
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def _collect_issues(
    owner: str,
    repo: str,
    token: str,
    project_id: str,
    since: Optional[str] = None,
) -> list[dict]:
    """Fetch recent issues and return ledger-ready event dicts."""
    params = "?state=all&per_page=50&sort=updated&direction=desc"
    if since:
        params += f"&since={since}"
    try:
        items = _github_get(f"/repos/{owner}/{repo}/issues{params}", token)
    except Exception:
        return []

    events = []
    for item in items:
        if item.get("pull_request"):
            continue  # PRs appear in issues endpoint too; skip here
        number = item["number"]
        event_id = make_event_id("github", f"issue:{number}", "issue")
        events.append(
            {
                "id": event_id,
                "timestamp": item.get("updated_at") or item.get("created_at", ""),
                "project_id": project_id,
                "type": "issue",
                "actor_kind": "human",
                "actor_name": (item.get("user") or {}).get("login"),
                "summary": f"#{number}: {item.get('title', '')}",
                "status": item.get("state", "unknown"),
                "provider": "github",
                "source_ref": str(number),
                "source_url": item.get("html_url"),
                "metadata": {
                    "number": number,
                    "labels": [lb["name"] for lb in item.get("labels", [])],
                    "body_excerpt": (item.get("body") or "")[:200],
                },
            }
        )
    return events


def _collect_pull_requests(
    owner: str,
    repo: str,
    token: str,
    project_id: str,
) -> list[dict]:
    """Fetch recent pull requests and return ledger-ready event dicts."""
    try:
        items = _github_get(
            f"/repos/{owner}/{repo}/pulls?state=all&per_page=30&sort=updated&direction=desc",
            token,
        )
    except Exception:
        return []

    events = []
    for item in items:
        number = item["number"]
        event_id = make_event_id("github", f"pr:{number}", "pull_request")

        # Determine status
        if item.get("merged_at"):
            status = "merged"
        elif item.get("state") == "closed":
            status = "closed"
        else:
            status = "open"

        events.append(
            {
                "id": event_id,
                "timestamp": item.get("updated_at") or item.get("created_at", ""),
                "project_id": project_id,
                "type": "pull_request",
                "actor_kind": "human",
                "actor_name": (item.get("user") or {}).get("login"),
                "summary": f"PR #{number}: {item.get('title', '')}",
                "status": status,
                "provider": "github",
                "source_ref": str(number),
                "source_url": item.get("html_url"),
                "metadata": {
                    "number": number,
                    "base_branch": (item.get("base") or {}).get("ref"),
                    "head_branch": (item.get("head") or {}).get("ref"),
                    "head_sha": (item.get("head") or {}).get("sha"),
                    "merged_at": item.get("merged_at"),
                    "draft": item.get("draft", False),
                },
            }
        )
    return events


def collect_github_events(
    git_root: Path,
    project_id: str,
    token: Optional[str] = None,
    since: Optional[str] = None,
) -> tuple[list[dict], bool]:
    """
    Collect GitHub events (issues + PRs).  Returns (events, github_available).

    Gracefully returns an empty list when:
    - No GITHUB_TOKEN is available
    - The remote is not a GitHub repository
    - The API call fails
    """
    resolved_token = token or os.environ.get("GITHUB_TOKEN")
    if not resolved_token:
        return [], False

    owner_repo = _extract_github_owner_repo(git_root)
    if owner_repo is None:
        return [], False

    owner, repo = owner_repo
    issues = _collect_issues(owner, repo, resolved_token, project_id, since)
    prs = _collect_pull_requests(owner, repo, resolved_token, project_id)
    return issues + prs, True
