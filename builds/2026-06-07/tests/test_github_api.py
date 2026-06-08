"""Tests for github_api — all network calls mocked via unittest.mock."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.github_api import get_user_repos, get_commits_since


def _mock_urlopen(payload):
    """Return a context-manager mock whose .read() returns JSON-encoded payload."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_get_user_repos_returns_names():
    """get_user_repos extracts repo names from the API response."""
    payload = [{"name": "repo-a", "archived": False}, {"name": "repo-b", "archived": False}]
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
        repos = get_user_repos("user", "token")
    assert repos == ["repo-a", "repo-b"]


def test_get_user_repos_excludes_archived():
    """Archived repos are not returned."""
    payload = [{"name": "live", "archived": False}, {"name": "old", "archived": True}]
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
        repos = get_user_repos("user", "token")
    assert repos == ["live"]
    assert "old" not in repos


def test_get_user_repos_respects_exclude_list():
    """Repos in the exclude list are omitted."""
    payload = [{"name": "keep", "archived": False}, {"name": "skip", "archived": False}]
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
        repos = get_user_repos("user", "token", exclude=["skip"])
    assert repos == ["keep"]


def test_get_commits_since_parses_response():
    """get_commits_since extracts message, hash, author, and source fields."""
    payload = [
        {
            "sha": "abc1234567890",
            "commit": {
                "message": "Fix bug\n\nBody text",
                "author": {"name": "Alice", "date": "2026-06-07T10:00:00Z"},
            },
        }
    ]
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(payload)):
        commits = get_commits_since("user", "my-repo", "token", hours=24)
    assert len(commits) == 1
    assert commits[0]["message"] == "Fix bug"  # body stripped
    assert commits[0]["hash"] == "abc12345"
    assert commits[0]["author"] == "Alice"
    assert commits[0]["source"] == "github"
    assert commits[0]["repo"] == "my-repo"


def test_get_commits_since_empty_repo_returns_empty():
    """An empty commit list from the API returns an empty list."""
    with patch("urllib.request.urlopen", return_value=_mock_urlopen([])):
        commits = get_commits_since("user", "empty-repo", "token", hours=24)
    assert commits == []
