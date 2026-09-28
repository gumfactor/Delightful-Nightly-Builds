"""Outdoor Ops CLI: sync, render, demo."""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import List, Optional

from . import ai_note, dashboard, fixtures, scoring, summary
from .air_quality_client import AirQualityClient, AirQualityClientError
from .storage import SnapshotRow, Storage
from .weather_client import WeatherClient, WeatherClientError

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "outdoor_ops.db"
DEFAULT_HTML_PATH = Path(__file__).resolve().parent.parent / "outdoor_ops.html"
DEFAULT_LOCATION_NAME = "Toronto, ON"
DEFAULT_LAT = 43.6532
DEFAULT_LON = -79.3832
NO_DATA_NOTE = "No data yet — run `sync` (or `demo`) first, then `render`."


def _score_row(forecast: dict, air_quality: Optional[dict], location_name: str, lat: float, lon: float,
                sync_day: str, fetched_at: str) -> SnapshotRow:
    aqi_max = air_quality["aqi_max"] if air_quality else 0.0
    aqi_mean = air_quality["aqi_mean"] if air_quality else 0.0
    pm25_mean = air_quality["pm25_mean"] if air_quality else 0.0

    conditions = scoring.DayConditions(
        temp_max=forecast["temp_max"],
        wind_max=forecast["wind_max"],
        precip_prob_max=forecast["precip_prob_max"],
        aqi_max=aqi_max,
        uv_index_max=forecast["uv_index_max"],
    )
    return SnapshotRow(
        location_name=location_name, lat=lat, lon=lon,
        forecast_date=forecast["date"], sync_day=sync_day, fetched_at=fetched_at,
        temp_max=forecast["temp_max"], temp_min=forecast["temp_min"],
        precip_prob_max=forecast["precip_prob_max"], precip_sum=forecast["precip_sum"],
        wind_max=forecast["wind_max"], windgust_max=forecast["windgust_max"],
        uv_index_max=forecast["uv_index_max"], weathercode=forecast["weathercode"],
        aqi_max=aqi_max, aqi_mean=aqi_mean, pm25_mean=pm25_mean,
        running_score=scoring.running_score(conditions),
        golf_score=scoring.golf_score(conditions),
    )


def build_rows(forecasts: List[dict], air_qualities: List[dict], location_name: str,
                lat: float, lon: float, now: dt.datetime) -> List[SnapshotRow]:
    aqi_by_date = {aq["date"]: aq for aq in air_qualities}
    sync_day = now.date().isoformat()
    fetched_at = now.isoformat()
    return [
        _score_row(forecast, aqi_by_date.get(forecast["date"]), location_name, lat, lon, sync_day, fetched_at)
        for forecast in forecasts
    ]


def cmd_sync(args: argparse.Namespace) -> int:
    weather_client = WeatherClient()
    air_quality_client = AirQualityClient()
    try:
        forecasts = weather_client.get_daily_forecast(args.lat, args.lon, days=args.days)
        air_qualities = air_quality_client.get_daily_air_quality(args.lat, args.lon, days=args.days)
    except (WeatherClientError, AirQualityClientError) as exc:
        print(f"Sync failed: {exc}", file=sys.stderr)
        return 1

    rows = build_rows(forecasts, air_qualities, args.location, args.lat, args.lon, dt.datetime.now(dt.timezone.utc))
    with Storage(Path(args.db)) as storage:
        storage.upsert_snapshots(rows)
    print(f"Synced {len(rows)} days for {args.location}.")
    return 0


def _render_from_rows(rows: List, location_name: str, sync_count: int, last_sync_time: Optional[str],
                       api_key: Optional[str], html_path: Path) -> None:
    days = [dict(row) for row in rows]
    if days:
        week_summary = summary.build_week_summary(days)
        note = ai_note.generate_note(week_summary, api_key=api_key)
    else:
        week_summary = {}
        note = NO_DATA_NOTE

    html_content = dashboard.render_dashboard(
        location_name=location_name,
        days=days,
        summary=week_summary,
        coach_note=note,
        sync_count=sync_count,
        last_sync_time=last_sync_time,
    )
    html_path.write_text(html_content, encoding="utf-8")
    print(f"Dashboard written to {html_path}")


def cmd_render(args: argparse.Namespace) -> int:
    with Storage(Path(args.db)) as storage:
        rows = storage.latest_snapshots(args.location)
        sync_count = storage.sync_count(args.location)
        last_sync_time = storage.last_sync_time(args.location)
    _render_from_rows(rows, args.location, sync_count, last_sync_time, None, Path(args.out))
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    now = dt.datetime.now(dt.timezone.utc)
    rows = build_rows(fixtures.DEMO_FORECAST, fixtures.DEMO_AIR_QUALITY,
                       fixtures.DEMO_LOCATION_NAME, fixtures.DEMO_LAT, fixtures.DEMO_LON, now)
    with Storage(Path(args.db)) as storage:
        storage.upsert_snapshots(rows)
        latest = storage.latest_snapshots(fixtures.DEMO_LOCATION_NAME)
        sync_count = storage.sync_count(fixtures.DEMO_LOCATION_NAME)
        last_sync_time = storage.last_sync_time(fixtures.DEMO_LOCATION_NAME)
    _render_from_rows(latest, fixtures.DEMO_LOCATION_NAME, sync_count, last_sync_time, None, Path(args.out))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="outdoor-ops", description="Running & golf conditions dashboard.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Fetch live forecast + air quality and store it.")
    sync_parser.add_argument("--location", default=DEFAULT_LOCATION_NAME)
    sync_parser.add_argument("--lat", type=float, default=DEFAULT_LAT)
    sync_parser.add_argument("--lon", type=float, default=DEFAULT_LON)
    sync_parser.add_argument("--days", type=int, default=7)
    sync_parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    sync_parser.set_defaults(func=cmd_sync)

    render_parser = subparsers.add_parser("render", help="Render the dashboard from the last sync.")
    render_parser.add_argument("--location", default=DEFAULT_LOCATION_NAME)
    render_parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    render_parser.add_argument("--out", default=str(DEFAULT_HTML_PATH))
    render_parser.set_defaults(func=cmd_render)

    demo_parser = subparsers.add_parser("demo", help="Render the dashboard from bundled fixture data (no network).")
    demo_parser.add_argument("--db", default=str(DEFAULT_DB_PATH))
    demo_parser.add_argument("--out", default=str(DEFAULT_HTML_PATH))
    demo_parser.set_defaults(func=cmd_demo)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
