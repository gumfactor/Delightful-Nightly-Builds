"""GitHub activity fetcher — repos, recent pushes, open PRs, stale detection."""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

GITHUB_API = "https://api.github.com"


def _get(path: str, token: str) -> Any:
    url = f"{GITHUB_API}{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def _get_paginated(path: str, token: str) -> list:
    results: list = []
    page = 1
    while True:
        sep = "&" if "?" in path else "?"
        data = _get(f"{path}{sep}per_page=100&page={page}", token)
        if not data:
            break
        results.extend(data)
        if len(data) < 100:
            break
        page += 1
    return results


def classify_repo_health(pushed_at: str | None, stale_days: int = 7) -> str:
    """Return 'active', 'recent', 'stale', or 'unknown' based on last push date."""
    if not pushed_at:
        return "unknown"
    try:
        pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    except ValueError:
        return "unknown"
    age_days = (datetime.now(timezone.utc) - pushed).days
    if age_days <= 1:
        return "active"
    if age_days <= stale_days:
        return "recent"
    return "stale"


def filter_recent_repos(repos: list[dict], hours: int = 24) -> list[dict]:
    """Return repos pushed to within the last N hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    result = []
    for repo in repos:
        pushed_at = repo.get("pushed_at")
        if not pushed_at:
            continue
        try:
            pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            if pushed >= cutoff:
                result.append(repo)
        except ValueError:
            pass
    return result


def fetch_github_activity(
    token: str,
    stale_days: int = 7,
    lookback_hours: int = 24,
) -> dict:
    """Fetch repos, recent activity, stale repos, and open PRs. Degrades gracefully."""
    if not token:
        return {
            "error": "GITHUB_TOKEN not set",
            "repos": [],
            "recent_repos": [],
            "stale_repos": [],
            "open_prs": [],
        }

    try:
        repos = _get_paginated("/user/repos?type=all&sort=pushed", token)
    except Exception as exc:
        return {
            "error": str(exc),
            "repos": [],
            "recent_repos": [],
            "stale_repos": [],
            "open_prs": [],
        }

    non_archived = [r for r in repos if not r.get("archived", False)]
    recent = filter_recent_repos(non_archived, hours=lookback_hours)
    stale = [
        r for r in non_archived
        if classify_repo_health(r.get("pushed_at"), stale_days) == "stale"
    ]

    open_prs: list[dict] = []
    for repo in recent[:10]:
        full_name = repo.get("full_name", "")
        if "/" not in full_name:
            continue
        owner, name = full_name.split("/", 1)
        try:
            prs = _get(f"/repos/{owner}/{name}/pulls?state=open&per_page=10", token)
            for pr in prs:
                open_prs.append({
                    "repo": full_name,
                    "number": pr.get("number"),
                    "title": pr.get("title", ""),
                    "user": pr.get("user", {}).get("login", ""),
                    "updated_at": pr.get("updated_at", ""),
                })
        except Exception:
            pass

    return {
        "total_repos": len(non_archived),
        "recent_repos": [
            {
                "name": r.get("full_name", ""),
                "pushed_at": r.get("pushed_at", ""),
                "open_issues": r.get("open_issues_count", 0),
                "health": classify_repo_health(r.get("pushed_at"), stale_days),
            }
            for r in recent
        ],
        "stale_repos": [
            {
                "name": r.get("full_name", ""),
                "pushed_at": r.get("pushed_at", ""),
                "open_issues": r.get("open_issues_count", 0),
            }
            for r in stale
        ],
        "open_prs": open_prs,
    }
