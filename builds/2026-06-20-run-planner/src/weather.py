"""Open-Meteo weather fetch and running-comfort scoring."""

import json
import urllib.request
from datetime import datetime
from typing import List, Optional

_BASE_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}"
    "&hourly=apparent_temperature,wind_speed_10m,precipitation_probability"
    "&timezone=America%2FToronto"
    "&forecast_days=7"
)

DEFAULT_LAT = 43.65
DEFAULT_LON = -79.38  # Toronto


def fetch_forecast(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON) -> dict:
    """Fetch hourly forecast from Open-Meteo (no auth required)."""
    url = _BASE_URL.format(lat=lat, lon=lon)
    req = urllib.request.Request(url, headers={"User-Agent": "run-planner/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def temp_score(apparent_temp_c: float) -> float:
    """Score 0–100 for running comfort based on feels-like temperature."""
    t = apparent_temp_c
    if t < -10:
        return 10.0
    if t < 0:
        return 20.0 + (t + 10) * 2.0        # 20–40 over -10→0
    if t < 5:
        return 40.0 + (t - 0) * 10.0        # 40–90 over 0→5
    if t <= 15:
        return 90.0 + (t - 5) * 1.0         # 90–100 over 5→15
    if t <= 20:
        return 100.0 - (t - 15) * 3.0       # 85–100 over 15→20
    if t <= 25:
        return 85.0 - (t - 20) * 3.0        # 70–85 over 20→25
    if t <= 30:
        return 70.0 - (t - 25) * 4.0        # 50–70 over 25→30
    return max(10.0, 50.0 - (t - 30) * 5.0)


def wind_score(wind_speed_kmh: float) -> float:
    """Score 0–100 for running comfort based on wind speed."""
    w = wind_speed_kmh
    if w <= 10:
        return 100.0
    if w <= 20:
        return 100.0 - (w - 10) * 2.0       # 80–100 over 10→20
    if w <= 30:
        return 80.0 - (w - 20) * 2.0        # 60–80 over 20→30
    if w <= 50:
        return 60.0 - (w - 30) * 1.5        # 30–60 over 30→50
    return max(0.0, 30.0 - (w - 50) * 1.0)


def precip_score(precip_probability: float) -> float:
    """Score 0–100 based on precipitation probability (0–100%)."""
    p = precip_probability
    if p <= 10:
        return 100.0
    if p <= 30:
        return 100.0 - (p - 10) * 1.5       # 70–100 over 10→30
    if p <= 60:
        return 70.0 - (p - 30) * 1.5        # 25–70 over 30→60
    return max(0.0, 25.0 - (p - 60) * 0.5)


def composite_score(
    apparent_temp_c: float,
    wind_speed_kmh: float,
    precip_probability: float,
) -> float:
    """Weighted composite: temperature 45%, precipitation 30%, wind 25%."""
    ts = temp_score(apparent_temp_c)
    ws = wind_score(wind_speed_kmh)
    ps = precip_score(precip_probability)
    return round(ts * 0.45 + ps * 0.30 + ws * 0.25, 1)


def score_label(score: float) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Fair"
    return "Poor"


def parse_forecast(raw: dict) -> List[dict]:
    """Convert Open-Meteo hourly dict into a list of scored hour records."""
    hourly = raw.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("apparent_temperature", [])
    winds = hourly.get("wind_speed_10m", [])
    precips = hourly.get("precipitation_probability", [])

    results = []
    for i, t in enumerate(times):
        if i >= len(temps) or i >= len(winds) or i >= len(precips):
            break
        temp = temps[i] if temps[i] is not None else 15.0
        wind = winds[i] if winds[i] is not None else 0.0
        precip = precips[i] if precips[i] is not None else 0.0

        score = composite_score(temp, wind, precip)
        results.append({
            "time": t,
            "apparent_temp_c": round(temp, 1),
            "wind_speed_kmh": round(wind, 1),
            "precip_probability": round(precip, 1),
            "score": score,
            "label": score_label(score),
        })
    return results


def best_windows(forecast_hours: List[dict], top_n: int = 5) -> List[dict]:
    """Return the top N daytime (6am–8pm) hours sorted by running score descending."""
    daytime = []
    for h in forecast_hours:
        try:
            dt = datetime.fromisoformat(h["time"])
            if 6 <= dt.hour <= 20:
                daytime.append(h)
        except (ValueError, KeyError):
            continue
    return sorted(daytime, key=lambda x: x["score"], reverse=True)[:top_n]
