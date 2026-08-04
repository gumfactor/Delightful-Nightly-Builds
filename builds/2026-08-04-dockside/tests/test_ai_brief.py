import json
import urllib.error
from unittest.mock import patch

import ai_brief


class FakeResponse:
    def __init__(self, body: dict):
        self._body = json.dumps(body).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_build_prompt_includes_site_and_summaries():
    prompt = ai_brief.build_prompt("Cottage Dock", ["Install Dock: ready_now, best day 2026-08-16"], 85.0)
    assert "Cottage Dock" in prompt
    assert "Install Dock" in prompt
    assert "85.0" in prompt


def test_deterministic_briefing_no_tasks():
    text = ai_brief.deterministic_briefing("Cottage Dock", [])
    assert "Cottage Dock" in text
    assert "add-task" in text


def test_deterministic_briefing_ready_and_blocked_counts():
    summaries = [
        "Install Dock: ready_now, best day 2026-08-16",
        "Remove Dock: overdue, best day none this week",
    ]
    text = ai_brief.deterministic_briefing("Cottage Dock", summaries)
    assert "1 task(s) are ready" in text
    assert "1 task(s) are blocked" in text


def test_generate_briefing_makes_zero_network_calls_without_key():
    with patch("urllib.request.urlopen") as mock_urlopen:
        text, source = ai_brief.generate_briefing("Cottage Dock", [], api_key=None)
    mock_urlopen.assert_not_called()
    assert source == "template"
    assert "Cottage Dock" in text


def test_generate_briefing_uses_ai_response_on_success():
    fake_body = {"content": [{"type": "text", "text": "Pull the dock Saturday, wind is calm."}]}
    with patch("urllib.request.urlopen", return_value=FakeResponse(fake_body)):
        text, source = ai_brief.generate_briefing("Cottage Dock", ["Install Dock: ready_now"], api_key="fake-key")
    assert source == "ai"
    assert text == "Pull the dock Saturday, wind is calm."


def test_generate_briefing_falls_back_to_template_on_api_failure():
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("blocked")):
        text, source = ai_brief.generate_briefing("Cottage Dock", ["Install Dock: ready_now"], api_key="fake-key")
    assert source == "template"
    assert "Cottage Dock" in text


def test_generate_briefing_falls_back_when_response_has_no_text():
    fake_body = {"content": []}
    with patch("urllib.request.urlopen", return_value=FakeResponse(fake_body)):
        text, source = ai_brief.generate_briefing("Cottage Dock", [], api_key="fake-key")
    assert source == "template"
