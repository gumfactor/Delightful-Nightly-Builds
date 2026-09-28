import datetime as dt
import sqlite3

from src import cli, fixtures
from src.weather_client import WeatherClientError


def test_build_parser_sync_defaults():
    parser = cli.build_parser()
    args = parser.parse_args(["sync"])
    assert args.location == cli.DEFAULT_LOCATION_NAME
    assert args.lat == cli.DEFAULT_LAT
    assert args.days == 7
    assert args.func is cli.cmd_sync


def test_build_parser_render_defaults():
    parser = cli.build_parser()
    args = parser.parse_args(["render"])
    assert args.func is cli.cmd_render


def test_build_parser_demo_defaults():
    parser = cli.build_parser()
    args = parser.parse_args(["demo"])
    assert args.func is cli.cmd_demo


def test_cmd_demo_creates_db_and_html_from_bundled_fixtures(tmp_path):
    # demo builds rows straight from src.fixtures and never constructs a
    # WeatherClient/AirQualityClient, so it makes zero network calls by
    # construction (no client to intercept).
    db_path = tmp_path / "demo.db"
    html_path = tmp_path / "demo.html"
    parser = cli.build_parser()
    args = parser.parse_args(["demo", "--db", str(db_path), "--out", str(html_path)])
    exit_code = args.func(args)

    assert exit_code == 0
    assert db_path.exists()
    assert html_path.exists()
    html_text = html_path.read_text(encoding="utf-8")
    assert "Outdoor Ops" in html_text
    assert "chart.js" in html_text

    conn = sqlite3.connect(str(db_path))
    count = conn.execute("SELECT COUNT(*) FROM forecast_snapshots;").fetchone()[0]
    conn.close()
    assert count == 7


def test_cmd_sync_returns_error_code_on_client_failure(tmp_path, monkeypatch, capsys):
    class FailingWeatherClient:
        def __init__(self, *args, **kwargs):
            pass

        def get_daily_forecast(self, *args, **kwargs):
            raise WeatherClientError("simulated network failure")

    monkeypatch.setattr(cli, "WeatherClient", FailingWeatherClient)

    db_path = tmp_path / "sync.db"
    parser = cli.build_parser()
    args = parser.parse_args(["sync", "--db", str(db_path)])
    exit_code = args.func(args)

    assert exit_code == 1
    assert not db_path.exists()
    captured = capsys.readouterr()
    assert "Sync failed" in captured.err


def test_build_rows_stores_none_aqi_when_air_quality_missing_for_date():
    forecast = [dict(date="2026-09-28", temp_max=15.0, temp_min=8.0, precip_prob_max=10.0,
                      precip_sum=0.0, wind_max=10.0, windgust_max=18.0, uv_index_max=3.0, weathercode=1)]
    air_quality: list = []  # no matching air-quality record for this date
    rows = cli.build_rows(forecast, air_quality, "Toronto, ON", 43.65, -79.38, dt.datetime(2026, 9, 28, tzinfo=dt.timezone.utc))

    assert rows[0]["aqi_max"] is None
    assert rows[0]["aqi_mean"] is None
    assert rows[0]["pm25_mean"] is None
    # The composite score must reflect the known-ideal factors, not a fake
    # perfect AQI: with temp/wind/precip/uv all ideal, excluding AQI from
    # the renormalized weighted average still nets 100 — see
    # tests/test_scoring.py for the case that actually distinguishes
    # "unknown" from "known and bad".
    assert rows[0]["running_score"] == 100.0


def test_demo_location_is_isolated_from_live_sync_location(tmp_path):
    # A real sync's default location_name ("Toronto, ON") must never equal
    # the demo fixture's location_name — otherwise, since sync_day is always
    # "today" for both, running `demo` after a real `sync` (or vice versa)
    # on an overlapping forecast date would silently overwrite live synced
    # data with sample data, or pollute the live location's history.
    assert fixtures.DEMO_LOCATION_NAME != cli.DEFAULT_LOCATION_NAME

    db_path = tmp_path / "shared.db"
    live_row = dict(
        location_name=cli.DEFAULT_LOCATION_NAME, lat=cli.DEFAULT_LAT, lon=cli.DEFAULT_LON,
        forecast_date="2026-09-28", sync_day="2026-09-28", fetched_at="2026-09-28T08:00:00",
        temp_max=15.0, temp_min=8.0, precip_prob_max=10.0, precip_sum=0.0,
        wind_max=10.0, windgust_max=18.0, uv_index_max=3.0, weathercode=1,
        aqi_max=40.0, aqi_mean=30.0, pm25_mean=8.0, running_score=77.0, golf_score=66.0,
    )
    from src.storage import Storage
    with Storage(db_path) as storage:
        storage.upsert_snapshots([live_row])

    parser = cli.build_parser()
    demo_args = parser.parse_args(["demo", "--db", str(db_path), "--out", str(tmp_path / "demo.html")])
    demo_args.func(demo_args)

    with Storage(db_path) as storage:
        live_after_demo = storage.latest_snapshots(cli.DEFAULT_LOCATION_NAME)

    assert len(live_after_demo) == 1
    assert live_after_demo[0]["running_score"] == 77.0


def test_render_after_demo_reports_no_data_for_unknown_location(tmp_path):
    db_path = tmp_path / "empty.db"
    html_path = tmp_path / "empty.html"
    parser = cli.build_parser()
    demo_args = parser.parse_args(["demo", "--db", str(db_path), "--out", str(tmp_path / "d.html")])
    demo_args.func(demo_args)

    render_args = parser.parse_args([
        "render", "--location", "Nowhere", "--db", str(db_path), "--out", str(html_path),
    ])
    exit_code = render_args.func(render_args)

    assert exit_code == 0
    html_text = html_path.read_text(encoding="utf-8")
    assert cli.NO_DATA_NOTE in html_text
