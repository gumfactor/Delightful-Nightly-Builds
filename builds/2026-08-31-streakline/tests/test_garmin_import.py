"""Unit tests for src/garmin_import.py — CSV parsing and habit matching."""

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import StreakDB
from src.garmin_import import (
    ActivityRow,
    import_activities,
    list_activity_types,
    parse_garmin_csv,
)

_HABITS = [
    {"id": "running", "name": "Running", "cadence": "daily", "source": "garmin",
     "garmin_activity_types": ["Running", "Trail Running"]},
    {"id": "golf", "name": "Golf", "cadence": "weekly", "source": "garmin",
     "garmin_activity_types": ["Golf"]},
    {"id": "writing", "name": "Writing", "cadence": "daily", "source": "manual"},
]


@pytest.fixture
def db(tmp_path: Path) -> StreakDB:
    return StreakDB(tmp_path / "test.db")


def _write_csv(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "activities.csv"
    path.write_text(content, encoding="utf-8")
    return path


def test_parse_garmin_csv_reads_valid_rows(tmp_path: Path) -> None:
    csv_content = (
        "Activity Type,Date,Title\n"
        "Running,2026-08-21 06:18:52,Morning Run\n"
        "Golf,2026-08-16 09:10:00,Weekend Round\n"
    )
    rows, warnings = parse_garmin_csv(_write_csv(tmp_path, csv_content))
    assert warnings == []
    assert len(rows) == 2
    assert rows[0] == ActivityRow(date(2026, 8, 21), "Running", "Morning Run")


def test_parse_garmin_csv_skips_missing_type_or_date(tmp_path: Path) -> None:
    csv_content = (
        "Activity Type,Date,Title\n"
        "Running,2026-08-21 06:18:52,Morning Run\n"
        ",2026-08-20 06:18:52,No Type\n"
        "Golf,,No Date\n"
    )
    rows, warnings = parse_garmin_csv(_write_csv(tmp_path, csv_content))
    assert len(rows) == 1
    assert len(warnings) == 2


def test_parse_garmin_csv_skips_unparseable_date(tmp_path: Path) -> None:
    csv_content = "Activity Type,Date,Title\nRunning,not-a-date,Morning Run\n"
    rows, warnings = parse_garmin_csv(_write_csv(tmp_path, csv_content))
    assert rows == []
    assert len(warnings) == 1
    assert "unparseable date" in warnings[0]


def test_parse_garmin_csv_missing_required_columns(tmp_path: Path) -> None:
    csv_content = "Distance,Calories\n5.0,400\n"
    rows, warnings = parse_garmin_csv(_write_csv(tmp_path, csv_content))
    assert rows == []
    assert len(warnings) == 1


def test_parse_garmin_csv_empty_file(tmp_path: Path) -> None:
    rows, warnings = parse_garmin_csv(_write_csv(tmp_path, ""))
    assert rows == []
    assert warnings == ["CSV has no header row"]


def test_list_activity_types_deduped_and_sorted() -> None:
    rows = [
        ActivityRow(date(2026, 8, 1), "Running", ""),
        ActivityRow(date(2026, 8, 2), "Golf", ""),
        ActivityRow(date(2026, 8, 3), "Running", ""),
    ]
    assert list_activity_types(rows) == ["Golf", "Running"]


def test_import_activities_matches_case_insensitively(db: StreakDB) -> None:
    rows = [ActivityRow(date(2026, 8, 21), "running", "Morning Run")]
    summary = import_activities(rows, _HABITS, db)
    assert summary.matched_rows == 1
    assert summary.inserted == 1
    assert db.get_dates("running") == {date(2026, 8, 21)}


def test_import_activities_same_day_multiple_activities_collapse(db: StreakDB) -> None:
    rows = [
        ActivityRow(date(2026, 8, 21), "Running", "Morning Run"),
        ActivityRow(date(2026, 8, 21), "Trail Running", "Second Run"),
    ]
    summary = import_activities(rows, _HABITS, db)
    assert summary.inserted == 1
    assert summary.already_recorded == 1
    assert db.get_dates("running") == {date(2026, 8, 21)}


def test_import_activities_unmatched_type_reported_not_inserted(db: StreakDB) -> None:
    rows = [ActivityRow(date(2026, 8, 21), "Cycling", "Weekend Ride")]
    summary = import_activities(rows, _HABITS, db)
    assert summary.matched_rows == 0
    assert summary.inserted == 0
    assert summary.unmatched_types == {"Cycling"}


def test_import_activities_manual_source_habits_never_matched(db: StreakDB) -> None:
    """A habit with source='manual' has no garmin_activity_types and must
    never receive a Garmin-imported completion, even by accident."""
    rows = [ActivityRow(date(2026, 8, 21), "Writing", "Blog post")]
    summary = import_activities(rows, _HABITS, db)
    assert summary.matched_rows == 0
    assert summary.unmatched_types == {"Writing"}


def test_import_activities_idempotent_on_reimport(db: StreakDB) -> None:
    rows = [ActivityRow(date(2026, 8, 21), "Running", "Morning Run")]
    first = import_activities(rows, _HABITS, db)
    second = import_activities(rows, _HABITS, db)
    assert first.inserted == 1
    assert second.inserted == 0
    assert second.already_recorded == 1
    assert len(db.get_all()) == 1
