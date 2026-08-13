import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src import garmin_import

BUILD_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CSV = BUILD_ROOT / "sample_data" / "sample_garmin_activities.csv"


def test_parses_sample_csv_successfully():
    summary = garmin_import.parse_activities_csv(str(SAMPLE_CSV))
    assert summary.warnings == []
    assert summary.activity_count > 0


def test_sample_csv_window_is_most_recent_7_days_relative_to_max_date():
    summary = garmin_import.parse_activities_csv(str(SAMPLE_CSV))
    # Max date in the fixture is 2026-08-10; window should be 2026-08-04..2026-08-10.
    assert summary.window_start == "2026-08-04"
    assert summary.window_end == "2026-08-10"


def test_sample_csv_window_activity_count_matches_fixture():
    # Rows within 2026-08-04..2026-08-10 in the fixture: 08-04, 08-05, 08-06, 08-08, 08-09, 08-10
    summary = garmin_import.parse_activities_csv(str(SAMPLE_CSV))
    assert summary.activity_count == 6


def test_daily_adjustment_is_positive_for_active_window():
    summary = garmin_import.parse_activities_csv(str(SAMPLE_CSV))
    assert summary.daily_adjustment_kcal > 0


def test_daily_adjustment_capped_at_maximum():
    # Even an enormous single-day calorie burn shouldn't blow past the cap.
    summary = garmin_import.GarminSummary(
        window_start="2026-01-01", window_end="2026-01-07",
        total_distance_km=500, total_duration_min=6000, total_calories=50000,
        activity_count=1, daily_adjustment_kcal=0, warnings=[],
    )
    computed = min((summary.total_calories * 0.5) / 7, garmin_import.MAX_DAILY_ADJUSTMENT_KCAL)
    assert computed == garmin_import.MAX_DAILY_ADJUSTMENT_KCAL


def test_missing_calories_column_degrades_gracefully(tmp_path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("Date,Distance\n2026-08-01,5.0\n")
    summary = garmin_import.parse_activities_csv(str(bad_csv))
    assert summary.activity_count == 0
    assert summary.daily_adjustment_kcal == 0.0
    assert len(summary.warnings) == 1
    assert "Calories" in summary.warnings[0]


def test_nonexistent_file_degrades_gracefully():
    summary = garmin_import.parse_activities_csv("/nonexistent/path/does-not-exist.csv")
    assert summary.activity_count == 0
    assert summary.daily_adjustment_kcal == 0.0
    assert len(summary.warnings) == 1


def test_rows_with_unparseable_dates_are_skipped(tmp_path):
    csv_path = tmp_path / "mixed.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Calories", "Distance"])
        writer.writerow(["not-a-date", "500", "5"])
        writer.writerow(["2026-08-01", "400", "6"])
    summary = garmin_import.parse_activities_csv(str(csv_path))
    assert summary.activity_count == 1


def test_empty_calories_field_treated_as_zero(tmp_path):
    csv_path = tmp_path / "empty_field.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Calories", "Distance"])
        writer.writerow(["2026-08-01", "", "5"])
    summary = garmin_import.parse_activities_csv(str(csv_path))
    assert summary.total_calories == 0.0
    assert summary.daily_adjustment_kcal == 0.0
