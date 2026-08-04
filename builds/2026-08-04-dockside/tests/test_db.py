import pytest

import db as dockside_db


@pytest.fixture
def conn():
    connection = dockside_db.connect(":memory:")
    dockside_db.init_db(connection)
    yield connection
    connection.close()


def test_init_db_creates_tables(conn):
    tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"sites", "tasks", "completions", "observations", "briefings"} <= tables


def test_add_and_get_site(conn):
    site_id = dockside_db.add_site(conn, "Cottage Dock", "Muskoka, Ontario", 45.0, -79.5)
    site = dockside_db.get_site_by_name(conn, "Cottage Dock")
    assert site["id"] == site_id
    assert site["latitude"] == 45.0
    assert site["marine_available"] is None


def test_get_site_by_name_returns_none_when_missing(conn):
    assert dockside_db.get_site_by_name(conn, "Nonexistent") is None


def test_set_marine_available(conn):
    site_id = dockside_db.add_site(conn, "Cottage Dock", None, 45.0, -79.5)
    dockside_db.set_marine_available(conn, site_id, True)
    site = dockside_db.get_site_by_name(conn, "Cottage Dock")
    assert site["marine_available"] == 1


def test_add_task_rejects_invalid_category(conn):
    site_id = dockside_db.add_site(conn, "Cottage Dock", None, 45.0, -79.5)
    with pytest.raises(ValueError):
        dockside_db.add_task(conn, site_id, "Bad Task", "not_a_category", 4, 5)


def test_add_task_rejects_invalid_month(conn):
    site_id = dockside_db.add_site(conn, "Cottage Dock", None, 45.0, -79.5)
    with pytest.raises(ValueError):
        dockside_db.add_task(conn, site_id, "Bad Task", "dock", 13, 5)


def test_add_and_list_tasks(conn):
    site_id = dockside_db.add_site(conn, "Cottage Dock", None, 45.0, -79.5)
    dockside_db.add_task(conn, site_id, "Install Dock", "dock", 4, 5, max_wind_kmh=20.0)
    dockside_db.add_task(conn, site_id, "Remove Dock", "dock", 9, 10, dry_days_required=2)
    tasks = dockside_db.list_tasks(conn, site_id=site_id)
    assert len(tasks) == 2
    assert {t["name"] for t in tasks} == {"Install Dock", "Remove Dock"}


def test_upsert_observation_dedupes_by_site_and_date(conn):
    site_id = dockside_db.add_site(conn, "Cottage Dock", None, 45.0, -79.5)
    dockside_db.upsert_observation(conn, site_id, "2026-08-15", 10.0, 20.0, 0.0, 10.0, None, None)
    dockside_db.upsert_observation(conn, site_id, "2026-08-15", 12.0, 22.0, 1.0, 15.0, None, None)
    rows = dockside_db.list_observations(conn, site_id)
    assert len(rows) == 1
    assert rows[0]["temp_min_c"] == 12.0  # second sync's values won, not duplicated


def test_upsert_observation_multiple_dates_not_deduped(conn):
    site_id = dockside_db.add_site(conn, "Cottage Dock", None, 45.0, -79.5)
    dockside_db.upsert_observation(conn, site_id, "2026-08-15", 10.0, 20.0, 0.0, 10.0, None, None)
    dockside_db.upsert_observation(conn, site_id, "2026-08-16", 10.0, 20.0, 0.0, 10.0, None, None)
    assert dockside_db.count_observations(conn, site_id) == 2


def test_record_completion_and_get_last_completion_year(conn):
    site_id = dockside_db.add_site(conn, "Cottage Dock", None, 45.0, -79.5)
    task_id = dockside_db.add_task(conn, site_id, "Remove Dock", "dock", 9, 10)
    assert dockside_db.get_last_completion_year(conn, task_id) is None
    dockside_db.record_completion(conn, task_id, 2026, "2026-09-30")
    assert dockside_db.get_last_completion_year(conn, task_id) == 2026
    dockside_db.record_completion(conn, task_id, 2027, "2027-09-28")
    assert dockside_db.get_last_completion_year(conn, task_id) == 2027


def test_save_and_get_latest_briefing(conn):
    site_id = dockside_db.add_site(conn, "Cottage Dock", None, 45.0, -79.5)
    assert dockside_db.get_latest_briefing(conn, site_id) is None
    dockside_db.save_briefing(conn, site_id, "template", "First briefing")
    dockside_db.save_briefing(conn, site_id, "ai", "Second briefing")
    latest = dockside_db.get_latest_briefing(conn, site_id)
    assert latest["text"] == "Second briefing"
    assert latest["source"] == "ai"
