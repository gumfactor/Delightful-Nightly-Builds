import os
import sys
from datetime import date
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import weather  # noqa: E402


def _daily_payload(start: date, num_days: int, temp_max=20.0, temp_min=10.0, precip=0.0, wind=10.0, code=1):
    dates = [(date.fromordinal(start.toordinal() + i)).isoformat() for i in range(num_days)]
    return {
        "daily": {
            "time": dates,
            "temperature_2m_max": [temp_max] * num_days,
            "temperature_2m_min": [temp_min] * num_days,
            "precipitation_sum": [precip] * num_days,
            "windspeed_10m_max": [wind] * num_days,
            "weathercode": [code] * num_days,
        }
    }


def test_trip_starting_in_5_days_routes_to_forecast():
    today = date(2026, 8, 1)
    start = date(2026, 8, 6)
    with patch.object(weather, "fetch_forecast", return_value=[]) as mock_forecast, patch.object(
        weather, "fetch_climate_normal", return_value=[]
    ) as mock_climate:
        weather.get_weather_for_trip(43.65, -79.38, start, start, today)

    mock_forecast.assert_called_once()
    mock_climate.assert_not_called()


def test_trip_starting_in_40_days_routes_to_climate_normal():
    today = date(2026, 8, 1)
    start = date(2026, 9, 10)
    with patch.object(weather, "fetch_forecast", return_value=[]) as mock_forecast, patch.object(
        weather, "fetch_climate_normal", return_value=[]
    ) as mock_climate:
        weather.get_weather_for_trip(43.65, -79.38, start, start, today)

    mock_climate.assert_called_once()
    mock_forecast.assert_not_called()


def test_boundary_exactly_16_days_out_is_forecast_mode():
    today = date(2026, 8, 1)
    start = date(2026, 8, 17)  # exactly 16 days out
    assert weather.is_within_forecast_horizon(start, today) is True

    today = date(2026, 8, 1)
    start = date(2026, 8, 18)  # 17 days out
    assert weather.is_within_forecast_horizon(start, today) is False


def test_climate_normal_averages_multiple_years():
    start = date(2026, 12, 20)
    end = date(2026, 12, 20)

    responses = [
        _daily_payload(date(2025, 12, 20), 1, temp_max=10.0),
        _daily_payload(date(2024, 12, 20), 1, temp_max=20.0),
        _daily_payload(date(2023, 12, 20), 1, temp_max=30.0),
        _daily_payload(date(2022, 12, 20), 1, temp_max=10.0),
        _daily_payload(date(2021, 12, 20), 1, temp_max=10.0),
    ]
    with patch.object(weather, "fetch_json", side_effect=responses):
        readings = weather.fetch_climate_normal(43.65, -79.38, start, end)

    assert len(readings) == 1
    assert readings[0].temp_max_c == 16.0  # (10+20+30+10+10)/5


def test_climate_normal_skips_a_failed_year_and_still_averages():
    start = date(2026, 12, 20)
    end = date(2026, 12, 20)

    responses = [
        _daily_payload(date(2025, 12, 20), 1, temp_max=10.0),
        OSError("network down"),
        _daily_payload(date(2023, 12, 20), 1, temp_max=30.0),
        _daily_payload(date(2022, 12, 20), 1, temp_max=10.0),
        _daily_payload(date(2021, 12, 20), 1, temp_max=10.0),
    ]

    def side_effect(url):
        item = responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    with patch.object(weather, "fetch_json", side_effect=side_effect):
        readings = weather.fetch_climate_normal(43.65, -79.38, start, end)

    assert len(readings) == 1
    assert readings[0].temp_max_c == 15.0  # (10+30+10+10)/4, the failed year skipped


def test_climate_normal_raises_when_all_years_fail():
    start = date(2026, 12, 20)
    end = date(2026, 12, 20)
    with patch.object(weather, "fetch_json", side_effect=OSError("down")):
        try:
            weather.fetch_climate_normal(43.65, -79.38, start, end)
            assert False, "expected WeatherError"
        except weather.WeatherError:
            pass


def test_fetch_forecast_clips_end_date_to_horizon():
    start = date(2026, 8, 1)
    end = date(2026, 9, 1)  # far beyond the 16-day horizon
    with patch.object(weather, "fetch_json", return_value=_daily_payload(start, 17)) as mocked:
        weather.fetch_forecast(43.65, -79.38, start, end)

    called_url = mocked.call_args[0][0]
    assert "end_date=2026-08-17" in called_url
