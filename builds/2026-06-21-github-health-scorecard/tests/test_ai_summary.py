import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_summary import generate_insights


def _make_repo(name: str = "test", score: int = 50) -> dict:
    return {
        "name": name,
        "health_score": score,
        "health_label": "Fair",
        "days_since_push": 10,
        "open_issues": 2,
        "ci_status": "no-ci",
    }


def test_generate_insights_returns_text_with_mock():
    """With a mock API, returns the text from the response."""
    def mock_post(payload):
        return {"content": [{"text": "• Repo alpha needs attention.\n• Repo beta is healthy."}]}

    result = generate_insights([_make_repo("alpha"), _make_repo("beta")], api_key="sk-test", _post=mock_post)
    assert "alpha" in result or "•" in result


def test_generate_insights_no_api_key_returns_empty():
    """Without an API key, returns empty string without making any request."""
    called = []

    def mock_post(payload):
        called.append(True)
        return {"content": [{"text": "Should not be called"}]}

    result = generate_insights([_make_repo()], api_key=None, _post=mock_post)
    assert result == ""
    assert called == []


def test_generate_insights_api_error_returns_empty():
    """When the API raises an exception, returns empty string gracefully."""
    def mock_post(payload):
        raise ConnectionError("API unreachable")

    result = generate_insights([_make_repo()], api_key="sk-test", _post=mock_post)
    assert result == ""


def test_generate_insights_empty_repos():
    """With no repos, returns empty string without calling API."""
    called = []

    def mock_post(payload):
        called.append(True)
        return {"content": [{"text": "x"}]}

    result = generate_insights([], api_key="sk-test", _post=mock_post)
    assert result == ""
    assert called == []
