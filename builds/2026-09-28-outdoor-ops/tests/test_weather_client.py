import json

import pytest

from src.weather_client import WeatherClient, WeatherClientError

FAKE_RESPONSE = json.dumps({
    "daily": {
        "time": ["2026-09-28", "2026-09-29"],
        "temperature_2m_max": [17.0, 14.0],
        "temperature_2m_min": [10.0, 8.0],
        "precipitation_probability_max": [10.0, 80.0],
        "precipitation_sum": [0.0, 12.5],
        "windspeed_10m_max": [10.0, 28.0],
        "windgusts_10m_max": [18.0, 45.0],
        "uv_index_max": [4.0, 2.0],
        "weather_code": [1, 63],
    }
})

# Some Open-Meteo deployments/older cached responses may still use the
# legacy "weathercode" key instead of the current "weather_code".
FAKE_RESPONSE_LEGACY_WEATHERCODE_KEY = json.dumps({
    "daily": {
        "time": ["2026-09-28"],
        "temperature_2m_max": [17.0],
        "temperature_2m_min": [10.0],
        "precipitation_probability_max": [10.0],
        "precipitation_sum": [0.0],
        "windspeed_10m_max": [10.0],
        "windgusts_10m_max": [18.0],
        "uv_index_max": [4.0],
        "weathercode": [1],
    }
})


def test_build_url_contains_lat_lon_and_daily_params():
    client = WeatherClient(transport=lambda url: FAKE_RESPONSE)
    url = client.build_url(43.65, -79.38, 7)
    assert "latitude=43.65" in url
    assert "longitude=-79.38" in url
    assert "forecast_days=7" in url
    assert "temperature_2m_max" in url


def test_build_url_requests_current_weather_code_param_name():
    client = WeatherClient(transport=lambda url: FAKE_RESPONSE)
    url = client.build_url(43.65, -79.38, 7)
    assert "weather_code" in url


def test_get_daily_forecast_parses_response():
    client = WeatherClient(transport=lambda url: FAKE_RESPONSE)
    records = client.get_daily_forecast(43.65, -79.38, days=2)
    assert len(records) == 2
    assert records[0]["date"] == "2026-09-28"
    assert records[0]["temp_max"] == 17.0
    assert records[0]["weathercode"] == 1
    assert records[1]["precip_sum"] == 12.5


def test_get_daily_forecast_falls_back_to_legacy_weathercode_key():
    client = WeatherClient(transport=lambda url: FAKE_RESPONSE_LEGACY_WEATHERCODE_KEY)
    records = client.get_daily_forecast(43.65, -79.38, days=1)
    assert records[0]["weathercode"] == 1


def test_get_daily_forecast_raises_on_null_daily_block():
    client = WeatherClient(transport=lambda url: json.dumps({"daily": None}))
    with pytest.raises(WeatherClientError):
        client.get_daily_forecast(43.65, -79.38)


def test_get_daily_forecast_raises_when_weather_code_field_entirely_missing():
    broken = json.dumps({"daily": {"time": ["2026-09-28"], "temperature_2m_max": [17.0]}})
    client = WeatherClient(transport=lambda url: broken)
    with pytest.raises(WeatherClientError):
        client.get_daily_forecast(43.65, -79.38)


def test_get_daily_forecast_raises_on_invalid_json():
    client = WeatherClient(transport=lambda url: "not json")
    with pytest.raises(WeatherClientError):
        client.get_daily_forecast(43.65, -79.38)


def test_get_daily_forecast_raises_on_missing_daily_block():
    client = WeatherClient(transport=lambda url: json.dumps({"error": True}))
    with pytest.raises(WeatherClientError):
        client.get_daily_forecast(43.65, -79.38)


def test_get_daily_forecast_raises_on_missing_non_weathercode_field():
    broken = json.dumps({"daily": {"time": ["2026-09-28"], "weather_code": [1]}})
    client = WeatherClient(transport=lambda url: broken)
    with pytest.raises(WeatherClientError):
        client.get_daily_forecast(43.65, -79.38)


def test_get_daily_forecast_wraps_transport_exception():
    def raising_transport(url):
        raise ConnectionError("network unreachable")

    client = WeatherClient(transport=raising_transport)
    with pytest.raises(WeatherClientError):
        client.get_daily_forecast(43.65, -79.38)
