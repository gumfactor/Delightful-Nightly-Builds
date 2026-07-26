import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import storage  # noqa: E402


def _make_conn(tmp_path):
    return storage.connect(str(tmp_path / "test_tripkit.db"))


def test_add_and_get_trip_round_trips_all_fields(tmp_path):
    conn = _make_conn(tmp_path)
    trip_id = storage.add_trip(
        conn,
        name="Cottage Weekend",
        destination_query="Muskoka",
        resolved_name="Muskoka, Ontario, Canada",
        country="Canada",
        latitude=45.0,
        longitude=-79.5,
        start_date="2026-08-10",
        end_date="2026-08-12",
        activity_tags=["cottage", "boating"],
        created_at="2026-07-26T00:00:00+00:00",
    )
    trip = storage.get_trip(conn, trip_id)

    assert trip["name"] == "Cottage Weekend"
    assert trip["resolved_name"] == "Muskoka, Ontario, Canada"
    assert trip["activity_tags"] == ["cottage", "boating"]
    assert trip["start_date"] == "2026-08-10"
    assert trip["latitude"] == 45.0


def test_get_trip_returns_none_for_missing_id(tmp_path):
    conn = _make_conn(tmp_path)
    assert storage.get_trip(conn, 999) is None


def test_delete_trip_removes_trip_and_its_weather_snapshot(tmp_path):
    conn = _make_conn(tmp_path)
    trip_id = storage.add_trip(
        conn, "Trip", "Toronto", "Toronto, Ontario, Canada", "Canada", 43.65, -79.38,
        "2026-08-01", "2026-08-02", ["leisure"], "2026-07-26T00:00:00+00:00",
    )
    storage.save_weather_snapshot(conn, trip_id, "forecast", "2026-07-26T00:00:00+00:00", [{"day_date": "2026-08-01"}])

    deleted = storage.delete_trip(conn, trip_id)

    assert deleted is True
    assert storage.get_trip(conn, trip_id) is None
    assert storage.get_latest_weather_snapshot(conn, trip_id) is None


def test_delete_trip_returns_false_for_missing_id(tmp_path):
    conn = _make_conn(tmp_path)
    assert storage.delete_trip(conn, 12345) is False


def test_list_trips_sorted_by_start_date_ascending(tmp_path):
    conn = _make_conn(tmp_path)
    storage.add_trip(
        conn, "Later Trip", "Boston", "Boston, MA, US", "United States", 42.36, -71.06,
        "2026-09-01", "2026-09-03", ["conference"], "2026-07-26T00:00:00+00:00",
    )
    storage.add_trip(
        conn, "Earlier Trip", "Muskoka", "Muskoka, ON, CA", "Canada", 45.0, -79.5,
        "2026-08-01", "2026-08-03", ["cottage"], "2026-07-26T00:00:00+00:00",
    )

    trips = storage.list_trips(conn)

    assert [t["name"] for t in trips] == ["Earlier Trip", "Later Trip"]


def test_save_weather_snapshot_replaces_previous_snapshot(tmp_path):
    conn = _make_conn(tmp_path)
    trip_id = storage.add_trip(
        conn, "Trip", "Toronto", "Toronto, Ontario, Canada", "Canada", 43.65, -79.38,
        "2026-08-01", "2026-08-02", ["leisure"], "2026-07-26T00:00:00+00:00",
    )
    storage.save_weather_snapshot(conn, trip_id, "climate_normal", "2026-07-01T00:00:00+00:00", [{"day_date": "old"}])
    storage.save_weather_snapshot(conn, trip_id, "forecast", "2026-07-26T00:00:00+00:00", [{"day_date": "new"}])

    snapshot = storage.get_latest_weather_snapshot(conn, trip_id)

    assert snapshot["mode"] == "forecast"
    assert snapshot["daily"] == [{"day_date": "new"}]
