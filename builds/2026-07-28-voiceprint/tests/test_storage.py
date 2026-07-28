import os

from src.storage import HistoryStore


def test_record_and_retrieve_single_run(tmp_path):
    db_path = str(tmp_path / "history.db")
    store = HistoryStore(db_path)
    file_path = str(tmp_path / "draft.md")

    store.record_run(file_path, "2026-07-28T08:00:00+00:00", 120, 88.5, 2, {"note": "first"})
    history = store.get_history(file_path)

    assert len(history) == 1
    assert history[0]["score"] == 88.5
    assert history[0]["word_count"] == 120
    assert history[0]["flag_count"] == 2
    assert history[0]["details"] == {"note": "first"}


def test_history_orders_runs_by_timestamp_ascending(tmp_path):
    db_path = str(tmp_path / "history.db")
    store = HistoryStore(db_path)
    file_path = str(tmp_path / "draft.md")

    store.record_run(file_path, "2026-07-28T09:00:00+00:00", 100, 70.0, 3, {})
    store.record_run(file_path, "2026-07-28T08:00:00+00:00", 100, 90.0, 1, {})

    history = store.get_history(file_path)
    assert [entry["score"] for entry in history] == [90.0, 70.0]


def test_history_is_isolated_per_file(tmp_path):
    db_path = str(tmp_path / "history.db")
    store = HistoryStore(db_path)
    file_a = str(tmp_path / "a.md")
    file_b = str(tmp_path / "b.md")

    store.record_run(file_a, "2026-07-28T08:00:00+00:00", 50, 60.0, 5, {})
    store.record_run(file_b, "2026-07-28T08:00:00+00:00", 50, 95.0, 0, {})

    assert len(store.get_history(file_a)) == 1
    assert len(store.get_history(file_b)) == 1
    assert store.get_history(file_a)[0]["score"] == 60.0
    assert store.get_history(file_b)[0]["score"] == 95.0


def test_get_history_returns_empty_list_for_unknown_file(tmp_path):
    db_path = str(tmp_path / "history.db")
    store = HistoryStore(db_path)
    assert store.get_history(str(tmp_path / "never-analyzed.md")) == []


def test_list_files_returns_distinct_paths(tmp_path):
    db_path = str(tmp_path / "history.db")
    store = HistoryStore(db_path)
    file_a = str(tmp_path / "a.md")

    store.record_run(file_a, "2026-07-28T08:00:00+00:00", 50, 60.0, 5, {})
    store.record_run(file_a, "2026-07-28T09:00:00+00:00", 55, 65.0, 4, {})

    assert store.list_files() == [os.path.abspath(file_a)]


def test_db_directory_is_created_if_missing(tmp_path):
    db_path = str(tmp_path / "nested" / "dir" / "history.db")
    HistoryStore(db_path)
    assert os.path.isfile(db_path)
