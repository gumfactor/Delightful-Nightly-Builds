import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import checklist, db, reviewer

SECTIONS = {"aims": "Aim 1: X. Our central hypothesis is that Y. This work will provide Z."}


@pytest.fixture
def conn(tmp_path):
    connection = db.connect(str(tmp_path / "test.db"))
    yield connection
    connection.close()


def _submit(conn, project_name, sections=SECTIONS):
    checklist_result = checklist.run(sections)
    review = reviewer.build_review(sections, checklist_result, api_key=None)
    return db.insert_version(conn, project_name, sections, checklist_result, review)


def test_first_submit_creates_project_and_version_one(conn):
    result = _submit(conn, "Test Project")
    assert result["version_num"] == 1
    history = db.get_history(conn, "Test Project")
    assert len(history) == 1


def test_second_submit_increments_version_number(conn):
    _submit(conn, "Test Project")
    result = _submit(conn, "Test Project")
    assert result["version_num"] == 2
    history = db.get_history(conn, "Test Project")
    assert [v["version_num"] for v in history] == [1, 2]


def test_history_ordered_ascending_by_version(conn):
    for _ in range(3):
        _submit(conn, "Ordered Project")
    history = db.get_history(conn, "Ordered Project")
    assert [v["version_num"] for v in history] == [1, 2, 3]


def test_history_for_unknown_project_raises():
    connection = db.connect(":memory:")
    with pytest.raises(db.ProjectNotFoundError):
        db.get_history(connection, "Nonexistent")


def test_get_latest_returns_most_recent_version(conn):
    _submit(conn, "Latest Project")
    second = _submit(conn, "Latest Project")
    latest = db.get_latest(conn, "Latest Project")
    assert latest["version_num"] == second["version_num"] == 2


def test_get_latest_returns_none_for_project_with_no_versions(conn):
    db.get_or_create_project(conn, "Empty Project")
    assert db.get_latest(conn, "Empty Project") is None


def test_list_projects_reports_version_counts(conn):
    _submit(conn, "Project A")
    _submit(conn, "Project A")
    _submit(conn, "Project B")
    projects = {p["name"]: p for p in db.list_projects(conn)}
    assert projects["Project A"]["version_count"] == 2
    assert projects["Project B"]["version_count"] == 1


def test_separate_projects_have_independent_version_sequences(conn):
    _submit(conn, "Project X")
    result_y = _submit(conn, "Project Y")
    assert result_y["version_num"] == 1


def test_stored_checklist_and_review_round_trip_correctly(conn):
    checklist_result = checklist.run(SECTIONS)
    review = reviewer.build_review(SECTIONS, checklist_result, api_key=None)
    db.insert_version(conn, "Round Trip", SECTIONS, checklist_result, review)
    stored = db.get_latest(conn, "Round Trip")
    assert stored["checklist"]["overall_pass_rate"] == checklist_result["overall_pass_rate"]
    assert stored["review"]["overall_impact"] == review["overall_impact"]
    assert stored["sections"] == SECTIONS
