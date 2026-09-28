"""Client for the Open-Meteo Forecast API (free, no auth required).

Docs: https://open-meteo.com/en/docs
The HTTP transport is injectable so tests never make a real network call.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Callable, List, TypedDict

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

DAILY_VARS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_probability_max",
    "precipitation_sum",
    "windspeed_10m_max",
    "windgusts_10m_max",
    "uv_index_max",
    "weathercode",
]


class DailyForecast(TypedDict):
    date: str
    temp_max: float
    temp_min: float
    precip_prob_max: float
    precip_sum: float
    wind_max: float
    windgust_max: float
    uv_index_max: float
    weathercode: int


class WeatherClientError(Exception):
    pass


Transport = Callable[[str], str]


def default_transport(url: str) -> str:
    with urllib.request.urlopen(url, timeout=15) as response:
        if response.status != 200:
            raise WeatherClientError(f"Open-Meteo forecast API returned HTTP {response.status}")
        return response.read().decode("utf-8")


class WeatherClient:
    def __init__(self, transport: Transport = default_transport):
        self._transport = transport

    def build_url(self, lat: float, lon: float, days: int) -> str:
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ",".join(DAILY_VARS),
            "forecast_days": days,
            "timezone": "auto",
        }
        return f"{FORECAST_URL}?{urllib.parse.urlencode(params)}"

    def get_daily_forecast(self, lat: float, lon: float, days: int = 7) -> List[DailyForecast]:
        url = self.build_url(lat, lon, days)
        try:
            raw = self._transport(url)
        except WeatherClientError:
            raise
        except Exception as exc:  # network failure, timeout, etc.
            raise WeatherClientError(f"Failed to reach Open-Meteo forecast API: {exc}") from exc

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise WeatherClientError(f"Open-Meteo forecast API returned invalid JSON: {exc}") from exc

        if "daily" not in payload:
            raise WeatherClientError("Open-Meteo forecast response missing 'daily' block")

        daily = payload["daily"]
        try:
            dates = daily["time"]
            records: List[DailyForecast] = []
            for i, date in enumerate(dates):
                records.append(DailyForecast(
                    date=date,
                    temp_max=daily["temperature_2m_max"][i],
                    temp_min=daily["temperature_2m_min"][i],
                    precip_prob_max=daily["precipitation_probability_max"][i],
                    precip_sum=daily["precipitation_sum"][i],
                    wind_max=daily["windspeed_10m_max"][i],
                    windgust_max=daily["windgusts_10m_max"][i],
                    uv_index_max=daily["uv_index_max"][i],
                    weathercode=daily["weathercode"][i],
                ))
            return records
        except (KeyError, IndexError) as exc:
            raise WeatherClientError(f"Open-Meteo forecast response missing expected field: {exc}") from exc
