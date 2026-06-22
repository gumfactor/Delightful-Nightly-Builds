"""Weather fetcher — Open-Meteo hourly forecast with activity scoring."""
from __future__ import annotations

import json
import urllib.request
from datetime import date, datetime, timezone
from typing import Any

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def score_hour(temp_c: float, wind_kph: float, precip_prob: float) -> dict[str, float]:
    """Score a single hour for running, golf, and boating comfort (0–100 each)."""
    # --- Running: ideal 10–20°C, low wind, no rain ---
    run = 100.0
    if temp_c < 0 or temp_c > 35:
        run -= 60
    elif temp_c < 5 or temp_c > 28:
        run -= 30
    elif temp_c < 10 or temp_c > 25:
        run -= 15
    if wind_kph > 40:
        run -= 40
    elif wind_kph > 25:
        run -= 20
    elif wind_kph > 15:
        run -= 10
    run -= precip_prob * 0.6

    # --- Golf: ideal 15–25°C, wind < 20 kph, dry ---
    golf = 100.0
    if temp_c < 5 or temp_c > 35:
        golf -= 70
    elif temp_c < 10 or temp_c > 32:
        golf -= 40
    elif temp_c < 15 or temp_c > 28:
        golf -= 15
    if wind_kph > 30:
        golf -= 50
    elif wind_kph > 20:
        golf -= 25
    elif wind_kph > 12:
        golf -= 10
    golf -= precip_prob * 0.8

    # --- Boating: ideal 20–28°C, moderate wind 5–20 kph ---
    boat = 100.0
    if temp_c < 10 or temp_c > 35:
        boat -= 70
    elif temp_c < 18 or temp_c > 32:
        boat -= 30
    if wind_kph > 35:
        boat -= 60
    elif wind_kph > 25:
        boat -= 20
    elif wind_kph < 5:
        boat -= 10
    boat -= precip_prob * 0.5

    return {
        "run": max(0.0, round(run, 1)),
        "golf": max(0.0, round(golf, 1)),
        "boat": max(0.0, round(boat, 1)),
    }


def get_best_windows(
    hours: list[dict],
    activity: str = "run",
    top_n: int = 3,
) -> list[dict]:
    """Return the top N hours for an activity, restricted to 6am–9pm, sorted descending."""
    daylight = [h for h in hours if 6 <= h.get("hour", 0) <= 21]
    return sorted(daylight, key=lambda h: h["scores"].get(activity, 0), reverse=True)[:top_n]


def parse_forecast_response(data: dict, target_date: date) -> list[dict]:
    """Parse Open-Meteo API JSON into per-hour records for a specific date."""
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("apparent_temperature", [])
    winds = hourly.get("wind_speed_10m", [])
    precips = hourly.get("precipitation_probability", [])

    result = []
    for i, time_str in enumerate(times):
        try:
            dt = datetime.fromisoformat(time_str)
        except ValueError:
            continue
        if dt.date() != target_date:
            continue

        temp = temps[i] if i < len(temps) and temps[i] is not None else 15.0
        wind = winds[i] if i < len(winds) and winds[i] is not None else 0.0
        precip = precips[i] if i < len(precips) and precips[i] is not None else 0.0

        result.append({
            "time": time_str,
            "hour": dt.hour,
            "temp_c": round(float(temp), 1),
            "wind_kph": round(float(wind), 1),
            "precip_prob": round(float(precip), 1),
            "scores": score_hour(float(temp), float(wind), float(precip)),
        })
    return result


def fetch_weather(lat: float, lon: float, target_date: date | None = None) -> dict:
    """Fetch hourly forecast from Open-Meteo and return scored hours + best windows."""
    if target_date is None:
        target_date = datetime.now(timezone.utc).date()

    params = (
        f"?latitude={lat}&longitude={lon}"
        f"&hourly=apparent_temperature,wind_speed_10m,precipitation_probability"
        f"&forecast_days=2&wind_speed_unit=kmh&timezone=auto"
    )

    try:
        with urllib.request.urlopen(f"{OPEN_METEO_URL}{params}", timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as exc:
        return {"error": str(exc), "hours": [], "best_run": [], "best_golf": [], "best_boat": []}

    hours = parse_forecast_response(data, target_date)
    return {
        "date": target_date.isoformat(),
        "hours": hours,
        "best_run": get_best_windows(hours, "run", 3),
        "best_golf": get_best_windows(hours, "golf", 3),
        "best_boat": get_best_windows(hours, "boat", 3),
    }
