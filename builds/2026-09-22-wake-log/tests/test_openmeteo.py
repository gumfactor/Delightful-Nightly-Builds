import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from src import openmeteo
from tests.conftest import make_forecast_payload


def test_build_url_rejects_invalid_coordinates():
    with pytest.raises(ValueError):
        openmeteo.build_url(latitude=200.0, longitude=0.0)
    with pytest.raises(ValueError):
        openmeteo.build_url(latitude=0.0, longitude=-200.0)


def test_build_url_rejects_invalid_forecast_days():
    with pytest.raises(ValueError):
        openmeteo.build_url(latitude=45.0, longitude=-79.0, forecast_days=0)
    with pytest.raises(ValueError):
        openmeteo.build_url(latitude=45.0, longitude=-79.0, forecast_days=11)


def test_build_url_uses_knots_and_auto_timezone():
    url = openmeteo.build_url(latitude=45.0, longitude=-79.0, forecast_days=3)
    assert "windspeed_unit=kn" in url
    assert "timezone=auto" in url
    assert "forecast_days=3" in url


def test_parse_forecast_produces_three_windows_per_day(calm_sunny_payload):
    windows = openmeteo.parse_forecast(calm_sunny_payload)
    labels = sorted(w.window for w in windows)
    assert labels == ["afternoon", "evening", "morning"]


def test_parse_forecast_computes_correct_aggregates(calm_sunny_payload):
    windows = openmeteo.parse_forecast(calm_sunny_payload)
    afternoon = next(w for w in windows if w.window == "afternoon")
    assert afternoon.wind_knots == 5.0
    assert afternoon.gust_knots == 6.0
    assert afternoon.temp_c == 22.0
    assert afternoon.precip_probability == 5.0
    assert afternoon.cloud_cover == 10.0
    assert afternoon.beaufort_number == 2
    assert afternoon.beaufort_name == "Light Breeze"
    assert afternoon.score > 0


def test_parse_forecast_tracks_daylight_hours_per_window():
    # Sunrise 07:00, sunset 19:00 -> morning window (6-12) has 5 daylight hours
    # (7,8,9,10,11); evening window (18-22) has 1 daylight hour (18).
    payload = make_forecast_payload(["2026-10-01"], sunrise_hour=7, sunset_hour=19)
    windows = openmeteo.parse_forecast(payload)
    morning = next(w for w in windows if w.window == "morning")
    evening = next(w for w in windows if w.window == "evening")
    assert morning.daylight_hours == 5
    assert evening.daylight_hours == 1


def test_parse_forecast_zero_daylight_window_scores_zero():
    # Sunrise very late, sunset very early -> evening window has no daylight overlap.
    payload = make_forecast_payload(["2026-10-01"], sunrise_hour=10, sunset_hour=15)
    windows = openmeteo.parse_forecast(payload)
    evening = next(w for w in windows if w.window == "evening")
    assert evening.daylight_hours == 0
    assert evening.score == 0.0


def test_parse_forecast_missing_hourly_raises():
    with pytest.raises(openmeteo.OpenMeteoError):
        openmeteo.parse_forecast({"daily": {}})


def test_parse_forecast_missing_required_field_raises(calm_sunny_payload):
    del calm_sunny_payload["hourly"]["windgusts_10m"]
    with pytest.raises(openmeteo.OpenMeteoError):
        openmeteo.parse_forecast(calm_sunny_payload)


def test_parse_forecast_length_mismatch_raises(calm_sunny_payload):
    calm_sunny_payload["hourly"]["temperature_2m"] = calm_sunny_payload["hourly"]["temperature_2m"][:-1]
    with pytest.raises(openmeteo.OpenMeteoError):
        openmeteo.parse_forecast(calm_sunny_payload)


def test_best_window_returns_none_for_empty_list():
    assert openmeteo.best_window([]) is None


def test_best_window_returns_none_when_all_zero(calm_sunny_payload):
    windows = openmeteo.parse_forecast(calm_sunny_payload)
    for w in windows:
        w.score = 0.0
    assert openmeteo.best_window(windows) is None


def test_best_window_returns_highest_score(calm_sunny_payload):
    windows = openmeteo.parse_forecast(calm_sunny_payload)
    windows[0].score = 10.0
    windows[1].score = 99.0
    windows[2].score = 50.0
    assert openmeteo.best_window(windows) is windows[1]


def test_fetch_forecast_raises_on_network_error():
    with patch("src.openmeteo.urllib.request.urlopen", side_effect=urllib.error.URLError("no route")):
        with pytest.raises(openmeteo.OpenMeteoError):
            openmeteo.fetch_forecast(45.0, -79.0)


def test_fetch_forecast_raises_on_malformed_json():
    mock_response = MagicMock()
    mock_response.read.return_value = b"not json{{{"
    mock_response.__enter__.return_value = mock_response
    with patch("src.openmeteo.urllib.request.urlopen", return_value=mock_response):
        with pytest.raises(openmeteo.OpenMeteoError):
            openmeteo.fetch_forecast(45.0, -79.0)


def test_fetch_forecast_parses_successful_response(calm_sunny_payload):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(calm_sunny_payload).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    with patch("src.openmeteo.urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
        result = openmeteo.fetch_forecast(45.0, -79.0)
        assert result == calm_sunny_payload
        mock_urlopen.assert_called_once()


def test_get_scored_windows_never_makes_a_real_network_call(calm_sunny_payload):
    """Guard against a regression that accidentally hits the live API in tests."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(calm_sunny_payload).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    with patch("src.openmeteo.urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
        windows = openmeteo.get_scored_windows(45.0, -79.0, forecast_days=1)
        assert len(windows) == 3
        mock_urlopen.assert_called_once()
