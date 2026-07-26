"""Weather resolution for a trip: live forecast when close, climate-normal estimate otherwise.

Open-Meteo's free forecast endpoint only covers the next 16 days. A trip planned
further out than that can't get a real forecast, so instead we pull the same
calendar date range from the last few years of the historical archive and
average it into a "climate normal" — clearly labeled as an estimate, not a
forecast.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from datetime import date, timedelta

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
REQUEST_TIMEOUT_SECONDS = 10
FORECAST_HORIZON_DAYS = 16
CLIMATE_NORMAL_YEARS_BACK = 5

DAILY_FIELDS = "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode"


class WeatherError(Exception):
    """Raised when weather data cannot be resolved for a trip."""


@dataclass(frozen=True)
class DailyWeather:
    day_date: str  # ISO date this reading represents (the trip's actual date, even in climate_normal mode)
    temp_max_c: float
    temp_min_c: float
    precip_mm: float
    wind_max_kmh: float
    weathercode: int

    def to_dict(self) -> dict:
        return asdict(self)


def fetch_json(url: str) -> dict:
    """Thin wrapper around urlopen so tests can mock a single call point per module."""
    with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def is_within_forecast_horizon(start_date: date, today: date) -> bool:
    return (start_date - today).days <= FORECAST_HORIZON_DAYS


def _safe_replace_year(a_date: date, year: int) -> date:
    """Shift a date to a different year, falling back a day for Feb 29 in a non-leap target year."""
    try:
        return a_date.replace(year=year)
    except ValueError:
        return a_date.replace(year=year, day=28)


def _build_daily_url(base_url: str, latitude: float, longitude: float, start_date: date, end_date: date) -> str:
    params = urllib.parse.urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily": DAILY_FIELDS,
            "timezone": "auto",
        }
    )
    return f"{base_url}?{params}"


def _parse_daily_block(payload: dict) -> list[dict]:
    daily = payload.get("daily")
    if not daily or "time" not in daily:
        raise WeatherError("Malformed weather response: missing 'daily' block.")

    dates = daily["time"]
    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])
    wind = daily.get("windspeed_10m_max", [])
    codes = daily.get("weathercode", [])

    rows = []
    for i, day_iso in enumerate(dates):
        rows.append(
            {
                "day_date": day_iso,
                "temp_max_c": temp_max[i] if i < len(temp_max) else None,
                "temp_min_c": temp_min[i] if i < len(temp_min) else None,
                "precip_mm": precip[i] if i < len(precip) else None,
                "wind_max_kmh": wind[i] if i < len(wind) else None,
                "weathercode": codes[i] if i < len(codes) else None,
            }
        )
    return rows


def fetch_forecast(latitude: float, longitude: float, start_date: date, end_date: date) -> list[DailyWeather]:
    clipped_end = min(end_date, start_date + timedelta(days=FORECAST_HORIZON_DAYS))
    url = _build_daily_url(FORECAST_URL, latitude, longitude, start_date, clipped_end)
    try:
        payload = fetch_json(url)
    except (OSError, ValueError) as exc:
        raise WeatherError(f"Could not reach the forecast service: {exc}") from exc

    rows = _parse_daily_block(payload)
    return [DailyWeather(**row) for row in rows if None not in row.values()]


def fetch_climate_normal(latitude: float, longitude: float, start_date: date, end_date: date) -> list[DailyWeather]:
    """Average the same calendar date range across the past N years of archive data.

    A single failed year's fetch is skipped rather than aborting the whole trip
    (partial historical coverage is still a useful estimate).
    """
    per_year_rows: list[list[dict]] = []

    for years_back in range(1, CLIMATE_NORMAL_YEARS_BACK + 1):
        hist_start = _safe_replace_year(start_date, start_date.year - years_back)
        hist_end = _safe_replace_year(end_date, end_date.year - years_back)
        url = _build_daily_url(ARCHIVE_URL, latitude, longitude, hist_start, hist_end)
        try:
            payload = fetch_json(url)
            rows = _parse_daily_block(payload)
        except (OSError, ValueError, WeatherError):
            continue
        per_year_rows.append(rows)

    if not per_year_rows:
        raise WeatherError("No historical weather data could be retrieved for this destination.")

    trip_length = (end_date - start_date).days + 1
    usable_years = [rows for rows in per_year_rows if len(rows) >= trip_length]
    if not usable_years:
        raise WeatherError("Historical weather responses were too short to average.")

    averaged: list[DailyWeather] = []
    for day_offset in range(trip_length):
        trip_day = start_date + timedelta(days=day_offset)
        samples = [rows[day_offset] for rows in usable_years]
        samples = [s for s in samples if None not in s.values()]
        if not samples:
            continue
        averaged.append(
            DailyWeather(
                day_date=trip_day.isoformat(),
                temp_max_c=round(sum(s["temp_max_c"] for s in samples) / len(samples), 1),
                temp_min_c=round(sum(s["temp_min_c"] for s in samples) / len(samples), 1),
                precip_mm=round(sum(s["precip_mm"] for s in samples) / len(samples), 1),
                wind_max_kmh=round(sum(s["wind_max_kmh"] for s in samples) / len(samples), 1),
                weathercode=round(sum(s["weathercode"] for s in samples) / len(samples)),
            )
        )

    if not averaged:
        raise WeatherError("Historical weather data did not overlap with the requested trip dates.")

    return averaged


def get_weather_for_trip(
    latitude: float, longitude: float, start_date: date, end_date: date, today: date
) -> tuple[str, list[DailyWeather]]:
    """Return (mode, daily_readings) where mode is 'forecast' or 'climate_normal'."""
    if is_within_forecast_horizon(start_date, today):
        return "forecast", fetch_forecast(latitude, longitude, start_date, end_date)
    return "climate_normal", fetch_climate_normal(latitude, longitude, start_date, end_date)
