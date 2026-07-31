"""Tests for fetcher.py — GitHub API client and response parsing."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fetcher import filter_repos_with_recent_push, group_runs_by_workflow


def _repo(pushed_days_ago: int, archived: bool = False, name: str = "repo") -> dict:
    pushed_at = (datetime.now(timezone.utc) - timedelta(days=pushed_days_ago)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    return {"name": name, "pushed_at": pushed_at, "archived": archived, "owner": {"login": "user"}}


def test_filter_repos_with_recent_push_includes_recent():
    repos = [_repo(5, name="recent"), _repo(40, name="old")]
    result = filter_repos_with_recent_push(repos, since_days=30)
    assert len(result) == 1
    assert result[0]["name"] == "recent"


def test_filter_repos_excludes_archived():
    repos = [_repo(5, archived=True, name="archived"), _repo(5, name="live")]
    result = filter_repos_with_recent_push(repos, since_days=30)
    assert len(result) == 1
    assert result[0]["name"] == "live"


def test_filter_repos_empty_input():
    assert filter_repos_with_recent_push([], since_days=30) == []


def test_filter_repos_missing_pushed_at():
    repos = [{"name": "no-date", "archived": False, "owner": {"login": "user"}}]
    result = filter_repos_with_recent_push(repos, since_days=30)
    assert result == []


def test_filter_repos_exactly_on_boundary():
    # pushed exactly 30 days ago should be included (>= cutoff)
    pushed_at = (datetime.now(timezone.utc) - timedelta(days=30, seconds=-1)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    repos = [{"name": "boundary", "pushed_at": pushed_at, "archived": False, "owner": {"login": "u"}}]
    result = filter_repos_with_recent_push(repos, since_days=30)
    assert len(result) == 1


def test_group_runs_by_workflow_basic():
    runs = [
        {"name": "CI", "id": 1, "status": "completed"},
        {"name": "CI", "id": 2, "status": "completed"},
        {"name": "Deploy", "id": 3, "status": "completed"},
    ]
    groups = group_runs_by_workflow(runs)
    assert "CI" in groups
    assert "Deploy" in groups
    assert len(groups["CI"]) == 2
    assert len(groups["Deploy"]) == 1


def test_group_runs_by_workflow_empty():
    assert group_runs_by_workflow([]) == {}


def test_group_runs_by_workflow_missing_name_uses_workflow_id():
    runs = [{"workflow_id": 99, "id": 1, "status": "completed"}]
    groups = group_runs_by_workflow(runs)
    assert "99" in groups


def test_group_runs_by_workflow_preserves_all_fields():
    runs = [{"name": "CI", "id": 42, "conclusion": "success", "created_at": "2024-01-01T00:00:00Z"}]
    groups = group_runs_by_workflow(runs)
    assert groups["CI"][0]["id"] == 42
    assert groups["CI"][0]["conclusion"] == "success"
