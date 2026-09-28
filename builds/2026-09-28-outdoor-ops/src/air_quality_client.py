"""Client for the Open-Meteo Air Quality API (free, no auth required).

Docs: https://open-meteo.com/en/docs/air-quality-api
The API returns hourly US AQI and PM2.5; this module aggregates those hours
into daily max/mean values keyed by date, matching the daily grain the
weather client and scoring engine use.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections import defaultdict
from typing import Callable, Dict, List, TypedDict

AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

HOURLY_VARS = ["us_aqi", "pm2_5"]


class DailyAirQuality(TypedDict):
    date: str
    aqi_max: float
    aqi_mean: float
    pm25_mean: float


class AirQualityClientError(Exception):
    pass


Transport = Callable[[str], str]


def default_transport(url: str) -> str:
    with urllib.request.urlopen(url, timeout=15) as response:
        if response.status != 200:
            raise AirQualityClientError(f"Open-Meteo air quality API returned HTTP {response.status}")
        return response.read().decode("utf-8")


class AirQualityClient:
    def __init__(self, transport: Transport = default_transport):
        self._transport = transport

    def build_url(self, lat: float, lon: float, days: int) -> str:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(HOURLY_VARS),
            "forecast_days": days,
            "timezone": "auto",
        }
        return f"{AIR_QUALITY_URL}?{urllib.parse.urlencode(params)}"

    def get_daily_air_quality(self, lat: float, lon: float, days: int = 7) -> List[DailyAirQuality]:
        url = self.build_url(lat, lon, days)
        try:
            raw = self._transport(url)
        except AirQualityClientError:
            raise
        except Exception as exc:
            raise AirQualityClientError(f"Failed to reach Open-Meteo air quality API: {exc}") from exc

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AirQualityClientError(f"Open-Meteo air quality API returned invalid JSON: {exc}") from exc

        if "hourly" not in payload:
            raise AirQualityClientError("Open-Meteo air quality response missing 'hourly' block")

        hourly = payload["hourly"]
        try:
            timestamps = hourly["time"]
            aqi_values = hourly["us_aqi"]
            pm25_values = hourly["pm2_5"]
        except KeyError as exc:
            raise AirQualityClientError(f"Open-Meteo air quality response missing expected field: {exc}") from exc

        by_date_aqi: Dict[str, List[float]] = defaultdict(list)
        by_date_pm25: Dict[str, List[float]] = defaultdict(list)
        for i, timestamp in enumerate(timestamps):
            date = timestamp.split("T")[0]
            aqi = aqi_values[i] if i < len(aqi_values) else None
            pm25 = pm25_values[i] if i < len(pm25_values) else None
            if aqi is not None:
                by_date_aqi[date].append(aqi)
            if pm25 is not None:
                by_date_pm25[date].append(pm25)

        records: List[DailyAirQuality] = []
        for date in sorted(by_date_aqi.keys()):
            aqi_hours = by_date_aqi[date]
            pm25_hours = by_date_pm25.get(date, [])
            records.append(DailyAirQuality(
                date=date,
                aqi_max=max(aqi_hours) if aqi_hours else 0.0,
                aqi_mean=round(sum(aqi_hours) / len(aqi_hours), 1) if aqi_hours else 0.0,
                pm25_mean=round(sum(pm25_hours) / len(pm25_hours), 1) if pm25_hours else 0.0,
            ))
        return records
