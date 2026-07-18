from datetime import date
from unittest.mock import patch

from src.boc_client import fetch_boc_series
from tests.conftest import FakeResponse, raise_url_error


VALID_PAYLOAD = {
    "seriesDetail": {"FXUSDCAD": {"label": "USD/CAD"}},
    "observations": [
        {"d": "2026-07-01", "FXUSDCAD": {"v": "1.3600"}},
        {"d": "2026-07-02", "FXUSDCAD": {"v": "1.3625"}},
    ],
}


def test_parses_valid_payload_into_observations():
    with patch("src.boc_client.urllib.request.urlopen", return_value=FakeResponse(200, VALID_PAYLOAD)):
        result = fetch_boc_series("FXUSDCAD", "USD/CAD Exchange Rate", "CAD per USD", recent=30)

    assert len(result) == 2
    assert result[0].obs_date == date(2026, 7, 1)
    assert result[0].value == 1.36
    assert result[0].series_id == "FXUSDCAD"
    assert result[0].source == "Bank of Canada Valet"


def test_rows_missing_series_field_are_skipped():
    payload = {
        "observations": [
            {"d": "2026-07-01", "FXUSDCAD": {"v": "1.36"}},
            {"d": "2026-07-02"},  # missing the series field entirely
            {"d": "2026-07-03", "FXUSDCAD": {"v": "not-a-number"}},
        ]
    }
    with patch("src.boc_client.urllib.request.urlopen", return_value=FakeResponse(200, payload)):
        result = fetch_boc_series("FXUSDCAD", "USD/CAD Exchange Rate", "CAD per USD")

    assert len(result) == 1
    assert result[0].obs_date == date(2026, 7, 1)


def test_network_error_returns_empty_list():
    with patch("src.boc_client.urllib.request.urlopen", side_effect=raise_url_error):
        result = fetch_boc_series("FXUSDCAD", "USD/CAD Exchange Rate", "CAD per USD")

    assert result == []


def test_non_200_status_returns_empty_list():
    with patch("src.boc_client.urllib.request.urlopen", return_value=FakeResponse(500, VALID_PAYLOAD)):
        result = fetch_boc_series("FXUSDCAD", "USD/CAD Exchange Rate", "CAD per USD")

    assert result == []


def test_missing_observations_key_returns_empty_list():
    with patch("src.boc_client.urllib.request.urlopen", return_value=FakeResponse(200, {"terms": {}})):
        result = fetch_boc_series("FXUSDCAD", "USD/CAD Exchange Rate", "CAD per USD")

    assert result == []
