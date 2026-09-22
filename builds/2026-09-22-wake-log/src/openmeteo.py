"""Open-Meteo forecast client and window aggregation.

Open-Meteo (https://open-meteo.com) is a free, no-auth weather API. This
module builds the request, parses the response into per-day window
aggregates (morning/afternoon/evening, clipped to daylight), and computes
each window's boating comfort score via scoring.py.

Only `urllib.request` is used -- no third-party HTTP dependency.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, time
from typing import Dict, List, Optional

from . import scoring

BASE_URL = "https://api.open-meteo.com/v1/forecast"

HOURLY_FIELDS = "temperature_2m,precipitation_probability,windspeed_10m,windgusts_10m,cloudcover"
DAILY_FIELDS = "sunrise,sunset"

# (label, start_hour_inclusive, end_hour_exclusive)
WINDOWS = [
    ("morning", 6, 12),
    ("afternoon", 12, 18),
    ("evening", 18, 22),
]


class OpenMeteoError(Exception):
    """Raised when the Open-Meteo API cannot be reached or returns an
    unparseable/incomplete response."""


@dataclass
class WindowAggregate:
    date: str
    window: str
    wind_knots: float
    gust_knots: float
    temp_c: float
    precip_probability: float
    cloud_cover: float
    daylight_hours: float
    beaufort_number: int
    beaufort_name: str
    score: float


def build_url(latitude: float, longitude: float, forecast_days: int = 7) -> str:
    if not (-90.0 <= latitude <= 90.0):
        raise ValueError(f"latitude out of range: {latitude}")
    if not (-180.0 <= longitude <= 180.0):
        raise ValueError(f"longitude out of range: {longitude}")
    if not (1 <= forecast_days <= 10):
        raise ValueError("forecast_days must be between 1 and 10")
    return (
        f"{BASE_URL}?latitude={latitude}&longitude={longitude}"
        f"&hourly={HOURLY_FIELDS}&daily={DAILY_FIELDS}"
        f"&windspeed_unit=kn&timezone=auto&forecast_days={forecast_days}"
    )


def fetch_forecast(latitude: float, longitude: float, forecast_days: int = 7, timeout: int = 15) -> dict:
    """Fetch the raw forecast JSON from Open-Meteo. Raises OpenMeteoError on
    any network or HTTP failure."""
    url = build_url(latitude, longitude, forecast_days)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.URLError as exc:
        raise OpenMeteoError(f"failed to reach Open-Meteo: {exc}") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise OpenMeteoError(f"Open-Meteo returned unparseable JSON: {exc}") from exc


def _parse_hour(iso_str: str) -> datetime:
    return datetime.fromisoformat(iso_str)


def _daylight_bounds_for_date(payload: dict, date_str: str) -> Optional[tuple]:
    daily = payload.get("daily", {})
    dates = daily.get("time", [])
    sunrises = daily.get("sunrise", [])
    sunsets = daily.get("sunset", [])
    if date_str not in dates:
        return None
    idx = dates.index(date_str)
    if idx >= len(sunrises) or idx >= len(sunsets):
        return None
    return _parse_hour(sunrises[idx]).time(), _parse_hour(sunsets[idx]).time()


def parse_forecast(payload: dict) -> List[WindowAggregate]:
    """Turn a raw Open-Meteo response into scored window aggregates."""
    hourly = payload.get("hourly")
    if not hourly:
        raise OpenMeteoError("response missing 'hourly' section")

    required = ("time", "temperature_2m", "precipitation_probability", "windspeed_10m", "windgusts_10m", "cloudcover")
    for field in required:
        if field not in hourly:
            raise OpenMeteoError(f"response missing required hourly field: {field}")

    times = hourly["time"]
    n = len(times)
    for field in required[1:]:
        if len(hourly[field]) != n:
            raise OpenMeteoError(f"hourly field '{field}' length mismatch")

    # Group hour indices by date.
    by_date: Dict[str, List[int]] = {}
    for i, t in enumerate(times):
        date_str = t.split("T")[0]
        by_date.setdefault(date_str, []).append(i)

    aggregates: List[WindowAggregate] = []
    for date_str, indices in by_date.items():
        daylight = _daylight_bounds_for_date(payload, date_str)
        for label, start_hour, end_hour in WINDOWS:
            window_indices = []
            daylight_hours = 0.0
            for i in indices:
                hour = _parse_hour(times[i])
                if not (start_hour <= hour.hour < end_hour):
                    continue
                window_indices.append(i)
                if daylight is not None:
                    sunrise, sunset = daylight
                    if sunrise <= hour.time() < sunset:
                        daylight_hours += 1.0

            if not window_indices:
                continue

            wind_vals = [hourly["windspeed_10m"][i] for i in window_indices]
            gust_vals = [hourly["windgusts_10m"][i] for i in window_indices]
            temp_vals = [hourly["temperature_2m"][i] for i in window_indices]
            precip_vals = [hourly["precipitation_probability"][i] for i in window_indices]
            cloud_vals = [hourly["cloudcover"][i] for i in window_indices]

            wind_knots = sum(wind_vals) / len(wind_vals)
            gust_knots = max(gust_vals)
            temp_c = sum(temp_vals) / len(temp_vals)
            precip_probability = max(precip_vals)
            cloud_cover = sum(cloud_vals) / len(cloud_vals)

            beaufort = scoring.classify_beaufort(wind_knots)
            score = scoring.comfort_score(
                wind_knots=wind_knots,
                gust_knots=gust_knots,
                precip_probability=precip_probability,
                temp_c=temp_c,
                cloud_cover_pct=cloud_cover,
                daylight_hours=daylight_hours,
            )

            aggregates.append(
                WindowAggregate(
                    date=date_str,
                    window=label,
                    wind_knots=round(wind_knots, 1),
                    gust_knots=round(gust_knots, 1),
                    temp_c=round(temp_c, 1),
                    precip_probability=round(precip_probability, 1),
                    cloud_cover=round(cloud_cover, 1),
                    daylight_hours=daylight_hours,
                    beaufort_number=beaufort.number,
                    beaufort_name=beaufort.name,
                    score=score,
                )
            )

    aggregates.sort(key=lambda a: (a.date, a.window))
    return aggregates


def get_scored_windows(latitude: float, longitude: float, forecast_days: int = 7) -> List[WindowAggregate]:
    """Convenience wrapper: fetch + parse in one call."""
    payload = fetch_forecast(latitude, longitude, forecast_days)
    return parse_forecast(payload)


def best_window(windows: List[WindowAggregate]) -> Optional[WindowAggregate]:
    """Return the highest-scoring window, or None if the list is empty or
    every window scored 0 (e.g. no daylight overlap anywhere)."""
    usable = [w for w in windows if w.score > 0]
    if not usable:
        return None
    return max(usable, key=lambda w: w.score)
