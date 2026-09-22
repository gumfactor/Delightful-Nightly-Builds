import sys
from pathlib import Path

import pytest

# Make `src` importable as a package regardless of pytest's invocation cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import openmeteo  # noqa: E402


def _hours_for_day(date_str: str, count: int = 24):
    return [f"{date_str}T{h:02d}:00" for h in range(count)]


def make_forecast_payload(
    dates,
    wind_knots=8.0,
    gust_knots=10.0,
    temp_c=20.0,
    precip_probability=10.0,
    cloud_cover=30.0,
    sunrise_hour=7,
    sunset_hour=19,
):
    """Build a realistic, minimal Open-Meteo response for the given dates,
    with constant conditions across all hours (tests override specific
    hours/fields as needed)."""
    times = []
    wind = []
    gust = []
    temp = []
    precip = []
    cloud = []
    for date_str in dates:
        hours = _hours_for_day(date_str)
        times.extend(hours)
        wind.extend([wind_knots] * len(hours))
        gust.extend([gust_knots] * len(hours))
        temp.extend([temp_c] * len(hours))
        precip.extend([precip_probability] * len(hours))
        cloud.extend([cloud_cover] * len(hours))

    daily_time = list(dates)
    sunrise = [f"{d}T{sunrise_hour:02d}:00" for d in dates]
    sunset = [f"{d}T{sunset_hour:02d}:00" for d in dates]

    return {
        "hourly": {
            "time": times,
            "temperature_2m": temp,
            "precipitation_probability": precip,
            "windspeed_10m": wind,
            "windgusts_10m": gust,
            "cloudcover": cloud,
        },
        "daily": {
            "time": daily_time,
            "sunrise": sunrise,
            "sunset": sunset,
        },
    }


@pytest.fixture
def calm_sunny_payload():
    return make_forecast_payload(["2026-10-01"], wind_knots=5.0, gust_knots=6.0, temp_c=22.0, precip_probability=5.0, cloud_cover=10.0)


@pytest.fixture
def windy_showery_payload():
    return make_forecast_payload(["2026-10-01"], wind_knots=25.0, gust_knots=38.0, temp_c=14.0, precip_probability=70.0, cloud_cover=90.0)


@pytest.fixture
def one_window(calm_sunny_payload):
    windows = openmeteo.parse_forecast(calm_sunny_payload)
    return next(w for w in windows if w.window == "afternoon")
