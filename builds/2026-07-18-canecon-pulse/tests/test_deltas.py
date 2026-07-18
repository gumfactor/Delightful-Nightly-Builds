from datetime import date

from src.deltas import compute_deltas


def test_empty_history_returns_none():
    assert compute_deltas([]) is None


def test_single_observation_has_no_deltas():
    summary = compute_deltas([(date(2026, 7, 1), 1.36)])

    assert summary.latest_value == 1.36
    assert summary.day is None
    assert summary.week is None
    assert summary.month is None


def test_day_delta_within_tolerance():
    history = [(date(2026, 7, 1), 1.36), (date(2026, 7, 2), 1.365)]
    summary = compute_deltas(history)

    assert summary.day is not None
    assert summary.day.compare_date == date(2026, 7, 1)
    assert round(summary.day.change, 4) == 0.005


def test_month_delta_within_tolerance():
    history = [(date(2026, 6, 1), 160.0), (date(2026, 7, 1), 161.0)]
    summary = compute_deltas(history)

    assert summary.month is not None
    assert summary.month.compare_date == date(2026, 6, 1)
    assert summary.month.change == 1.0
    assert round(summary.month.pct_change, 4) == round(1.0 / 160.0 * 100, 4)


def test_delta_outside_tolerance_returns_none():
    # Only a comparison point ~100 days old exists, far outside the
    # day-over-day tolerance window (2 days) — must not be mislabeled.
    history = [(date(2026, 3, 24), 158.0), (date(2026, 7, 1), 161.0)]
    summary = compute_deltas(history)

    assert summary.day is None


def test_zero_comparison_value_avoids_division_by_zero():
    history = [(date(2026, 6, 1), 0.0), (date(2026, 7, 1), 1.0)]
    summary = compute_deltas(history)

    assert summary.month is not None
    assert summary.month.change == 1.0
    assert summary.month.pct_change is None
