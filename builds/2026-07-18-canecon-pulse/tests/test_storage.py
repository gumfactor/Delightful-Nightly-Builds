from datetime import date

from src.models import Observation
from src.storage import connect, get_history, get_latest_fetched_at, get_series_ids, insert_observations


def make_observation(series_id="FXUSDCAD", obs_date=date(2026, 7, 1), value=1.36):
    return Observation(
        series_id=series_id,
        series_label="USD/CAD Exchange Rate",
        unit="CAD per USD",
        source="Bank of Canada Valet",
        obs_date=obs_date,
        value=value,
    )


def test_insert_and_retrieve(tmp_path):
    conn = connect(str(tmp_path / "test.db"))
    inserted = insert_observations(conn, [make_observation()])

    assert inserted == 1
    history = get_history(conn, "FXUSDCAD")
    assert history == [(date(2026, 7, 1), 1.36)]
    conn.close()


def test_duplicate_insert_is_a_noop(tmp_path):
    conn = connect(str(tmp_path / "test.db"))
    insert_observations(conn, [make_observation()])
    second_pass = insert_observations(conn, [make_observation()])

    assert second_pass == 0
    assert len(get_history(conn, "FXUSDCAD")) == 1
    conn.close()


def test_multiple_series_coexist(tmp_path):
    conn = connect(str(tmp_path / "test.db"))
    insert_observations(
        conn,
        [
            make_observation(series_id="FXUSDCAD"),
            make_observation(series_id="FXEURCAD", value=1.48),
        ],
    )

    assert get_series_ids(conn) == ["FXEURCAD", "FXUSDCAD"]
    conn.close()


def test_history_is_ordered_oldest_to_newest(tmp_path):
    conn = connect(str(tmp_path / "test.db"))
    insert_observations(
        conn,
        [
            make_observation(obs_date=date(2026, 7, 3), value=1.37),
            make_observation(obs_date=date(2026, 7, 1), value=1.36),
            make_observation(obs_date=date(2026, 7, 2), value=1.365),
        ],
    )

    history = get_history(conn, "FXUSDCAD")
    assert [d for d, _ in history] == [date(2026, 7, 1), date(2026, 7, 2), date(2026, 7, 3)]
    conn.close()


def test_get_series_ids_empty_database(tmp_path):
    conn = connect(str(tmp_path / "test.db"))
    assert get_series_ids(conn) == []
    conn.close()


def test_get_latest_fetched_at_returns_none_when_no_history(tmp_path):
    conn = connect(str(tmp_path / "test.db"))
    assert get_latest_fetched_at(conn, "FXUSDCAD") is None
    conn.close()


def test_get_latest_fetched_at_returns_timestamp(tmp_path):
    conn = connect(str(tmp_path / "test.db"))
    insert_observations(conn, [make_observation()])
    assert get_latest_fetched_at(conn, "FXUSDCAD") is not None
    conn.close()
