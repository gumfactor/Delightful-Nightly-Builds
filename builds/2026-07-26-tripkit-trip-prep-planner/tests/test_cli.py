import os
import sys
from datetime import date
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import main  # noqa: E402
import geocoding  # noqa: E402
import weather  # noqa: E402

FAKE_PLACE = geocoding.ResolvedPlace(
    display_name="Boston, Massachusetts, United States", country="United States", latitude=42.36, longitude=-71.06
)
FAKE_DAILY = [
    weather.DailyWeather(day_date="2026-08-15", temp_max_c=27.0, temp_min_c=19.0, precip_mm=0.0, wind_max_kmh=12.0, weathercode=1),
    weather.DailyWeather(day_date="2026-08-16", temp_max_c=26.0, temp_min_c=18.0, precip_mm=1.0, wind_max_kmh=15.0, weathercode=2),
]


def _configure_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "OUTPUT_DIR", str(tmp_path))
    monkeypatch.setattr(main, "DB_PATH", str(tmp_path / "tripkit.db"))
    monkeypatch.setattr(main, "DASHBOARD_PATH", str(tmp_path / "dashboard.html"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def test_cli_add_rejects_end_before_start(tmp_path, monkeypatch, capsys):
    _configure_paths(tmp_path, monkeypatch)
    exit_code = main.main(
        ["add", "--name", "Bad Trip", "--destination", "Boston", "--start", "2026-08-15", "--end", "2026-08-10", "--tags", "conference"]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "End date cannot be before start date" in captured.err


def test_cli_add_rejects_unknown_activity_tag(tmp_path, monkeypatch, capsys):
    _configure_paths(tmp_path, monkeypatch)
    exit_code = main.main(
        ["add", "--name", "Trip", "--destination", "Boston", "--start", "2026-08-15", "--end", "2026-08-16", "--tags", "skydiving"]
    )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Unknown activity tag" in captured.err


def test_cli_add_then_list_shows_the_trip(tmp_path, monkeypatch, capsys):
    _configure_paths(tmp_path, monkeypatch)
    with patch.object(geocoding, "resolve_destination", return_value=FAKE_PLACE), patch.object(
        weather, "get_weather_for_trip", return_value=("forecast", FAKE_DAILY)
    ):
        add_exit = main.main(
            ["add", "--name", "ICON Conference", "--destination", "Boston", "--start", "2026-08-15", "--end", "2026-08-16", "--tags", "conference"]
        )
    list_exit = main.main(["list"])
    captured = capsys.readouterr()

    assert add_exit == 0
    assert list_exit == 0
    assert "ICON Conference" in captured.out
    assert "Boston" in captured.out


def test_cli_show_unknown_trip_id_errors(tmp_path, monkeypatch, capsys):
    _configure_paths(tmp_path, monkeypatch)
    exit_code = main.main(["show", "999"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "No trip with id 999" in captured.err


def test_cli_delete_removes_trip(tmp_path, monkeypatch, capsys):
    _configure_paths(tmp_path, monkeypatch)
    with patch.object(geocoding, "resolve_destination", return_value=FAKE_PLACE), patch.object(
        weather, "get_weather_for_trip", return_value=("forecast", FAKE_DAILY)
    ):
        main.main(["add", "--name", "Trip", "--destination", "Boston", "--start", "2026-08-15", "--end", "2026-08-16", "--tags", "leisure"])

    delete_exit = main.main(["delete", "1"])
    show_exit = main.main(["show", "1"])

    assert delete_exit == 0
    assert show_exit == 1


def test_cli_dashboard_writes_self_contained_html_file(tmp_path, monkeypatch):
    _configure_paths(tmp_path, monkeypatch)
    with patch.object(geocoding, "resolve_destination", return_value=FAKE_PLACE), patch.object(
        weather, "get_weather_for_trip", return_value=("forecast", FAKE_DAILY)
    ):
        main.main(["add", "--name", "ICON Conference", "--destination", "Boston", "--start", "2026-08-15", "--end", "2026-08-16", "--tags", "conference"])

    exit_code = main.main(["dashboard"])

    assert exit_code == 0
    dashboard_path = tmp_path / "dashboard.html"
    assert dashboard_path.exists()
    content = dashboard_path.read_text(encoding="utf-8")
    assert "ICON Conference" in content
    assert "chart.js@4.4.4" in content


def test_cli_add_with_mocked_weather_failure_reports_error(tmp_path, monkeypatch, capsys):
    _configure_paths(tmp_path, monkeypatch)
    with patch.object(geocoding, "resolve_destination", return_value=FAKE_PLACE), patch.object(
        weather, "get_weather_for_trip", side_effect=weather.WeatherError("service unreachable")
    ):
        exit_code = main.main(
            ["add", "--name", "Trip", "--destination", "Boston", "--start", "2026-08-15", "--end", "2026-08-16", "--tags", "conference"]
        )
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "service unreachable" in captured.err
