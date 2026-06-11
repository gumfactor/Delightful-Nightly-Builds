"""
Pure logic functions for repo parsing, health scoring, filtering, and enrichment.
No I/O — all functions are deterministic and testable without network or filesystem access.
"""
from datetime import datetime, timezone
from typing import Optional


def parse_repo(raw: dict) -> dict:
    """Extract and normalise relevant fields from a raw GitHub API repo object."""
    return {
        "name": raw.get("name", "unknown"),
        "full_name": raw.get("full_name", ""),
        "language": raw.get("language") or "—",
        "stars": raw.get("stargazers_count", 0),
        "open_issues": raw.get("open_issues_count", 0),
        "pushed_at": raw.get("pushed_at") or "",
        "archived": bool(raw.get("archived", False)),
        "private": bool(raw.get("private", False)),
        "html_url": raw.get("html_url", ""),
    }


def days_since_push(pushed_at: str, now: Optional[datetime] = None) -> int:
    """
    Return integer days elapsed since pushed_at (ISO 8601 UTC timestamp).
    Returns 9999 if pushed_at is empty (sentinel meaning "unknown/never").
    Accepts an optional `now` for deterministic testing.
    """
    if not pushed_at:
        return 9999
    if now is None:
        now = datetime.now(timezone.utc)
    pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    return (now - pushed).days


def health_status(repo: dict, now: Optional[datetime] = None) -> str:
    """
    Return a health label for the repo:
      archived  — repo is archived (overrides activity)
      active    — pushed within the last 30 days
      quiet     — pushed 30–90 days ago
      stale     — pushed more than 90 days ago
    """
    if repo.get("archived"):
        return "archived"
    days = days_since_push(repo.get("pushed_at", ""), now=now)
    if days < 30:
        return "active"
    elif days <= 90:
        return "quiet"
    return "stale"


def filter_repos(repos: list[dict], include_archived: bool = False) -> list[dict]:
    """Return repos list with archived repos removed unless include_archived is True."""
    if include_archived:
        return list(repos)
    return [r for r in repos if not r.get("archived", False)]


def enrich_repos(raw_repos: list[dict], now: Optional[datetime] = None) -> list[dict]:
    """
    Parse raw GitHub API responses and attach computed fields.
    Returns a new list; does not mutate inputs.
    """
    result = []
    for raw in raw_repos:
        repo = parse_repo(raw)
        repo["days_since_push"] = days_since_push(repo["pushed_at"], now=now)
        repo["health"] = health_status(repo, now=now)
        result.append(repo)
    return result
