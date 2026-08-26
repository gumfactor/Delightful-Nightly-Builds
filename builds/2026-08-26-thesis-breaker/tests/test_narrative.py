import json

from src.rules import RuleResult
from src.personas import PersonaScore
from src.narrative import deterministic_text, polish


def make_persona(score=60):
    fired = [RuleResult("valuation_stretch", "Valuation Stretch", True, "P/E of 40 exceeds threshold of 35.")]
    not_fired = [RuleResult("growth_deceleration", "Growth Deceleration", False, "Growth did not decelerate.")]
    unavailable = [RuleResult("insider_selling", "Insider Selling Signal", None, "No data available.")]
    return PersonaScore("value_skeptic", "Value Skeptic", score, fired, not_fired, unavailable)


def test_deterministic_text_includes_score_and_findings():
    text = deterministic_text(make_persona())
    assert "60/100" in text
    assert "P/E of 40 exceeds threshold of 35." in text
    assert "Growth did not decelerate." in text
    assert "No data available." in text


def test_deterministic_text_handles_no_score():
    persona = PersonaScore("x", "X", None, [], [], [])
    text = deterministic_text(persona)
    assert "insufficient data" in text


def test_polish_falls_back_with_no_api_key():
    text, was_polished = polish(make_persona(), api_key=None)
    assert was_polished is False
    assert text == deterministic_text(make_persona())


def test_polish_falls_back_on_network_error():
    def failing_post(url, data, headers):
        raise __import__("urllib.error", fromlist=["URLError"]).URLError("boom")

    text, was_polished = polish(make_persona(), api_key="fake-key", http_post=failing_post)
    assert was_polished is False
    assert "insufficient data" not in text


def test_polish_falls_back_on_non_200_status():
    def bad_status_post(url, data, headers):
        return 500, b"{}"

    text, was_polished = polish(make_persona(), api_key="fake-key", http_post=bad_status_post)
    assert was_polished is False


def test_polish_falls_back_on_malformed_response():
    def malformed_post(url, data, headers):
        return 200, b"not json"

    text, was_polished = polish(make_persona(), api_key="fake-key", http_post=malformed_post)
    assert was_polished is False


def test_polish_falls_back_when_expected_field_missing():
    def missing_field_post(url, data, headers):
        return 200, json.dumps({"unexpected": "shape"}).encode()

    text, was_polished = polish(make_persona(), api_key="fake-key", http_post=missing_field_post)
    assert was_polished is False


def test_polish_succeeds_on_valid_response():
    def good_post(url, data, headers):
        return 200, json.dumps({"content": [{"text": "Skeptical rewritten prose."}]}).encode()

    text, was_polished = polish(make_persona(), api_key="fake-key", http_post=good_post)
    assert was_polished is True
    assert text == "Skeptical rewritten prose."


def test_polish_never_calls_network_without_api_key():
    calls = []

    def spy_post(url, data, headers):
        calls.append(url)
        return 200, json.dumps({"content": [{"text": "should not be called"}]}).encode()

    polish(make_persona(), api_key=None, http_post=spy_post)
    assert calls == []
