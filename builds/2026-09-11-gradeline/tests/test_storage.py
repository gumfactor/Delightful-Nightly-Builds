import os

import pytest

from src import storage


@pytest.fixture
def conn(tmp_path):
    db_path = os.path.join(tmp_path, "test.db")
    connection = storage.connect(db_path)
    yield connection
    connection.close()


def test_create_batch_and_get_batch_roundtrip(conn):
    batch_id = storage.create_batch(conn, "My Rubric", '{"name": "My Rubric"}', "/path/to/subs")
    row = storage.get_batch(conn, batch_id)
    assert row["rubric_name"] == "My Rubric"
    assert row["source_path"] == "/path/to/subs"
    assert row["graded_at"]


def test_get_batch_missing_returns_none(conn):
    assert storage.get_batch(conn, 9999) is None


def test_add_submission_roundtrip(conn):
    batch_id = storage.create_batch(conn, "R", "{}", "/subs")
    sub_id = storage.add_submission(
        conn,
        batch_id,
        "alice",
        250,
        3,
        62.5,
        {"word_count_ok": True, "sections_ok": True, "citations_ok": True, "sections_found": {}},
        [{"id": "c1", "score": 8.0, "max_points": 10, "manual_only": False}],
        None,
    )
    rows = storage.get_submissions(conn, batch_id)
    assert len(rows) == 1
    assert rows[0]["id"] == sub_id
    assert rows[0]["identifier"] == "alice"
    assert rows[0]["word_count"] == 250
    assert rows[0]["citation_count"] == 3


def test_get_submissions_orders_by_id_ascending(conn):
    batch_id = storage.create_batch(conn, "R", "{}", "/subs")
    for name in ["carol", "alice", "bob"]:
        storage.add_submission(conn, batch_id, name, 100, 1, 50.0, {}, [], None)
    rows = storage.get_submissions(conn, batch_id)
    assert [r["identifier"] for r in rows] == ["carol", "alice", "bob"]


def test_add_similarity_pair_roundtrip(conn):
    batch_id = storage.create_batch(conn, "R", "{}", "/subs")
    sub_a = storage.add_submission(conn, batch_id, "alice", 100, 1, 50.0, {}, [], None)
    sub_b = storage.add_submission(conn, batch_id, "bob", 100, 1, 50.0, {}, [], None)
    storage.add_similarity_pair(conn, batch_id, sub_a, sub_b, 0.91)
    pairs = storage.get_similarity_pairs(conn, batch_id)
    assert len(pairs) == 1
    assert pairs[0]["submission_a_id"] == sub_a
    assert pairs[0]["submission_b_id"] == sub_b
    assert pairs[0]["score"] == 0.91


def test_similarity_pairs_ordered_by_score_descending(conn):
    batch_id = storage.create_batch(conn, "R", "{}", "/subs")
    sub_ids = [storage.add_submission(conn, batch_id, f"s{i}", 100, 1, 50.0, {}, [], None) for i in range(3)]
    storage.add_similarity_pair(conn, batch_id, sub_ids[0], sub_ids[1], 0.5)
    storage.add_similarity_pair(conn, batch_id, sub_ids[1], sub_ids[2], 0.95)
    pairs = storage.get_similarity_pairs(conn, batch_id)
    assert [p["score"] for p in pairs] == [0.95, 0.5]


def test_list_batches_orders_newest_first(conn):
    id_1 = storage.create_batch(conn, "First", "{}", "/subs1")
    id_2 = storage.create_batch(conn, "Second", "{}", "/subs2")
    rows = storage.list_batches(conn)
    assert [r["id"] for r in rows] == [id_2, id_1]


def test_regrading_creates_new_batch_not_overwrite(conn):
    id_1 = storage.create_batch(conn, "Same Rubric", "{}", "/subs")
    id_2 = storage.create_batch(conn, "Same Rubric", "{}", "/subs")
    assert id_1 != id_2
    assert len(storage.list_batches(conn)) == 2


def test_ai_feedback_json_stored_and_retrieved(conn):
    batch_id = storage.create_batch(conn, "R", "{}", "/subs")
    storage.add_submission(
        conn, batch_id, "alice", 100, 1, 50.0, {}, [], {"note": "sample feedback"}
    )
    rows = storage.get_submissions(conn, batch_id)
    assert rows[0]["ai_feedback_json"] == '{"note": "sample feedback"}'
