import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db


@pytest.fixture
def conn(tmp_path):
    connection = db.connect(tmp_path / "test_forge.db")
    db.init_db(connection)
    yield connection
    connection.close()


SAMPLE_QUESTION = {
    "population": "p_healthy_controls",
    "construct": "c_empathic_accuracy",
    "outcome": "o_prosocial_behavior",
    "method": "m_behavioral_task",
    "frame": "f_dual_process_empathy",
    "skeleton": "Does empathic accuracy predict prosocial behavior?",
    "rationale": "Measured via a behavioral task.",
    "testability": "feasible-now",
    "novelty_score": 1.0,
}


def test_connect_creates_missing_parent_directory(tmp_path):
    nested_path = tmp_path / "does" / "not" / "exist" / "forge.db"
    assert not nested_path.parent.exists()
    connection = db.connect(nested_path)
    db.init_db(connection)
    connection.close()
    assert nested_path.exists()


def test_init_db_is_idempotent(conn):
    db.init_db(conn)  # calling twice must not error or duplicate the table
    db.init_db(conn)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    names = [t["name"] for t in tables]
    assert names.count("questions") == 1


def test_insert_and_list_question(conn):
    qid = db.insert_question(conn, "2026-07-12T00:00:00+00:00", SAMPLE_QUESTION)
    assert qid == 1
    rows = db.list_questions(conn)
    assert len(rows) == 1
    assert rows[0]["skeleton"] == SAMPLE_QUESTION["skeleton"]
    assert rows[0]["starred"] == 0
    assert rows[0]["ai_source"] == "template"


def test_all_skeletons_returns_saved_skeletons(conn):
    db.insert_question(conn, "2026-07-12T00:00:00+00:00", SAMPLE_QUESTION)
    skeletons = db.all_skeletons(conn)
    assert skeletons == [SAMPLE_QUESTION["skeleton"]]


def test_set_starred_round_trip(conn):
    qid = db.insert_question(conn, "2026-07-12T00:00:00+00:00", SAMPLE_QUESTION)
    assert db.set_starred(conn, qid, True) is True
    assert db.get_question(conn, qid)["starred"] == 1
    assert db.set_starred(conn, qid, False) is True
    assert db.get_question(conn, qid)["starred"] == 0


def test_set_starred_on_missing_id_returns_false(conn):
    assert db.set_starred(conn, 9999, True) is False


def test_set_used_round_trip(conn):
    qid = db.insert_question(conn, "2026-07-12T00:00:00+00:00", SAMPLE_QUESTION)
    assert db.set_used(conn, qid, True) is True
    assert db.get_question(conn, qid)["used"] == 1


def test_set_tag_round_trip(conn):
    qid = db.insert_question(conn, "2026-07-12T00:00:00+00:00", SAMPLE_QUESTION)
    assert db.set_tag(conn, qid, "R01-empathy-aim2") is True
    assert db.get_question(conn, qid)["tag"] == "R01-empathy-aim2"


def test_search_questions_matches_skeleton_text(conn):
    db.insert_question(conn, "2026-07-12T00:00:00+00:00", SAMPLE_QUESTION)
    other = dict(SAMPLE_QUESTION)
    other["skeleton"] = "Does cortisol reactivity predict burnout?"
    db.insert_question(conn, "2026-07-12T00:00:00+00:00", other)

    results = db.search_questions(conn, "cortisol")
    assert len(results) == 1
    assert "cortisol" in results[0]["skeleton"].lower()


def test_search_questions_no_match_returns_empty(conn):
    db.insert_question(conn, "2026-07-12T00:00:00+00:00", SAMPLE_QUESTION)
    results = db.search_questions(conn, "nonexistent-term-xyz")
    assert results == []
