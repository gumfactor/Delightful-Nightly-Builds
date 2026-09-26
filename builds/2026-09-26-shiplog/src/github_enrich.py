"""Optional GitHub PR-title/label enrichment for merge commits.

Zero network calls unless both a GitHub token and --repo are supplied. Callers
inject `http_get` in tests; the default implementation is the only place that
touches the network.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Callable, Optional

from classify import Commit, _keyword_classify

LABEL_TYPE_MAP = {
    "bug": "fix",
    "bugfix": "fix",
    "enhancement": "feat",
    "feature": "feat",
    "documentation": "docs",
    "docs": "docs",
    "performance": "perf",
    "refactor": "refactor",
    "chore": "chore",
    "dependencies": "chore",
}
BREAKING_LABELS = {"breaking", "breaking-change"}

HttpGet = Callable[[str, dict], tuple[int, Optional[dict]]]


def default_http_get(url: str, headers: dict) -> tuple[int, Optional[dict]]:
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read()
            return response.status, json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return 0, None


def _classify_from_labels(labels: list[str], title: str) -> tuple[str, bool]:
    breaking = any(label.lower() in BREAKING_LABELS for label in labels)
    for label in labels:
        mapped = LABEL_TYPE_MAP.get(label.lower())
        if mapped:
            return mapped, breaking
    return _keyword_classify(title), breaking


def enrich_with_github(
    commits: list[Commit],
    repo: str | None,
    token: str | None,
    http_get: HttpGet = default_http_get,
) -> list[Commit]:
    if not repo or not token:
        return commits

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "shiplog",
    }

    enriched: list[Commit] = []
    for commit in commits:
        if commit.pr_number is None:
            enriched.append(commit)
            continue
        url = f"https://api.github.com/repos/{repo}/pulls/{commit.pr_number}"
        status, data = http_get(url, headers)
        if status != 200 or not data or "title" not in data:
            enriched.append(commit)
            continue
        title = data["title"]
        labels = [label.get("name", "") for label in data.get("labels", []) if isinstance(label, dict)]
        new_type, breaking = _classify_from_labels(labels, title)
        enriched.append(
            Commit(
                sha=commit.sha,
                subject=title,
                body=commit.body,
                author_date=commit.author_date,
                type=new_type,
                scope=commit.scope,
                breaking=commit.breaking or breaking,
                pr_number=commit.pr_number,
                source="github-pr",
                raw_subject=commit.raw_subject,
            )
        )
    return enriched
