"""HTTP fetchers for Bank of Canada Valet and Statistics Canada WDS."""
from __future__ import annotations

import json
import re
import urllib.request
from typing import Any, Callable

from . import config

Point = list  # [iso_date, float]
Fetcher = Callable[[str, bytes | None], Any]

USER_AGENT = "canpulse/1.0 (personal dashboard)"


def http_json(url: str, body: bytes | None = None, timeout: int = 30) -> Any:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed https hosts
        return json.loads(resp.read().decode("utf-8"))


def _iso_date(raw: str) -> str:
    """Normalise 'YYYY-MM' / 'YYYY-MM-DD' / 'YYYY-MM-DDTHH:MM:SS' to YYYY-MM-DD."""
    raw = raw[:10]
    if re.fullmatch(r"\d{4}-\d{2}", raw):
        return raw + "-01"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return raw
    raise ValueError(f"unrecognised date: {raw!r}")


def parse_valet(payload: dict, series: str) -> list[Point]:
    points: list[Point] = []
    for obs in payload.get("observations", []):
        cell = obs.get(series)
        if not cell or cell.get("v") in (None, ""):
            continue
        try:
            points.append([_iso_date(obs["d"]), float(cell["v"])])
        except (ValueError, KeyError):
            continue
    points.sort(key=lambda p: p[0])
    return points


def parse_wds(payload: Any, vector: int) -> tuple[list[Point], str | None]:
    """Return (points, scalar_note) for one vector from a WDS response list."""
    for item in payload:
        if item.get("status") != "SUCCESS":
            continue
        obj = item.get("object", {})
        if obj.get("vectorId") != vector:
            continue
        points = []
        for pt in obj.get("vectorDataPoint", []):
            val = pt.get("value")
            if val in (None, ""):
                continue
            points.append([_iso_date(pt["refPer"]), float(val)])
        points.sort(key=lambda p: p[0])
        return points, None
    raise ValueError(f"vector {vector} missing or not SUCCESS in response")


def fetch_valet(series: str, fetch: Fetcher = http_json, years: int = 25) -> list[Point]:
    url = f"{config.VALET_BASE}/{series}/json?recent={years * 260}"
    points = parse_valet(fetch(url, None), series)
    if not points:
        raise ValueError(f"Valet returned no observations for {series}")
    return points


def fetch_wds(vector: int, fetch: Fetcher = http_json, latest_n: int = 360) -> list[Point]:
    body = json.dumps([{"vectorId": vector, "latestN": latest_n}]).encode()
    points, _ = parse_wds(fetch(config.WDS_URL, body), vector)
    if not points:
        raise ValueError(f"WDS returned no data points for vector {vector}")
    return points


def fetch_indicator(spec: dict[str, Any], fetch: Fetcher = http_json) -> list[Point]:
    if spec["source"] == "valet":
        return fetch_valet(spec["series"], fetch)
    if spec["source"] == "statcan":
        return fetch_wds(spec["vector"], fetch)
    raise ValueError(f"unknown source {spec['source']!r}")


def fetch_all(fetch: Fetcher = http_json,
              specs: list[dict[str, Any]] | None = None) -> tuple[dict[str, dict], dict[str, str]]:
    """Fetch every indicator independently; failures are collected, never raised."""
    series: dict[str, dict] = {}
    errors: dict[str, str] = {}
    for spec in specs if specs is not None else config.INDICATORS:
        try:
            points = fetch_indicator(spec, fetch)
        except Exception as exc:  # noqa: BLE001 - isolate each source
            errors[spec["id"]] = f"{type(exc).__name__}: {exc}"[:200]
            continue
        series[spec["id"]] = {k: spec[k] for k in ("id", "label", "unit", "source", "freq",
                                                    "higher_is", "group")} | {"points": points}
    return series, errors


def verify_vectors(fetch: Fetcher = http_json,
                   specs: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Check each StatCan vector's published title contains the expected keyword."""
    results = []
    for spec in specs if specs is not None else config.INDICATORS:
        if spec["source"] != "statcan":
            continue
        entry = {"id": spec["id"], "vector": spec["vector"], "ok": False, "title": ""}
        try:
            body = json.dumps([{"vectorId": spec["vector"]}]).encode()
            resp = fetch(config.WDS_INFO_URL, body)
            obj = resp[0]["object"]
            title = f"{obj.get('SeriesTitleEn', '')} ({obj.get('productId', '')})"
            entry["title"] = title
            entry["ok"] = spec["expect"].lower() in title.lower()
        except Exception as exc:  # noqa: BLE001
            entry["title"] = f"error: {exc}"[:150]
        results.append(entry)
    return results
