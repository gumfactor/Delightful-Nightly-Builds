"""Client for the Bank of Canada Valet API (free, public, no authentication).

Docs: https://www.bankofcanada.ca/valet/docs
Endpoint shape used: GET /valet/observations/{series}/json?recent=N
Response shape:
{
    "seriesDetail": {"<series>": {"label": "...", "description": "..."}},
    "observations": [
        {"d": "2026-07-14", "<series>": {"v": "1.3689"}},
        ...
    ]
}
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import date, datetime
from typing import List

from src.models import Observation

BASE_URL = "https://www.bankofcanada.ca/valet/observations"
REQUEST_TIMEOUT_SECONDS = 15


def fetch_boc_series(
    series_id: str,
    series_label: str,
    unit: str,
    recent: int = 30,
) -> List[Observation]:
    """Fetch recent observations for one Bank of Canada Valet series.

    Returns an empty list on any network, HTTP, or parsing failure rather
    than raising — a single indicator failing must never abort a full sync.
    """
    url = f"{BASE_URL}/{series_id}/json?recent={recent}"
    try:
        with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                return []
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError, OSError):
        return []

    return _parse_boc_payload(payload, series_id, series_label, unit)


def _parse_boc_payload(
    payload: dict,
    series_id: str,
    series_label: str,
    unit: str,
) -> List[Observation]:
    observations = payload.get("observations")
    if not isinstance(observations, list):
        return []

    parsed: List[Observation] = []
    for row in observations:
        if not isinstance(row, dict):
            continue
        obs_date = _parse_date(row.get("d"))
        series_field = row.get(series_id)
        if obs_date is None or not isinstance(series_field, dict):
            continue
        raw_value = series_field.get("v")
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        parsed.append(
            Observation(
                series_id=series_id,
                series_label=series_label,
                unit=unit,
                source="Bank of Canada Valet",
                obs_date=obs_date,
                value=value,
            )
        )
    return parsed


def _parse_date(raw: object) -> date | None:
    if not isinstance(raw, str):
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None
