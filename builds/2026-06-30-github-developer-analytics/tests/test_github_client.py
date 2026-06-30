"""Tests for GitHub API client utilities (no real HTTP calls)."""

import sys
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from github_client import GitHubClient


class TestParseCommitTimestamp:
    def test_parses_utc_z_suffix(self):
        commit = {"commit": {"author": {"date": "2026-06-30T14:23:45Z"}}}
        dt = GitHubClient.parse_commit_timestamp(commit)
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 6
        assert dt.day == 30
        assert dt.hour == 14

    def test_parses_offset_timezone(self):
        commit = {"commit": {"author": {"date": "2026-06-30T10:23:45-04:00"}}}
        dt = GitHubClient.parse_commit_timestamp(commit)
        assert dt is not None
        # Should be normalised to UTC: 10 + 4 = 14
        dt_utc = dt.astimezone(timezone.utc)
        assert dt_utc.hour == 14

    def test_returns_none_on_missing_key(self):
        commit = {"commit": {"author": {}}}
        dt = GitHubClient.parse_commit_timestamp(commit)
        assert dt is None

    def test_returns_none_on_malformed_date(self):
        commit = {"commit": {"author": {"date": "not-a-date"}}}
        dt = GitHubClient.parse_commit_timestamp(commit)
        assert dt is None

    def test_returns_none_on_empty_commit(self):
        dt = GitHubClient.parse_commit_timestamp({})
        assert dt is None


class TestBuildSinceIso:
    def test_returns_string_in_iso_format(self):
        since = GitHubClient.build_since_iso(3)
        assert "T" in since
        assert since.endswith("Z")

    def test_months_back_is_in_the_past(self):
        since = GitHubClient.build_since_iso(6)
        dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        assert dt < datetime.now(timezone.utc)

    def test_one_month_back_is_recent(self):
        since = GitHubClient.build_since_iso(1)
        dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        # Returns first of last month — may be up to ~62 days ago (e.g. May 1 from June 30)
        assert (now - dt).days <= 62

    def test_twelve_months_back_is_roughly_a_year(self):
        since = GitHubClient.build_since_iso(12)
        dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_back = (now - dt).days
        # Returns first of same month 1 year ago — between 365 and ~396 days depending on day of month
        assert 325 <= days_back <= 400


class TestGitHubClientMocked:
    def _make_client(self) -> GitHubClient:
        client = GitHubClient(token="fake-token")
        return client

    def test_get_authenticated_user_calls_correct_endpoint(self):
        client = self._make_client()
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {"login": "testuser"}
        with patch.object(client.session, "get", return_value=fake_response):
            user = client.get_authenticated_user()
            assert user["login"] == "testuser"

    def test_get_repos_returns_list(self):
        client = self._make_client()
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = [{"name": "repo1", "owner": {"login": "me"}}]
        with patch.object(client.session, "get", return_value=fake_response):
            repos = client.get_repos(max_repos=5)
            assert isinstance(repos, list)
            assert repos[0]["name"] == "repo1"

    def test_get_commits_returns_list(self):
        client = self._make_client()
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = [
            {"commit": {"author": {"date": "2026-06-01T10:00:00Z"}}}
        ]
        with patch.object(client.session, "get", return_value=fake_response):
            commits = client.get_commits("me", "repo1", "me", "2026-01-01T00:00:00Z")
            assert len(commits) == 1

    def test_get_languages_returns_dict(self):
        client = self._make_client()
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.json.return_value = {"Python": 5000, "JavaScript": 1000}
        with patch.object(client.session, "get", return_value=fake_response):
            langs = client.get_languages("me", "repo1")
            assert langs["Python"] == 5000

    def test_get_returns_none_on_404(self):
        client = self._make_client()
        fake_response = MagicMock()
        fake_response.status_code = 404
        fake_response.json.return_value = {}
        with patch.object(client.session, "get", return_value=fake_response):
            result = client._get("/repos/me/missing-repo")
            assert result is None

    def test_get_returns_none_on_409_empty_repo(self):
        client = self._make_client()
        fake_response = MagicMock()
        fake_response.status_code = 409  # GitHub returns 409 for empty repos
        fake_response.json.return_value = {"message": "Git Repository is empty."}
        with patch.object(client.session, "get", return_value=fake_response):
            commits = client.get_commits("me", "empty-repo", "me", "2025-01-01T00:00:00Z")
            assert commits == []

    def test_get_returns_none_on_permission_403(self):
        client = self._make_client()
        fake_response = MagicMock()
        fake_response.status_code = 403
        fake_response.headers = {"X-RateLimit-Remaining": "1"}  # not rate limited
        fake_response.json.return_value = {"message": "Permission denied"}
        with patch.object(client.session, "get", return_value=fake_response):
            result = client._get("/repos/me/private-repo/commits")
            assert result is None

    def test_get_commits_returns_empty_on_permission_denied(self):
        client = self._make_client()
        fake_response = MagicMock()
        fake_response.status_code = 403
        fake_response.headers = {"X-RateLimit-Remaining": "1"}
        fake_response.json.return_value = {}
        with patch.object(client.session, "get", return_value=fake_response):
            commits = client.get_commits("me", "private-repo", "me", "2025-01-01T00:00:00Z")
            assert commits == []

    def test_get_languages_returns_empty_dict_on_404(self):
        client = self._make_client()
        fake_response = MagicMock()
        fake_response.status_code = 404
        fake_response.json.return_value = {}
        with patch.object(client.session, "get", return_value=fake_response):
            langs = client.get_languages("me", "private-repo")
            assert langs == {}
