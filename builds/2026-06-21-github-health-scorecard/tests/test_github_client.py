import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from github_client import get_latest_ci_run, list_repos


def _make_repo(name: str, pushed_at: str = "2026-06-21T00:00:00Z") -> dict:
    return {
        "name": name,
        "full_name": f"user/{name}",
        "language": "Python",
        "description": "",
        "private": False,
        "archived": False,
        "open_issues_count": 0,
        "pushed_at": pushed_at,
        "owner": {"login": "user"},
    }


def test_list_repos_returns_repos():
    """list_repos returns all repos from the mock fetch."""
    repos = [_make_repo("repo-a"), _make_repo("repo-b")]
    call_count = []

    def mock_fetch(url: str):
        call_count.append(url)
        return repos

    result = list_repos("fake-token", fetch=mock_fetch)
    assert len(result) == 2
    assert result[0]["name"] == "repo-a"


def test_list_repos_paginates():
    """list_repos fetches subsequent pages when first page is exactly 100 items."""
    page_one = [_make_repo(f"repo-{i}") for i in range(100)]
    page_two = [_make_repo("repo-100")]
    pages = [page_one, page_two]
    call_idx = []

    def mock_fetch(url: str):
        idx = len(call_idx)
        call_idx.append(url)
        return pages[idx] if idx < len(pages) else []

    result = list_repos("fake-token", fetch=mock_fetch)
    assert len(result) == 101
    assert len(call_idx) == 2


def test_list_repos_empty():
    """list_repos returns empty list when API returns empty."""
    def mock_fetch(url: str):
        return []

    result = list_repos("fake-token", fetch=mock_fetch)
    assert result == []


def test_get_latest_ci_run_success():
    """get_latest_ci_run returns first run when runs exist."""
    run = {"id": 42, "status": "completed", "conclusion": "success"}

    def mock_fetch(url: str):
        return {"workflow_runs": [run]}

    result = get_latest_ci_run("user", "myrepo", "fake-token", fetch=mock_fetch)
    assert result is not None
    assert result["id"] == 42
    assert result["conclusion"] == "success"


def test_get_latest_ci_run_no_runs():
    """get_latest_ci_run returns None when no workflow runs exist."""
    def mock_fetch(url: str):
        return {"workflow_runs": []}

    result = get_latest_ci_run("user", "myrepo", "fake-token", fetch=mock_fetch)
    assert result is None


def test_get_latest_ci_run_failure_ci():
    """get_latest_ci_run correctly returns a failing run."""
    run = {"id": 7, "status": "completed", "conclusion": "failure"}

    def mock_fetch(url: str):
        return {"workflow_runs": [run]}

    result = get_latest_ci_run("user", "myrepo", "fake-token", fetch=mock_fetch)
    assert result["conclusion"] == "failure"
