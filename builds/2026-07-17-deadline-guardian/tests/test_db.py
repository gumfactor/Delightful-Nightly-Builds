import os
from datetime import date

import pytest

from src import db


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test.db")
    return db.get_connection(db_path)


def test_add_and_get_deadline(conn):
    deadline_id = db.add_deadline(
        conn, title="IRB renewal", category="IRB/Ethics", due_date=date(2027, 3, 1)
    )
    fetched = db.get_deadline(conn, deadline_id)
    assert fetched["title"] == "IRB renewal"
    assert fetched["category"] == "IRB/Ethics"
    assert fetched["due_date"] == "2027-03-01"
    assert fetched["completed"] is False


def test_add_deadline_invalid_category_raises(conn):
    with pytest.raises(db.InvalidCategoryError):
        db.add_deadline(conn, title="X", category="Not A Real Category", due_date=date(2027, 1, 1))


def test_list_deadlines_ordered_by_due_date(conn):
    db.add_deadline(conn, title="Later", category="Other", due_date=date(2027, 6, 1))
    db.add_deadline(conn, title="Sooner", category="Other", due_date=date(2027, 1, 1))
    titles = [d["title"] for d in db.list_deadlines(conn)]
    assert titles == ["Sooner", "Later"]


def test_list_deadlines_excludes_completed_when_flag_false(conn):
    keep_id = db.add_deadline(conn, title="Keep", category="Other", due_date=date(2027, 1, 1))
    done_id = db.add_deadline(conn, title="Done", category="Other", due_date=date(2027, 1, 2))
    db.complete_deadline(conn, done_id, date(2026, 12, 31))
    remaining = db.list_deadlines(conn, include_completed=False)
    assert [d["id"] for d in remaining] == [keep_id]


def test_complete_non_recurring_no_followup(conn):
    deadline_id = db.add_deadline(
        conn, title="One-off", category="Conference", due_date=date(2027, 1, 1), recurrence_rule="none"
    )
    completed, next_deadline = db.complete_deadline(conn, deadline_id, date(2026, 12, 31))
    assert completed["completed"] is True
    assert next_deadline is None


def test_complete_annual_creates_next_occurrence(conn):
    deadline_id = db.add_deadline(
        conn, title="Annual IRB", category="IRB/Ethics", due_date=date(2027, 3, 1), recurrence_rule="annual"
    )
    _, next_deadline = db.complete_deadline(conn, deadline_id, date(2027, 2, 25))
    assert next_deadline is not None
    assert next_deadline["due_date"] == "2028-03-01"
    assert next_deadline["recurrence"] == "annual"


def test_complete_semesterly_creates_next_occurrence(conn):
    deadline_id = db.add_deadline(
        conn, title="Course prep", category="Course", due_date=date(2027, 1, 10), recurrence_rule="semesterly"
    )
    _, next_deadline = db.complete_deadline(conn, deadline_id)
    assert next_deadline["due_date"] == "2027-07-10"


def test_complete_every_n_months_creates_next_occurrence(conn):
    deadline_id = db.add_deadline(
        conn,
        title="Grant report",
        category="Grant",
        due_date=date(2027, 1, 1),
        recurrence_rule="every_N_months",
        recurrence_months=4,
    )
    _, next_deadline = db.complete_deadline(conn, deadline_id)
    assert next_deadline["due_date"] == "2027-05-01"
    assert next_deadline["recurrence_months"] == 4


def test_complete_already_completed_raises(conn):
    deadline_id = db.add_deadline(conn, title="X", category="Other", due_date=date(2027, 1, 1))
    db.complete_deadline(conn, deadline_id)
    with pytest.raises(db.AlreadyCompletedError):
        db.complete_deadline(conn, deadline_id)


def test_complete_nonexistent_id_raises(conn):
    with pytest.raises(db.DeadlineNotFoundError):
        db.complete_deadline(conn, 9999)


def test_get_connection_creates_parent_directory(tmp_path):
    nested_path = str(tmp_path / "nested" / "sub" / "deadlines.db")
    db.get_connection(nested_path)
    assert os.path.isdir(os.path.dirname(nested_path))
    assert os.path.isfile(nested_path)
