"""Unit tests for src/db.py — SQLite completion storage."""

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import StreakDB


@pytest.fixture
def db(tmp_path: Path) -> StreakDB:
    return StreakDB(tmp_path / "test.db")


def test_add_completion_returns_true_when_new(db: StreakDB) -> None:
    inserted = db.add_completion("running", date(2026, 8, 21), source="manual")
    assert inserted is True


def test_add_completion_returns_false_when_duplicate(db: StreakDB) -> None:
    db.add_completion("running", date(2026, 8, 21), source="manual")
    inserted_again = db.add_completion("running", date(2026, 8, 21), source="garmin")
    assert inserted_again is False


def test_add_completion_same_date_different_habit_both_succeed(db: StreakDB) -> None:
    first = db.add_completion("running", date(2026, 8, 21), source="manual")
    second = db.add_completion("golf", date(2026, 8, 21), source="manual")
    assert first is True
    assert second is True


def test_get_dates_returns_only_that_habits_dates(db: StreakDB) -> None:
    db.add_completion("running", date(2026, 8, 20), source="manual")
    db.add_completion("running", date(2026, 8, 21), source="manual")
    db.add_completion("golf", date(2026, 8, 21), source="manual")
    assert db.get_dates("running") == {date(2026, 8, 20), date(2026, 8, 21)}


def test_get_dates_empty_for_unknown_habit(db: StreakDB) -> None:
    assert db.get_dates("nonexistent") == set()


def test_remove_completion_returns_true_when_removed(db: StreakDB) -> None:
    db.add_completion("running", date(2026, 8, 21), source="manual")
    removed = db.remove_completion("running", date(2026, 8, 21))
    assert removed is True
    assert db.get_dates("running") == set()


def test_remove_completion_returns_false_when_nothing_to_remove(db: StreakDB) -> None:
    removed = db.remove_completion("running", date(2026, 8, 21))
    assert removed is False


def test_get_all_includes_source_and_detail(db: StreakDB) -> None:
    db.add_completion("running", date(2026, 8, 21), source="garmin", detail="Morning Run")
    rows = db.get_all()
    assert len(rows) == 1
    assert rows[0]["habit_id"] == "running"
    assert rows[0]["source"] == "garmin"
    assert rows[0]["detail"] == "Morning Run"


def test_db_persists_across_reopen(tmp_path: Path) -> None:
    path = tmp_path / "persist.db"
    StreakDB(path).add_completion("running", date(2026, 8, 21), source="manual")
    reopened = StreakDB(path)
    assert reopened.get_dates("running") == {date(2026, 8, 21)}
