"""Tests for github_fetcher.py — repo health, filtering, activity fetch."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from github_fetcher import classify_repo_health, fetch_github_activity, filter_recent_repos


def _hours_ago(hours: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def _days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


# ---------------------------------------------------------------------------
# classify_repo_health
# ---------------------------------------------------------------------------

class TestClassifyRepoHealth:
    def test_active_if_pushed_within_24h(self):
        assert classify_repo_health(_hours_ago(6)) == "active"

    def test_active_if_pushed_2h_ago(self):
        assert classify_repo_health(_hours_ago(2)) == "active"

    def test_recent_if_pushed_3_days_ago(self):
        assert classify_repo_health(_days_ago(3)) == "recent"

    def test_stale_if_pushed_10_days_ago(self):
        assert classify_repo_health(_days_ago(10)) == "stale"

    def test_unknown_for_none(self):
        assert classify_repo_health(None) == "unknown"

    def test_unknown_for_empty_string(self):
        assert classify_repo_health("") == "unknown"

    def test_unknown_for_invalid_date(self):
        assert classify_repo_health("not-a-date") == "unknown"

    def test_handles_z_suffix(self):
        pushed = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        assert classify_repo_health(pushed) == "active"

    def test_custom_stale_days_recent(self):
        assert classify_repo_health(_days_ago(15), stale_days=30) == "recent"

    def test_custom_stale_days_stale(self):
        assert classify_repo_health(_days_ago(15), stale_days=10) == "stale"


# ---------------------------------------------------------------------------
# filter_recent_repos
# ---------------------------------------------------------------------------

class TestFilterRecentRepos:
    def test_includes_repo_pushed_within_window(self):
        repos = [{"pushed_at": _hours_ago(12)}]
        assert len(filter_recent_repos(repos, hours=24)) == 1

    def test_excludes_repo_pushed_outside_window(self):
        repos = [{"pushed_at": _days_ago(3)}]
        assert len(filter_recent_repos(repos, hours=24)) == 0

    def test_returns_empty_for_empty_input(self):
        assert filter_recent_repos([], hours=24) == []

    def test_skips_entry_with_no_pushed_at(self):
        repos = [{"name": "a"}, {"pushed_at": _hours_ago(1), "name": "b"}]
        result = filter_recent_repos(repos, hours=24)
        assert len(result) == 1
        assert result[0]["name"] == "b"

    def test_skips_entry_with_none_pushed_at(self):
        repos = [{"pushed_at": None}, {"pushed_at": _hours_ago(5)}]
        assert len(filter_recent_repos(repos, hours=24)) == 1

    def test_skips_entry_with_invalid_date(self):
        repos = [{"pushed_at": "bad-date"}]
        assert filter_recent_repos(repos, hours=24) == []

    def test_multiple_repos_mixed_recency(self):
        repos = [
            {"pushed_at": _hours_ago(6), "name": "recent"},
            {"pushed_at": _days_ago(5), "name": "old"},
        ]
        result = filter_recent_repos(repos, hours=24)
        assert len(result) == 1
        assert result[0]["name"] == "recent"


# ---------------------------------------------------------------------------
# fetch_github_activity
# ---------------------------------------------------------------------------

class TestFetchGithubActivity:
    def test_returns_error_dict_when_no_token(self):
        result = fetch_github_activity("")
        assert "error" in result
        assert result["recent_repos"] == []
        assert result["stale_repos"] == []
        assert result["open_prs"] == []

    def test_returns_error_on_api_failure(self):
        with patch("github_fetcher._get_paginated", side_effect=Exception("timeout")):
            result = fetch_github_activity("fake-token")
        assert "error" in result

    def test_excludes_archived_repos(self):
        fake_repos = [
            {
                "full_name": "u/active",
                "pushed_at": _hours_ago(3),
                "archived": False,
                "open_issues_count": 0,
            },
            {
                "full_name": "u/archived",
                "pushed_at": _hours_ago(3),
                "archived": True,
                "open_issues_count": 0,
            },
        ]
        with patch("github_fetcher._get_paginated", return_value=fake_repos):
            with patch("github_fetcher._get", return_value=[]):
                result = fetch_github_activity("fake-token")
        names = [r["name"] for r in result["recent_repos"]]
        assert "u/archived" not in names
        assert "u/active" in names

    def test_detects_stale_repos(self):
        fake_repos = [
            {
                "full_name": "u/old",
                "pushed_at": _days_ago(14),
                "archived": False,
                "open_issues_count": 2,
            },
        ]
        with patch("github_fetcher._get_paginated", return_value=fake_repos):
            result = fetch_github_activity("fake-token", stale_days=7)
        assert len(result["stale_repos"]) == 1
        assert result["stale_repos"][0]["name"] == "u/old"

    def test_fetches_prs_for_recent_repos(self):
        fake_repo = {
            "full_name": "u/repo",
            "pushed_at": _hours_ago(2),
            "archived": False,
            "open_issues_count": 0,
        }
        fake_pr = {
            "number": 42,
            "title": "Fix something",
            "user": {"login": "alice"},
            "updated_at": _hours_ago(1),
        }
        with patch("github_fetcher._get_paginated", return_value=[fake_repo]):
            with patch("github_fetcher._get", return_value=[fake_pr]):
                result = fetch_github_activity("fake-token")
        assert len(result["open_prs"]) == 1
        assert result["open_prs"][0]["number"] == 42
        assert result["open_prs"][0]["repo"] == "u/repo"

    def test_pr_fetch_failure_does_not_crash(self):
        fake_repo = {
            "full_name": "u/repo",
            "pushed_at": _hours_ago(2),
            "archived": False,
            "open_issues_count": 0,
        }
        with patch("github_fetcher._get_paginated", return_value=[fake_repo]):
            with patch("github_fetcher._get", side_effect=Exception("forbidden")):
                result = fetch_github_activity("fake-token")
        assert result["open_prs"] == []

    def test_health_field_present_in_recent_repos(self):
        fake_repo = {
            "full_name": "u/repo",
            "pushed_at": _hours_ago(1),
            "archived": False,
            "open_issues_count": 0,
        }
        with patch("github_fetcher._get_paginated", return_value=[fake_repo]):
            with patch("github_fetcher._get", return_value=[]):
                result = fetch_github_activity("fake-token")
        assert "health" in result["recent_repos"][0]
        assert result["recent_repos"][0]["health"] == "active"
