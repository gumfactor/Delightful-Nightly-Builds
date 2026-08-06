import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test.db")
    connection = db.connect(db_path)
    yield connection
    connection.close()


def test_add_manuscript_creates_row_with_submitted_status(conn):
    manuscript_id = db.add_manuscript(
        conn, "A Study of Things", "Jane Doe, John Smith", "Journal of Examples",
        "original-research", "2026-08-01",
    )
    row = db.get_manuscript(conn, manuscript_id)
    assert row["status"] == "submitted"
    assert row["title"] == "A Study of Things"
    assert row["expected_review_days"] == 90


def test_add_manuscript_rejects_invalid_type(conn):
    with pytest.raises(db.InvalidStatusError):
        db.add_manuscript(conn, "X", "A", "J", "not-a-real-type", "2026-08-01")


def test_add_manuscript_logs_initial_status(conn):
    manuscript_id = db.add_manuscript(conn, "X", "A", "J", "review", "2026-08-01")
    log = db.get_status_log(conn, manuscript_id)
    assert len(log) == 1
    assert log[0]["status"] == "submitted"
    assert log[0]["source"] == "manual"


def test_get_manuscript_raises_on_missing_id(conn):
    with pytest.raises(db.ManuscriptNotFoundError):
        db.get_manuscript(conn, 999)


def test_list_manuscripts_orders_by_submitted_date(conn):
    db.add_manuscript(conn, "Later", "A", "J", "review", "2026-08-10")
    db.add_manuscript(conn, "Earlier", "A", "J", "review", "2026-08-01")
    rows = db.list_manuscripts(conn)
    assert [r["title"] for r in rows] == ["Earlier", "Later"]


def test_update_status_appends_to_log_without_deleting_history(conn):
    manuscript_id = db.add_manuscript(conn, "X", "A", "J", "review", "2026-08-01")
    db.update_status(conn, manuscript_id, "under_review", note="Sent to reviewers")
    db.update_status(conn, manuscript_id, "revise_resubmit", note="Major revision requested",
                      revision_deadline="2026-09-01")
    log = db.get_status_log(conn, manuscript_id)
    assert [entry["status"] for entry in log] == ["submitted", "under_review", "revise_resubmit"]
    row = db.get_manuscript(conn, manuscript_id)
    assert row["status"] == "revise_resubmit"
    assert row["revision_deadline"] == "2026-09-01"


def test_update_status_rejects_invalid_status(conn):
    manuscript_id = db.add_manuscript(conn, "X", "A", "J", "review", "2026-08-01")
    with pytest.raises(db.InvalidStatusError):
        db.update_status(conn, manuscript_id, "not_a_status")


def test_update_status_raises_on_missing_manuscript(conn):
    with pytest.raises(db.ManuscriptNotFoundError):
        db.update_status(conn, 999, "under_review")


def test_update_status_sets_doi_and_published_date(conn):
    manuscript_id = db.add_manuscript(conn, "X", "A", "J", "review", "2026-08-01")
    db.update_status(conn, manuscript_id, "published", doi="10.1000/xyz123", published_date="2026-08-05")
    row = db.get_manuscript(conn, manuscript_id)
    assert row["doi"] == "10.1000/xyz123"
    assert row["published_date"] == "2026-08-05"


def test_days_in_stage_computes_from_submitted_date(conn):
    manuscript_id = db.add_manuscript(conn, "X", "A", "J", "review", "2026-01-01")
    row = db.get_manuscript(conn, manuscript_id)
    assert db.days_in_stage(row, today=date(2026, 3, 2)) == 60


def test_days_in_stage_handles_leap_year_boundary(conn):
    # 2028 is a leap year; Feb 29 exists, so Jan 1 -> Mar 1 should be 60 days.
    manuscript_id = db.add_manuscript(conn, "X", "A", "J", "review", "2028-01-01")
    row = db.get_manuscript(conn, manuscript_id)
    assert db.days_in_stage(row, today=date(2028, 3, 1)) == 60


def test_is_at_risk_false_when_under_expected_review_days(conn):
    manuscript_id = db.add_manuscript(conn, "X", "A", "J", "review", "2026-08-01", expected_review_days=90)
    row = db.get_manuscript(conn, manuscript_id)
    assert db.is_at_risk(row, today=date(2026, 9, 1)) is False


def test_is_at_risk_true_just_over_expected_review_days(conn):
    manuscript_id = db.add_manuscript(conn, "X", "A", "J", "review", "2026-01-01", expected_review_days=90)
    row = db.get_manuscript(conn, manuscript_id)
    # 91 days after Jan 1 2026 -> exceeds the 90-day threshold
    assert db.is_at_risk(row, today=date(2026, 4, 2)) is True


def test_is_at_risk_exactly_at_threshold_is_not_yet_at_risk(conn):
    manuscript_id = db.add_manuscript(conn, "X", "A", "J", "review", "2026-01-01", expected_review_days=90)
    row = db.get_manuscript(conn, manuscript_id)
    assert db.is_at_risk(row, today=date(2026, 4, 1)) is False  # exactly 90 days


def test_is_at_risk_for_revise_resubmit_past_deadline(conn):
    manuscript_id = db.add_manuscript(conn, "X", "A", "J", "review", "2026-01-01")
    db.update_status(conn, manuscript_id, "revise_resubmit", revision_deadline="2026-09-01")
    row = db.get_manuscript(conn, manuscript_id)
    assert db.is_at_risk(row, today=date(2026, 9, 2)) is True
    assert db.is_at_risk(row, today=date(2026, 8, 30)) is False


def test_is_at_risk_false_for_terminal_statuses(conn):
    manuscript_id = db.add_manuscript(conn, "X", "A", "J", "review", "2020-01-01")
    db.update_status(conn, manuscript_id, "published")
    row = db.get_manuscript(conn, manuscript_id)
    assert db.is_at_risk(row, today=date(2026, 1, 1)) is False


def test_row_to_dict_returns_plain_dict(conn):
    manuscript_id = db.add_manuscript(conn, "X", "A", "J", "review", "2026-08-01")
    row = db.get_manuscript(conn, manuscript_id)
    d = db.row_to_dict(row)
    assert isinstance(d, dict)
    assert d["title"] == "X"
