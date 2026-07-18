from datetime import date
from unittest.mock import patch

from src.statcan_client import fetch_statcan_vector
from tests.conftest import FakeResponse, raise_url_error


VALID_PAYLOAD = [
    {
        "status": "SUCCESS",
        "object": {
            "vectorId": 41690973,
            "vectorDataPoint": [
                {"refPer": "2026-05-01", "value": 160.2},
                {"refPer": "2026-06-01", "value": 161.1},
            ],
        },
    }
]


def test_parses_valid_payload_into_observations():
    with patch("src.statcan_client.urllib.request.urlopen", return_value=FakeResponse(200, VALID_PAYLOAD)):
        result = fetch_statcan_vector(41690973, "Canada All-Items CPI", "index (2002=100)", latest_n=12)

    assert len(result) == 2
    assert result[1].obs_date == date(2026, 6, 1)
    assert result[1].value == 161.1
    assert result[1].series_id == "STATCAN_V41690973"
    assert result[1].source == "Statistics Canada WDS"


def test_status_not_success_returns_empty_list():
    payload = [{"status": "FAILED", "object": {}}]
    with patch("src.statcan_client.urllib.request.urlopen", return_value=FakeResponse(200, payload)):
        result = fetch_statcan_vector(41690973, "Canada All-Items CPI", "index (2002=100)")

    assert result == []


def test_missing_vector_data_point_returns_empty_list():
    payload = [{"status": "SUCCESS", "object": {"vectorId": 41690973}}]
    with patch("src.statcan_client.urllib.request.urlopen", return_value=FakeResponse(200, payload)):
        result = fetch_statcan_vector(41690973, "Canada All-Items CPI", "index (2002=100)")

    assert result == []


def test_network_error_returns_empty_list():
    with patch("src.statcan_client.urllib.request.urlopen", side_effect=raise_url_error):
        result = fetch_statcan_vector(41690973, "Canada All-Items CPI", "index (2002=100)")

    assert result == []


def test_malformed_value_rows_are_skipped():
    payload = [
        {
            "status": "SUCCESS",
            "object": {
                "vectorId": 41690973,
                "vectorDataPoint": [
                    {"refPer": "2026-06-01", "value": "not-a-number"},
                    {"refPer": "2026-07-01", "value": 161.5},
                ],
            },
        }
    ]
    with patch("src.statcan_client.urllib.request.urlopen", return_value=FakeResponse(200, payload)):
        result = fetch_statcan_vector(41690973, "Canada All-Items CPI", "index (2002=100)")

    assert len(result) == 1
    assert result[0].obs_date == date(2026, 7, 1)
