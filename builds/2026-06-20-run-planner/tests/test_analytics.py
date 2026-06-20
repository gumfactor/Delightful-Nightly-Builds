"""Tests for analytics.py — weekly stats, streaks, mileage aggregation."""

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import analytics


def _run(run_date: str, distance_km: float = 5.0, duration_seconds: int = 1500) -> dict:
    """Helper to build a minimal run dict."""
    return {
        "date": run_date,
        "distance_km": distance_km,
        "duration_seconds": duration_seconds,
        "effort": "moderate",
        "notes": "",
        "pace": "5:00",
    }


# ---------------------------------------------------------------------------
# weekly_mileage
# ---------------------------------------------------------------------------

def test_weekly_mileage_sums_correctly():
    # 2026-06-15 is ISO week 25, 2026
    runs = [
        _run("2026-06-15", 5.0),
        _run("2026-06-16", 8.0),
        _run("2026-06-17", 10.0),
    ]
    assert analytics.weekly_mileage(runs, 2026, 25) == 23.0


def test_weekly_mileage_empty_week_returns_zero():
    runs = [_run("2026-06-15", 5.0)]
    assert analytics.weekly_mileage(runs, 2026, 24) == 0.0


def test_weekly_mileage_excludes_other_weeks():
    runs = [_run("2026-06-15", 5.0), _run("2026-06-22", 8.0)]  # different weeks
    assert analytics.weekly_mileage(runs, 2026, 25) == 5.0


# ---------------------------------------------------------------------------
# mileage_by_week
# ---------------------------------------------------------------------------

def test_mileage_by_week_groups_correctly():
    runs = [_run("2026-06-15", 5.0), _run("2026-06-16", 8.0)]
    result = analytics.mileage_by_week(runs)
    assert len(result) == 1
    assert result[0]["km"] == 13.0


def test_mileage_by_week_multiple_weeks():
    runs = [_run("2026-06-15", 5.0), _run("2026-06-22", 8.0)]
    result = analytics.mileage_by_week(runs)
    assert len(result) == 2
    assert result[0]["km"] == 5.0
    assert result[1]["km"] == 8.0


def test_mileage_by_week_empty_returns_empty():
    assert analytics.mileage_by_week([]) == []


# ---------------------------------------------------------------------------
# current_streak
# ---------------------------------------------------------------------------

def test_current_streak_no_runs_returns_zero():
    assert analytics.current_streak([], reference_date=date(2026, 6, 20)) == 0


def test_current_streak_single_run_today():
    runs = [_run("2026-06-20")]
    assert analytics.current_streak(runs, reference_date=date(2026, 6, 20)) == 1


def test_current_streak_consecutive_three_days():
    runs = [_run("2026-06-18"), _run("2026-06-19"), _run("2026-06-20")]
    assert analytics.current_streak(runs, reference_date=date(2026, 6, 20)) == 3


def test_current_streak_breaks_on_gap():
    # Runs on 18th and 20th but not 19th — streak from 20th back = 1
    runs = [_run("2026-06-18"), _run("2026-06-20")]
    assert analytics.current_streak(runs, reference_date=date(2026, 6, 20)) == 1


def test_current_streak_zero_if_most_recent_run_too_old():
    runs = [_run("2026-06-17")]
    # Reference date is 2026-06-20, most recent run is 3 days ago
    assert analytics.current_streak(runs, reference_date=date(2026, 6, 20)) == 0


def test_current_streak_run_yesterday_counts():
    runs = [_run("2026-06-19")]
    # Yesterday counts — streak = 1
    assert analytics.current_streak(runs, reference_date=date(2026, 6, 20)) == 1


# ---------------------------------------------------------------------------
# average_pace_seconds
# ---------------------------------------------------------------------------

def test_average_pace_seconds_single_run():
    runs = [_run("2026-06-20", distance_km=10.0, duration_seconds=3600)]
    assert analytics.average_pace_seconds(runs) == 360.0


def test_average_pace_seconds_empty_returns_zero():
    assert analytics.average_pace_seconds([]) == 0.0


# ---------------------------------------------------------------------------
# weekly_summary
# ---------------------------------------------------------------------------

def test_weekly_summary_run_count(monkeypatch):
    ref = date(2026, 6, 20)  # Saturday, ISO week 25
    runs = [_run("2026-06-16"), _run("2026-06-18"), _run("2026-06-20")]
    s = analytics.weekly_summary(runs, reference_date=ref)
    assert s["run_count"] == 3


def test_weekly_summary_empty_week(monkeypatch):
    ref = date(2026, 6, 20)
    s = analytics.weekly_summary([], reference_date=ref)
    assert s["run_count"] == 0
    assert s["total_km"] == 0.0
    assert s["avg_pace"] == "--:--"
