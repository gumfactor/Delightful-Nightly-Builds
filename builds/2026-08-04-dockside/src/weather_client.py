"""Open-Meteo API clients: geocoding, forecast, and marine data.

stdlib-only (urllib). Every call here is mocked in tests - see
tests/test_weather_client.py - so none of these functions are ever invoked
against the live network during the test suite.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"

REQUEST_TIMEOUT_SECONDS = 10


class WeatherClientError(Exception):
    """Raised when an Open-Meteo request fails or returns unusable data."""


@dataclass(frozen=True)
class GeocodeResult:
    name: str
    latitude: float
    longitude: float
    country: Optional[str] = None
    admin1: Optional[str] = None


@dataclass(frozen=True)
class DailyForecast:
    obs_date: date
    temp_min_c: Optional[float]
    temp_max_c: Optional[float]
    precip_mm: Optional[float]
    wind_speed_max_kmh: Optional[float]


@dataclass(frozen=True)
class DailyMarine:
    obs_date: date
    wave_height_max_m: Optional[float]
    water_temp_c: Optional[float]


def _http_get_json(url: str, params: dict) -> dict:
    query = urllib.parse.urlencode(params)
    full_url = f"{url}?{query}"
    try:
        with urllib.request.urlopen(full_url, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            if resp.status != 200:
                raise WeatherClientError(f"HTTP {resp.status} from {url}")
            body = resp.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise WeatherClientError(f"Request to {url} failed: {exc}") from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise WeatherClientError(f"Invalid JSON from {url}: {exc}") from exc


def _safe_get(values: list, index: int):
    if 0 <= index < len(values):
        return values[index]
    return None


def geocode(place_name: str) -> GeocodeResult:
    data = _http_get_json(GEOCODING_URL, {
        "name": place_name,
        "count": 1,
        "language": "en",
        "format": "json",
    })
    results = data.get("results") or []
    if not results:
        raise WeatherClientError(f"No geocoding match for '{place_name}'")
    r = results[0]
    return GeocodeResult(
        name=r.get("name", place_name),
        latitude=float(r["latitude"]),
        longitude=float(r["longitude"]),
        country=r.get("country"),
        admin1=r.get("admin1"),
    )


def fetch_forecast(latitude: float, longitude: float, forecast_days: int = 7) -> list:
    data = _http_get_json(FORECAST_URL, {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "timezone": "auto",
        "forecast_days": forecast_days,
    })
    daily = data.get("daily") or {}
    times = daily.get("time") or []
    tmax = daily.get("temperature_2m_max") or []
    tmin = daily.get("temperature_2m_min") or []
    precip = daily.get("precipitation_sum") or []
    wind = daily.get("wind_speed_10m_max") or []

    results = []
    for i, t in enumerate(times):
        results.append(DailyForecast(
            obs_date=datetime.strptime(t, "%Y-%m-%d").date(),
            temp_min_c=_safe_get(tmin, i),
            temp_max_c=_safe_get(tmax, i),
            precip_mm=_safe_get(precip, i),
            wind_speed_max_kmh=_safe_get(wind, i),
        ))
    return results


def _pick_midday_hourly(hourly_times: list, hourly_values: list, target_date: str) -> Optional[float]:
    """Picks the hourly value at 12:00 local time for target_date; falls back
    to the first available non-null hour of that date; returns None if
    there's no data for that date at all."""
    midday_key = f"{target_date}T12:00"
    fallback_value = None
    for i, ts in enumerate(hourly_times):
        if not ts.startswith(target_date):
            continue
        value = _safe_get(hourly_values, i)
        if fallback_value is None and value is not None:
            fallback_value = value
        if ts == midday_key and value is not None:
            return value
    return fallback_value


def fetch_marine(latitude: float, longitude: float, forecast_days: int = 7) -> list:
    """Best-effort marine data fetch.

    Returns [] (not an exception) whenever the location has no marine model
    coverage - many inland lakes fall outside Open-Meteo's marine model
    grid. Callers treat an empty list as "marine data unavailable for this
    site" rather than a hard failure.
    """
    try:
        data = _http_get_json(MARINE_URL, {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "wave_height_max",
            "hourly": "sea_surface_temperature",
            "timezone": "auto",
            "forecast_days": forecast_days,
        })
    except WeatherClientError:
        return []

    daily = data.get("daily") or {}
    times = daily.get("time") or []
    waves = daily.get("wave_height_max") or []
    if not times or all(w is None for w in waves):
        return []

    hourly = data.get("hourly") or {}
    hourly_times = hourly.get("time") or []
    hourly_temps = hourly.get("sea_surface_temperature") or []

    results = []
    for i, t in enumerate(times):
        results.append(DailyMarine(
            obs_date=datetime.strptime(t, "%Y-%m-%d").date(),
            wave_height_max_m=_safe_get(waves, i),
            water_temp_c=_pick_midday_hourly(hourly_times, hourly_temps, t),
        ))
    return results
