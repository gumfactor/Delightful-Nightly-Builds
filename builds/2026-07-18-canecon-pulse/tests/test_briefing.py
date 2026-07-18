from datetime import date
from unittest.mock import patch

from src.briefing import generate_briefing
from src.deltas import DeltaSummary, PeriodDelta
from tests.conftest import FakeResponse, raise_url_error


def make_summary():
    month = PeriodDelta(compare_date=date(2026, 6, 1), compare_value=1.30, change=0.02, pct_change=1.54)
    return DeltaSummary(latest_date=date(2026, 7, 1), latest_value=1.32, day=None, week=None, month=month)


def test_no_api_key_uses_template():
    text, source = generate_briefing({"USD/CAD Exchange Rate": make_summary()}, api_key=None)

    assert source == "template"
    assert "USD/CAD Exchange Rate" in text
    assert len(text) > 0


def test_ai_success_is_used():
    payload = {"content": [{"type": "text", "text": "The loonie strengthened this month."}]}
    with patch("src.briefing.urllib.request.urlopen", return_value=FakeResponse(200, payload)):
        text, source = generate_briefing({"USD/CAD Exchange Rate": make_summary()}, api_key="fake-key")

    assert source == "ai"
    assert text == "The loonie strengthened this month."


def test_ai_network_failure_falls_back_to_template():
    with patch("src.briefing.urllib.request.urlopen", side_effect=raise_url_error):
        text, source = generate_briefing({"USD/CAD Exchange Rate": make_summary()}, api_key="fake-key")

    assert source == "template"
    assert len(text) > 0


def test_ai_non_200_status_falls_back_to_template():
    with patch("src.briefing.urllib.request.urlopen", return_value=FakeResponse(500, {})):
        text, source = generate_briefing({"USD/CAD Exchange Rate": make_summary()}, api_key="fake-key")

    assert source == "template"


def test_ai_malformed_response_falls_back_to_template():
    with patch("src.briefing.urllib.request.urlopen", return_value=FakeResponse(200, {"unexpected": "shape"})):
        text, source = generate_briefing({"USD/CAD Exchange Rate": make_summary()}, api_key="fake-key")

    assert source == "template"


def test_template_handles_indicator_with_no_data():
    text, source = generate_briefing({"Canada All-Items CPI": None}, api_key=None)

    assert source == "template"
    assert "no data synced yet" in text
