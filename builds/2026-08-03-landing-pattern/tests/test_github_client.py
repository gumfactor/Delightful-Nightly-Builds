"""Tests for the GitHub client — every HTTP call goes through a mocked `_api_get`
or a mocked `urllib.request.urlopen`. No real network call is ever made here.
"""

from __future__ import annotations

import io
import urllib.error
import urllib.request

import pytest

from landing_pattern import github_client


def test_fetch_open_prs_paginates_until_short_page(monkeypatch):
    calls = []

    def fake_api_get(path, token, params=None):
        calls.append((path, params))
        page = int(params["page"])
        if page == 1:
            return [{"number": i} for i in range(100)]
        if page == 2:
            return [{"number": 100}]
        return []

    monkeypatch.setattr(github_client, "_api_get", fake_api_get)
    result = github_client.fetch_open_prs("owner/repo", "tok")
    assert len(result) == 101
    assert calls[0][0] == "/repos/owner/repo/pulls?state=open"


def test_fetch_pr_files_extracts_filenames(monkeypatch):
    def fake_api_get(path, token, params=None):
        page = int(params["page"])
        if page == 1:
            return [{"filename": "a.py"}, {"filename": "b.py"}]
        return []

    monkeypatch.setattr(github_client, "_api_get", fake_api_get)
    files = github_client.fetch_pr_files("owner/repo", 5, "tok")
    assert files == ["a.py", "b.py"]


def test_fetch_ci_state_from_combined_status(monkeypatch):
    monkeypatch.setattr(
        github_client, "_api_get", lambda path, token, params=None: {"total_count": 2, "state": "success"}
    )
    assert github_client.fetch_ci_state("owner/repo", "sha123", "tok") == "success"


def test_fetch_ci_state_falls_back_to_check_runs_pending(monkeypatch):
    def fake_api_get(path, token, params=None):
        if "status" in path:
            return {"total_count": 0}
        return {"check_runs": [{"conclusion": None}]}

    monkeypatch.setattr(github_client, "_api_get", fake_api_get)
    assert github_client.fetch_ci_state("owner/repo", "sha", "tok") == "pending"


def test_fetch_ci_state_falls_back_to_check_runs_failure(monkeypatch):
    def fake_api_get(path, token, params=None):
        if "status" in path:
            return {"total_count": 0}
        return {"check_runs": [{"conclusion": "success"}, {"conclusion": "failure"}]}

    monkeypatch.setattr(github_client, "_api_get", fake_api_get)
    assert github_client.fetch_ci_state("owner/repo", "sha", "tok") == "failure"


def test_fetch_ci_state_none_when_no_status_or_checks(monkeypatch):
    def fake_api_get(path, token, params=None):
        if "status" in path:
            return {"total_count": 0}
        return {"check_runs": []}

    monkeypatch.setattr(github_client, "_api_get", fake_api_get)
    assert github_client.fetch_ci_state("owner/repo", "sha", "tok") == "none"


def test_fetch_review_state_changes_requested_wins_over_approved(monkeypatch):
    def fake_api_get(path, token, params=None):
        page = int(params["page"])
        if page == 1:
            return [
                {"user": {"login": "alice"}, "state": "APPROVED"},
                {"user": {"login": "bob"}, "state": "CHANGES_REQUESTED"},
            ]
        return []

    monkeypatch.setattr(github_client, "_api_get", fake_api_get)
    assert github_client.fetch_review_state("owner/repo", 1, "tok") == "changes_requested"


def test_fetch_review_state_review_required_when_no_reviews_but_requested(monkeypatch):
    monkeypatch.setattr(github_client, "_api_get", lambda path, token, params=None: [])
    result = github_client.fetch_review_state("owner/repo", 1, "tok", requested_reviewers=1)
    assert result == "review_required"


def test_fetch_review_state_none_when_nothing_pending(monkeypatch):
    monkeypatch.setattr(github_client, "_api_get", lambda path, token, params=None: [])
    assert github_client.fetch_review_state("owner/repo", 1, "tok") == "none"


def test_api_get_raises_clear_error_on_http_error(monkeypatch):
    def fake_urlopen(request, timeout=30):
        raise urllib.error.HTTPError(
            url="https://api.github.com/repos/owner/repo/pulls",
            code=404,
            msg="Not Found",
            hdrs=None,  # type: ignore[arg-type]
            fp=io.BytesIO(b'{"message": "Not Found"}'),
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(github_client.GitHubAPIError):
        github_client._api_get("/repos/owner/repo/pulls", "tok")


def test_fetch_repo_prs_full_assembles_all_fields(monkeypatch):
    monkeypatch.setattr(
        github_client,
        "fetch_open_prs",
        lambda repo, token: [{"number": 1}],
    )
    monkeypatch.setattr(
        github_client,
        "fetch_pr_detail",
        lambda repo, number, token: {
            "title": "Real Title",
            "html_url": "https://example/1",
            "created_at": "2026-08-01T00:00:00Z",
            "draft": False,
            "mergeable_state": "clean",
            "head": {"sha": "abc123"},
            "requested_reviewers": [],
        },
    )
    monkeypatch.setattr(github_client, "fetch_pr_files", lambda repo, number, token: ["a.py"])
    monkeypatch.setattr(github_client, "fetch_ci_state", lambda repo, sha, token: "success")
    monkeypatch.setattr(
        github_client,
        "fetch_review_state",
        lambda repo, number, token, requested_reviewers=0: "none",
    )

    result = github_client.fetch_repo_prs_full("owner/repo", "tok")
    assert result == [
        {
            "number": 1,
            "title": "Real Title",
            "url": "https://example/1",
            "created_at": "2026-08-01T00:00:00Z",
            "draft": False,
            "mergeable_state": "clean",
            "ci_state": "success",
            "review_state": "none",
            "files": ["a.py"],
        }
    ]
