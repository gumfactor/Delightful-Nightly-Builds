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
        "weathercode": [1, 63],
    }
})


def test_build_url_contains_lat_lon_and_daily_params():
    client = WeatherClient(transport=lambda url: FAKE_RESPONSE)
    url = client.build_url(43.65, -79.38, 7)
    assert "latitude=43.65" in url
    assert "longitude=-79.38" in url
    assert "forecast_days=7" in url
    assert "temperature_2m_max" in url


def test_get_daily_forecast_parses_response():
    client = WeatherClient(transport=lambda url: FAKE_RESPONSE)
    records = client.get_daily_forecast(43.65, -79.38, days=2)
    assert len(records) == 2
    assert records[0]["date"] == "2026-09-28"
    assert records[0]["temp_max"] == 17.0
    assert records[1]["precip_sum"] == 12.5


def test_get_daily_forecast_raises_on_invalid_json():
    client = WeatherClient(transport=lambda url: "not json")
    with pytest.raises(WeatherClientError):
        client.get_daily_forecast(43.65, -79.38)


def test_get_daily_forecast_raises_on_missing_daily_block():
    client = WeatherClient(transport=lambda url: json.dumps({"error": True}))
    with pytest.raises(WeatherClientError):
        client.get_daily_forecast(43.65, -79.38)


def test_get_daily_forecast_raises_on_missing_field():
    broken = json.dumps({"daily": {"time": ["2026-09-28"]}})
    client = WeatherClient(transport=lambda url: broken)
    with pytest.raises(WeatherClientError):
        client.get_daily_forecast(43.65, -79.38)


def test_get_daily_forecast_wraps_transport_exception():
    def raising_transport(url):
        raise ConnectionError("network unreachable")

    client = WeatherClient(transport=raising_transport)
    with pytest.raises(WeatherClientError):
        client.get_daily_forecast(43.65, -79.38)
