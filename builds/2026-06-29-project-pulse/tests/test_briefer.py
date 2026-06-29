import json
import os
import sys
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from briefer import _fallback_brief, build_brief_prompt, generate_brief

SAMPLE_PROJECT = {
    "id": 1,
    "name": "Canada List",
    "slug": "canada-list",
    "description": "Canadian business directory",
    "type": "business",
    "github_repos": ["owner/canada-list"],
}

SAMPLE_ACTIVITIES = [
    {
        "occurred_at": "2026-06-28T10:00:00Z",
        "title": "Updated ingestion pipeline",
        "source": "github",
    },
    {
        "occurred_at": "2026-06-27T09:00:00Z",
        "title": "Fixed classification bug",
        "source": "github",
    },
]


def test_build_brief_prompt_includes_project_name():
    prompt = build_brief_prompt(SAMPLE_PROJECT, SAMPLE_ACTIVITIES)
    assert "Canada List" in prompt


def test_build_brief_prompt_includes_description():
    prompt = build_brief_prompt(SAMPLE_PROJECT, SAMPLE_ACTIVITIES)
    assert "Canadian business directory" in prompt


def test_build_brief_prompt_includes_project_type():
    prompt = build_brief_prompt(SAMPLE_PROJECT, SAMPLE_ACTIVITIES)
    assert "business" in prompt


def test_build_brief_prompt_includes_recent_activities():
    prompt = build_brief_prompt(SAMPLE_PROJECT, SAMPLE_ACTIVITIES)
    assert "Updated ingestion pipeline" in prompt


def test_build_brief_prompt_includes_activity_dates():
    prompt = build_brief_prompt(SAMPLE_PROJECT, SAMPLE_ACTIVITIES)
    assert "2026-06-28" in prompt


def test_build_brief_prompt_handles_empty_activities():
    prompt = build_brief_prompt(SAMPLE_PROJECT, [])
    assert "no recent activity" in prompt.lower()


def test_generate_brief_no_api_key_returns_fallback():
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=False):
        result = generate_brief(SAMPLE_PROJECT, SAMPLE_ACTIVITIES, api_key=None)
    assert "Canada List" in result
    assert len(result) > 10


def test_generate_brief_api_error_returns_fallback():
    with patch(
        "briefer.urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        result = generate_brief(SAMPLE_PROJECT, SAMPLE_ACTIVITIES, api_key="fake-key")
    assert isinstance(result, str)
    assert len(result) > 0
    assert "Canada List" in result


def test_generate_brief_parses_api_response():
    response_body = json.dumps({
        "content": [{"text": "Canada List is currently improving the ingestion pipeline."}]
    }).encode()

    mock_resp = MagicMock()
    mock_resp.read.return_value = response_body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("briefer.urllib.request.urlopen", return_value=mock_resp):
        result = generate_brief(SAMPLE_PROJECT, SAMPLE_ACTIVITIES, api_key="fake-key")

    assert "Canada List" in result
    assert "ingestion" in result


def test_fallback_brief_with_activities():
    result = _fallback_brief(SAMPLE_PROJECT, SAMPLE_ACTIVITIES)
    assert "Canada List" in result
    assert "2026-06-28" in result
    assert "Updated ingestion pipeline" in result


def test_fallback_brief_no_activities():
    result = _fallback_brief(SAMPLE_PROJECT, [])
    assert "Canada List" in result
    assert "No recent activity" in result


def test_generate_brief_with_explicit_key_uses_api():
    response_body = json.dumps({
        "content": [{"text": "AI-generated brief."}]
    }).encode()

    mock_resp = MagicMock()
    mock_resp.read.return_value = response_body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("briefer.urllib.request.urlopen", return_value=mock_resp) as mock_open:
        generate_brief(SAMPLE_PROJECT, SAMPLE_ACTIVITIES, api_key="test-key")
        assert mock_open.called
