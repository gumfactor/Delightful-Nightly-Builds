import urllib.error
from unittest.mock import patch

import ai_briefing


def project(**overrides):
    base = {
        "project_num": "P1",
        "title": "Neural correlates of empathy",
        "abstract": "abstract text",
        "award_amount": 100000,
        "fiscal_year": 2024,
    }
    base.update(overrides)
    return base


SAMPLE_STATS = {
    "project_count": 2,
    "total_amount": 300000,
    "fiscal_year_range": (2023, 2024),
    "distinct_institutes": 1,
    "distinct_organizations": 2,
}
SAMPLE_INSTITUTES = [("NIMH", {"total_amount": 300000, "count": 2})]
SAMPLE_MECHANISMS = {"R01": 2}


class FakeAnthropicResponse:
    def __init__(self, text):
        import json

        self._body = json.dumps({"content": [{"type": "text", "text": text}]}).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_generate_briefing_uses_ai_when_key_and_call_succeed():
    with patch("ai_briefing.urllib.request.urlopen", return_value=FakeAnthropicResponse("The field is trending toward NIMH R01 funding.")):
        result = ai_briefing.generate_briefing(
            "Empathy", [project()], SAMPLE_STATS, SAMPLE_INSTITUTES, SAMPLE_MECHANISMS, api_key="sk-test-key"
        )
    assert result["source"] == "ai"
    assert "NIMH" in result["text"]


def test_generate_briefing_falls_back_without_api_key():
    result = ai_briefing.generate_briefing(
        "Empathy", [project()], SAMPLE_STATS, SAMPLE_INSTITUTES, SAMPLE_MECHANISMS, api_key=None
    )
    assert result["source"] == "template"
    assert len(result["text"]) > 0
    assert "NIMH" in result["text"]


def test_generate_briefing_falls_back_on_http_error():
    error = urllib.error.HTTPError(url="x", code=401, msg="Unauthorized", hdrs=None, fp=None)
    with patch("ai_briefing.urllib.request.urlopen", side_effect=error):
        result = ai_briefing.generate_briefing(
            "Empathy", [project()], SAMPLE_STATS, SAMPLE_INSTITUTES, SAMPLE_MECHANISMS, api_key="sk-test-key"
        )
    assert result["source"] == "template"
    assert len(result["text"]) > 0


def test_generate_briefing_falls_back_on_url_error():
    error = urllib.error.URLError("network down")
    with patch("ai_briefing.urllib.request.urlopen", side_effect=error):
        result = ai_briefing.generate_briefing(
            "Empathy", [project()], SAMPLE_STATS, SAMPLE_INSTITUTES, SAMPLE_MECHANISMS, api_key="sk-test-key"
        )
    assert result["source"] == "template"


def test_generate_briefing_falls_back_on_empty_content():
    class EmptyContentResponse:
        def read(self):
            return b'{"content": []}'

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    with patch("ai_briefing.urllib.request.urlopen", return_value=EmptyContentResponse()):
        result = ai_briefing.generate_briefing(
            "Empathy", [project()], SAMPLE_STATS, SAMPLE_INSTITUTES, SAMPLE_MECHANISMS, api_key="sk-test-key"
        )
    assert result["source"] == "template"


def test_template_briefing_handles_zero_projects():
    empty_stats = {"project_count": 0, "total_amount": 0, "fiscal_year_range": (None, None), "distinct_institutes": 0, "distinct_organizations": 0}
    result = ai_briefing.generate_briefing("Empathy", [], empty_stats, [], {}, api_key=None)
    assert result["source"] == "template"
    assert "Run" in result["text"] or "sync" in result["text"]


def test_build_prompt_includes_topic_and_stats():
    prompt = ai_briefing._build_prompt("Empathy", SAMPLE_STATS, SAMPLE_INSTITUTES, SAMPLE_MECHANISMS, ["Sample title"])
    assert "Empathy" in prompt
    assert "NIMH" in prompt
    assert "Sample title" in prompt
    assert "R01" in prompt


def test_call_anthropic_raises_briefing_error_on_malformed_json():
    class BadResponse:
        def read(self):
            return b"not json"

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    with patch("ai_briefing.urllib.request.urlopen", return_value=BadResponse()):
        import pytest

        with pytest.raises(ai_briefing.BriefingError):
            ai_briefing._call_anthropic("prompt", "sk-test", ai_briefing.DEFAULT_MODEL)
