import os
from datetime import date
from unittest.mock import patch

import pytest

import db as dockside_db
import main as dockside_main
import weather_client


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "dockside.db")


def run(db_path, *cli_args):
    dockside_main.main(["--db", db_path, *cli_args])


def test_init_creates_database_file(db_path):
    run(db_path, "init")
    assert os.path.exists(db_path)


def test_add_site_with_explicit_lat_lon(db_path, capsys):
    run(db_path, "add-site", "Cottage Dock", "--lat", "45.0", "--lon", "-79.5")
    out = capsys.readouterr().out
    assert "Added site 'Cottage Dock'" in out
    conn = dockside_db.connect(db_path)
    site = dockside_db.get_site_by_name(conn, "Cottage Dock")
    conn.close()
    assert site["latitude"] == 45.0


def test_add_site_geocodes_when_location_given(db_path):
    fake_result = weather_client.GeocodeResult(name="Muskoka", latitude=45.1, longitude=-79.6)
    with patch("weather_client.geocode", return_value=fake_result):
        run(db_path, "add-site", "Cottage Dock", "--location", "Muskoka, Ontario")
    conn = dockside_db.connect(db_path)
    site = dockside_db.get_site_by_name(conn, "Cottage Dock")
    conn.close()
    assert site["latitude"] == 45.1
    assert site["place_name"] == "Muskoka"


def test_add_site_requires_location_or_lat_lon(db_path):
    with pytest.raises(SystemExit):
        run(db_path, "add-site", "Cottage Dock")


def test_add_task_rejects_invalid_month(db_path):
    run(db_path, "add-site", "Cottage Dock", "--lat", "45.0", "--lon", "-79.5")
    with pytest.raises(ValueError):
        run(db_path, "add-task", "Install Dock", "--site", "Cottage Dock",
            "--category", "dock", "--window-start-month", "13", "--window-end-month", "5")


def test_add_task_unknown_site_exits(db_path):
    with pytest.raises(SystemExit):
        run(db_path, "add-task", "Install Dock", "--site", "Nonexistent",
            "--category", "dock", "--window-start-month", "4", "--window-end-month", "5")


def test_sync_persists_observations_and_marine_flag(db_path, capsys):
    run(db_path, "add-site", "Cottage Dock", "--lat", "45.0", "--lon", "-79.5")
    run(db_path, "add-task", "Install Dock", "--site", "Cottage Dock",
        "--category", "dock", "--window-start-month", "1", "--window-end-month", "12",
        "--max-wind", "20")

    fake_forecast = [
        weather_client.DailyForecast(obs_date=date(2026, 8, 15),
                                      temp_min_c=10.0, temp_max_c=20.0, precip_mm=0.0,
                                      wind_speed_max_kmh=10.0),
    ]
    with patch("weather_client.fetch_forecast", return_value=fake_forecast), \
         patch("weather_client.fetch_marine", return_value=[]):
        run(db_path, "sync")

    out = capsys.readouterr().out
    assert "Synced 1 day(s)" in out
    assert "marine data: unavailable" in out

    conn = dockside_db.connect(db_path)
    site = dockside_db.get_site_by_name(conn, "Cottage Dock")
    assert dockside_db.count_observations(conn, site["id"]) == 1
    assert site["marine_available"] == 0
    conn.close()


def test_sync_does_not_duplicate_observations_on_rerun(db_path):
    run(db_path, "add-site", "Cottage Dock", "--lat", "45.0", "--lon", "-79.5")
    fake_forecast = [
        weather_client.DailyForecast(obs_date=date(2026, 8, 15),
                                      temp_min_c=10.0, temp_max_c=20.0, precip_mm=0.0,
                                      wind_speed_max_kmh=10.0),
    ]
    with patch("weather_client.fetch_forecast", return_value=fake_forecast), \
         patch("weather_client.fetch_marine", return_value=[]):
        run(db_path, "sync")
        run(db_path, "sync")

    conn = dockside_db.connect(db_path)
    site = dockside_db.get_site_by_name(conn, "Cottage Dock")
    assert dockside_db.count_observations(conn, site["id"]) == 1
    conn.close()


def test_sync_with_no_sites_exits(db_path):
    run(db_path, "init")
    with pytest.raises(SystemExit):
        run(db_path, "sync")


def test_complete_records_completion_and_prints_next_season(db_path, capsys):
    run(db_path, "add-site", "Cottage Dock", "--lat", "45.0", "--lon", "-79.5")
    run(db_path, "add-task", "Remove Dock", "--site", "Cottage Dock",
        "--category", "dock", "--window-start-month", "9", "--window-end-month", "10")

    conn = dockside_db.connect(db_path)
    task = dockside_db.list_tasks(conn, active_only=False)[0]
    conn.close()

    run(db_path, "complete", str(task["id"]), "--date", "2026-09-30")
    out = capsys.readouterr().out
    assert "complete for 2026" in out
    assert "September 2027" in out


def test_render_produces_html_file(db_path, tmp_path):
    run(db_path, "add-site", "Cottage Dock", "--lat", "45.0", "--lon", "-79.5")
    run(db_path, "add-task", "Install Dock", "--site", "Cottage Dock",
        "--category", "dock", "--window-start-month", "1", "--window-end-month", "12")
    output_path = str(tmp_path / "dashboard.html")
    run(db_path, "render", "--site", "Cottage Dock", "--output", output_path)
    assert os.path.exists(output_path)
    with open(output_path, encoding="utf-8") as fh:
        content = fh.read()
    assert "Cottage Dock" in content


def test_brief_makes_no_network_call_without_api_key(db_path, capsys, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    run(db_path, "add-site", "Cottage Dock", "--lat", "45.0", "--lon", "-79.5")
    with patch("urllib.request.urlopen") as mock_urlopen:
        run(db_path, "brief", "--site", "Cottage Dock")
    mock_urlopen.assert_not_called()
    out = capsys.readouterr().out
    assert "[template]" in out
