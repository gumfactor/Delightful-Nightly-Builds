import json
import urllib.error

import pytest

from src.github_client import (
    GitHubAPIError,
    _request,
    get_commit_detail,
    list_fix_candidate_commits,
    list_user_repos,
)


def test_list_user_repos_filters_forks(monkeypatch):
    def fake_request(url, token, params=None):
        assert params["page"] == 1
        return [
            {"full_name": "user/real-repo", "fork": False},
            {"full_name": "user/forked-repo", "fork": True},
        ]

    repos = list_user_repos("tok", request_fn=fake_request)
    assert repos == ["user/real-repo"]


def test_list_user_repos_includes_forks_when_requested(monkeypatch):
    def fake_request(url, token, params=None):
        return [{"full_name": "user/forked-repo", "fork": True}]

    repos = list_user_repos("tok", include_forks=True, request_fn=fake_request)
    assert repos == ["user/forked-repo"]


def test_list_user_repos_paginates(monkeypatch):
    calls = {"count": 0}

    def fake_request(url, token, params=None):
        calls["count"] += 1
        if params["page"] == 1:
            return [{"full_name": f"user/repo{i}", "fork": False} for i in range(100)]
        return [{"full_name": "user/repo100", "fork": False}]

    repos = list_user_repos("tok", max_repos=200, request_fn=fake_request)
    assert len(repos) == 101
    assert calls["count"] == 2


def test_list_fix_candidate_commits_paginates_and_stops_on_short_page():
    def fake_request(url, token, params=None):
        if params["page"] == 1:
            return [{"sha": f"s{i}"} for i in range(100)]
        return [{"sha": "s100"}]

    commits = list_fix_candidate_commits("tok", "owner/repo", limit=500, request_fn=fake_request)
    assert len(commits) == 101


def test_list_fix_candidate_commits_respects_limit():
    def fake_request(url, token, params=None):
        return [{"sha": f"s{i}"} for i in range(100)]

    commits = list_fix_candidate_commits("tok", "owner/repo", limit=10, request_fn=fake_request)
    assert len(commits) == 10


def test_get_commit_detail_calls_correct_url():
    seen = {}

    def fake_request(url, token):
        seen["url"] = url
        return {"sha": "abc123", "files": []}

    detail = get_commit_detail("tok", "owner/repo", "abc123", request_fn=fake_request)
    assert detail["sha"] == "abc123"
    assert "owner/repo/commits/abc123" in seen["url"]


def test_request_wraps_http_error(monkeypatch):
    class FakeHTTPError(urllib.error.HTTPError):
        def __init__(self):
            super().__init__("http://x", 404, "Not Found", {}, None)

    def fake_urlopen(req, timeout=15):
        raise FakeHTTPError()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(GitHubAPIError):
        _request("https://api.github.com/user/repos", "tok")


def test_request_wraps_url_error(monkeypatch):
    def fake_urlopen(req, timeout=15):
        raise urllib.error.URLError("network unreachable")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    with pytest.raises(GitHubAPIError):
        _request("https://api.github.com/user/repos", "tok")
