import json

import pytest

from src import ai_narrative

ANOMALY = {"fiscal_year": 2023, "type": "revenue_decline", "detail": "Revenue fell 15.0% year-over-year"}


class FakeResponse:
    def __init__(self, payload):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def test_deterministic_fallback_mentions_ticker_and_detail():
    text = ai_narrative.deterministic_fallback("AAPL", ANOMALY)
    assert "AAPL" in text
    assert "2023" in text
    assert "Revenue fell 15.0%" in text


def test_no_api_key_makes_zero_network_calls(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    calls = []

    def spy_urlopen(request, timeout=None):
        calls.append(request)
        raise AssertionError("should never be called with no API key")

    result = ai_narrative.generate_narrative("AAPL", ANOMALY, api_key=None, urlopen_func=spy_urlopen)
    assert calls == []
    assert result == ai_narrative.deterministic_fallback("AAPL", ANOMALY)


def test_explicit_empty_api_key_skips_network_call():
    calls = []

    def spy_urlopen(request, timeout=None):
        calls.append(request)
        raise AssertionError("should never be called")

    result = ai_narrative.generate_narrative("AAPL", ANOMALY, api_key="", urlopen_func=spy_urlopen)
    assert calls == []
    assert result == ai_narrative.deterministic_fallback("AAPL", ANOMALY)


def test_successful_api_call_returns_ai_text():
    def fake_urlopen(request, timeout=None):
        return FakeResponse({"content": [{"text": "Revenue declined meaningfully in FY2023."}]})

    result = ai_narrative.generate_narrative("AAPL", ANOMALY, api_key="fake-key", urlopen_func=fake_urlopen)
    assert result == "Revenue declined meaningfully in FY2023."


def test_api_call_sends_only_aggregate_fields_never_raw_filing_text():
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["body"] = json.loads(request.data)
        return FakeResponse({"content": [{"text": "ok"}]})

    ai_narrative.generate_narrative("AAPL", ANOMALY, api_key="fake-key", urlopen_func=fake_urlopen)
    prompt_text = captured["body"]["messages"][0]["content"]
    assert "AAPL" in prompt_text
    assert "2023" in prompt_text
    assert "revenue_decline" in prompt_text.lower() or "revenue decline" in prompt_text.lower()


def test_network_failure_falls_back_to_deterministic():
    def failing_urlopen(request, timeout=None):
        raise OSError("timeout")

    result = ai_narrative.generate_narrative("AAPL", ANOMALY, api_key="fake-key", urlopen_func=failing_urlopen)
    assert result == ai_narrative.deterministic_fallback("AAPL", ANOMALY)


def test_malformed_response_falls_back_to_deterministic():
    def bad_shape_urlopen(request, timeout=None):
        return FakeResponse({"unexpected": "shape"})

    result = ai_narrative.generate_narrative("AAPL", ANOMALY, api_key="fake-key", urlopen_func=bad_shape_urlopen)
    assert result == ai_narrative.deterministic_fallback("AAPL", ANOMALY)


def test_empty_text_response_falls_back_to_deterministic():
    def empty_text_urlopen(request, timeout=None):
        return FakeResponse({"content": [{"text": "   "}]})

    result = ai_narrative.generate_narrative("AAPL", ANOMALY, api_key="fake-key", urlopen_func=empty_text_urlopen)
    assert result == ai_narrative.deterministic_fallback("AAPL", ANOMALY)


def test_generate_narratives_keys_by_ticker_fiscal_year_type():
    anomalies_by_ticker = {"AAPL": [ANOMALY]}
    result = ai_narrative.generate_narratives(anomalies_by_ticker, api_key="")
    assert ("AAPL", 2023, "revenue_decline") in result
