import json

import pytest

from src.air_quality_client import AirQualityClient, AirQualityClientError

FAKE_RESPONSE = json.dumps({
    "hourly": {
        "time": [
            "2026-09-28T00:00", "2026-09-28T12:00",
            "2026-09-29T00:00", "2026-09-29T12:00",
        ],
        "us_aqi": [20.0, 42.0, 25.0, 55.0],
        "pm2_5": [4.0, 8.0, 5.0, 11.0],
    }
})


def test_build_url_contains_hourly_params():
    client = AirQualityClient(transport=lambda url: FAKE_RESPONSE)
    url = client.build_url(43.65, -79.38, 7)
    assert "us_aqi" in url
    assert "pm2_5" in url
    assert "forecast_days=7" in url


def test_get_daily_air_quality_aggregates_hourly_to_daily():
    client = AirQualityClient(transport=lambda url: FAKE_RESPONSE)
    records = client.get_daily_air_quality(43.65, -79.38, days=2)
    assert len(records) == 2
    day1 = records[0]
    assert day1["date"] == "2026-09-28"
    assert day1["aqi_max"] == 42.0
    assert day1["aqi_mean"] == pytest.approx(31.0)
    assert day1["pm25_mean"] == pytest.approx(6.0)


def test_get_daily_air_quality_handles_missing_hours_gracefully():
    sparse = json.dumps({
        "hourly": {
            "time": ["2026-09-28T00:00"],
            "us_aqi": [30.0],
            "pm2_5": [6.0],
        }
    })
    client = AirQualityClient(transport=lambda url: sparse)
    records = client.get_daily_air_quality(43.65, -79.38, days=1)
    assert len(records) == 1
    assert records[0]["aqi_max"] == 30.0


def test_get_daily_air_quality_raises_on_invalid_json():
    client = AirQualityClient(transport=lambda url: "not json")
    with pytest.raises(AirQualityClientError):
        client.get_daily_air_quality(43.65, -79.38)


def test_get_daily_air_quality_raises_on_missing_hourly_block():
    client = AirQualityClient(transport=lambda url: json.dumps({"error": True}))
    with pytest.raises(AirQualityClientError):
        client.get_daily_air_quality(43.65, -79.38)


def test_get_daily_air_quality_raises_controlled_error_on_null_hourly_block():
    # {"hourly": null} must not reach hourly["time"] and raise an uncaught
    # TypeError — it must be a normal, catchable AirQualityClientError.
    client = AirQualityClient(transport=lambda url: json.dumps({"hourly": None}))
    with pytest.raises(AirQualityClientError):
        client.get_daily_air_quality(43.65, -79.38)


def test_get_daily_air_quality_raises_on_non_array_hourly_field():
    malformed = json.dumps({"hourly": {"time": ["2026-09-28T00:00"], "us_aqi": None, "pm2_5": [4.0]}})
    client = AirQualityClient(transport=lambda url: malformed)
    with pytest.raises(AirQualityClientError):
        client.get_daily_air_quality(43.65, -79.38)


def test_get_daily_air_quality_wraps_transport_exception():
    def raising_transport(url):
        raise TimeoutError("timed out")

    client = AirQualityClient(transport=raising_transport)
    with pytest.raises(AirQualityClientError):
        client.get_daily_air_quality(43.65, -79.38)
