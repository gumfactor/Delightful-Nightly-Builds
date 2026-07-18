"""Client for Statistics Canada's Web Data Service (WDS) API (free, public, no authentication).

Docs: https://www.statcan.gc.ca/en/developers/wds/user-guide
Endpoint used: POST /t1/wds/rest/getDataFromVectorsAndLatestNPeriods
Request body: [{"vectorId": <int>, "latestN": <int>}]
Response shape:
[
    {
        "status": "SUCCESS",
        "object": {
            "vectorId": <int>,
            "vectorDataPoint": [
                {"refPer": "2026-06-01", "value": 161.1, ...},
                ...
            ]
        }
    }
]
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import date, datetime
from typing import List

from src.models import Observation

URL = "https://www150.statcan.gc.ca/t1/wds/rest/getDataFromVectorsAndLatestNPeriods"
REQUEST_TIMEOUT_SECONDS = 15


def fetch_statcan_vector(
    vector_id: int,
    series_label: str,
    unit: str,
    latest_n: int = 12,
) -> List[Observation]:
    """Fetch the latest N periods for one StatsCan WDS vector.

    Returns an empty list on any network, HTTP, or parsing failure rather
    than raising — a single indicator failing must never abort a full sync.
    """
    body = json.dumps([{"vectorId": vector_id, "latestN": latest_n}]).encode("utf-8")
    request = urllib.request.Request(
        URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                return []
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError, OSError):
        return []

    series_id = f"STATCAN_V{vector_id}"
    return _parse_statcan_payload(payload, series_id, series_label, unit)


def _parse_statcan_payload(
    payload: object,
    series_id: str,
    series_label: str,
    unit: str,
) -> List[Observation]:
    if not isinstance(payload, list) or not payload:
        return []

    result_entry = payload[0]
    if not isinstance(result_entry, dict) or result_entry.get("status") != "SUCCESS":
        return []

    data_object = result_entry.get("object")
    if not isinstance(data_object, dict):
        return []

    points = data_object.get("vectorDataPoint")
    if not isinstance(points, list):
        return []

    parsed: List[Observation] = []
    for point in points:
        if not isinstance(point, dict):
            continue
        obs_date = _parse_date(point.get("refPer"))
        try:
            value = float(point.get("value"))
        except (TypeError, ValueError):
            continue
        if obs_date is None:
            continue
        parsed.append(
            Observation(
                series_id=series_id,
                series_label=series_label,
                unit=unit,
                source="Statistics Canada WDS",
                obs_date=obs_date,
                value=value,
            )
        )
    return parsed


def _parse_date(raw: object) -> date | None:
    if not isinstance(raw, str):
        return None
    normalized = raw[:10]
    try:
        return datetime.strptime(normalized, "%Y-%m-%d").date()
    except ValueError:
        return None
