import json
import urllib.error
from datetime import date
from unittest.mock import patch

import pytest

import weather_client


class FakeResponse:
    def __init__(self, body: dict, status: int = 200):
        self._body = json.dumps(body).encode("utf-8")
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_geocode_success():
    fake_body = {"results": [{"name": "Muskoka", "latitude": 45.0, "longitude": -79.5,
                               "country": "Canada", "admin1": "Ontario"}]}
    with patch("urllib.request.urlopen", return_value=FakeResponse(fake_body)):
        result = weather_client.geocode("Muskoka, Ontario")
    assert result.name == "Muskoka"
    assert result.latitude == 45.0
    assert result.longitude == -79.5


def test_geocode_no_match_raises():
    with patch("urllib.request.urlopen", return_value=FakeResponse({"results": []})):
        with pytest.raises(weather_client.WeatherClientError):
            weather_client.geocode("Nowhereville")


def test_fetch_forecast_parses_daily_fields():
    fake_body = {
        "daily": {
            "time": ["2026-08-15", "2026-08-16"],
            "temperature_2m_max": [25.0, 27.0],
            "temperature_2m_min": [15.0, 16.0],
            "precipitation_sum": [0.0, 5.0],
            "wind_speed_10m_max": [10.0, 20.0],
        }
    }
    with patch("urllib.request.urlopen", return_value=FakeResponse(fake_body)):
        results = weather_client.fetch_forecast(45.0, -79.5)
    assert len(results) == 2
    assert results[0].obs_date == date(2026, 8, 15)
    assert results[0].temp_max_c == 25.0
    assert results[1].precip_mm == 5.0


def test_fetch_forecast_handles_missing_optional_fields():
    fake_body = {"daily": {"time": ["2026-08-15"], "temperature_2m_max": [25.0]}}
    with patch("urllib.request.urlopen", return_value=FakeResponse(fake_body)):
        results = weather_client.fetch_forecast(45.0, -79.5)
    assert results[0].temp_max_c == 25.0
    assert results[0].wind_speed_max_kmh is None


def test_fetch_marine_returns_wave_and_water_temp():
    fake_body = {
        "daily": {"time": ["2026-08-15"], "wave_height_max": [0.4]},
        "hourly": {
            "time": ["2026-08-15T00:00", "2026-08-15T12:00", "2026-08-15T18:00"],
            "sea_surface_temperature": [18.0, 20.5, 19.0],
        },
    }
    with patch("urllib.request.urlopen", return_value=FakeResponse(fake_body)):
        results = weather_client.fetch_marine(45.0, -79.5)
    assert len(results) == 1
    assert results[0].wave_height_max_m == 0.4
    assert results[0].water_temp_c == 20.5  # picked the 12:00 reading


def test_fetch_marine_falls_back_to_first_available_hour_when_no_midday():
    fake_body = {
        "daily": {"time": ["2026-08-15"], "wave_height_max": [0.4]},
        "hourly": {
            "time": ["2026-08-15T00:00", "2026-08-15T06:00"],
            "sea_surface_temperature": [18.0, 18.5],
        },
    }
    with patch("urllib.request.urlopen", return_value=FakeResponse(fake_body)):
        results = weather_client.fetch_marine(45.0, -79.5)
    assert results[0].water_temp_c == 18.0


def test_fetch_marine_returns_empty_list_when_no_coverage():
    fake_body = {"daily": {"time": ["2026-08-15"], "wave_height_max": [None]}, "hourly": {}}
    with patch("urllib.request.urlopen", return_value=FakeResponse(fake_body)):
        results = weather_client.fetch_marine(45.0, -79.5)
    assert results == []


def test_fetch_marine_returns_empty_list_on_http_error_rather_than_raising():
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("blocked")):
        results = weather_client.fetch_marine(45.0, -79.5)
    assert results == []


def test_fetch_forecast_raises_on_http_error():
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("blocked")):
        with pytest.raises(weather_client.WeatherClientError):
            weather_client.fetch_forecast(45.0, -79.5)


def test_http_get_json_raises_on_non_200_status():
    with patch("urllib.request.urlopen", return_value=FakeResponse({}, status=500)):
        with pytest.raises(weather_client.WeatherClientError):
            weather_client._http_get_json(weather_client.FORECAST_URL, {"latitude": 45.0})
