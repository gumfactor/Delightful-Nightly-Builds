import sqlite3

from src import cli
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
