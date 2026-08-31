"""Unit tests for src/streaks.py — pure daily/weekly streak and
completion-rate math."""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.streaks import completion_rate, daily_streak, weekly_streak


# ── daily_streak ─────────────────────────────────────────────────────────

def test_daily_streak_empty_history() -> None:
    info = daily_streak(set(), date(2026, 8, 21))
    assert info.current == 0
    assert info.longest == 0


def test_daily_streak_single_day_today() -> None:
    info = daily_streak({date(2026, 8, 21)}, date(2026, 8, 21))
    assert info.current == 1
    assert info.longest == 1


def test_daily_streak_active_run_including_today() -> None:
    dates = {date(2026, 8, 18), date(2026, 8, 19), date(2026, 8, 20), date(2026, 8, 21)}
    info = daily_streak(dates, date(2026, 8, 21))
    assert info.current == 4
    assert info.longest == 4


def test_daily_streak_grace_period_yesterday_only() -> None:
    """Today has no completion yet, but yesterday does — the streak is
    still current (the day isn't over)."""
    dates = {date(2026, 8, 19), date(2026, 8, 20)}
    info = daily_streak(dates, date(2026, 8, 21))
    assert info.current == 2


def test_daily_streak_broken_two_days_ago() -> None:
    """Nothing yesterday or today — the streak is broken, even though the
    day before yesterday was completed."""
    dates = {date(2026, 8, 19)}
    info = daily_streak(dates, date(2026, 8, 21))
    assert info.current == 0
    assert info.longest == 1


def test_daily_streak_longest_is_in_the_past() -> None:
    """A 5-day run earlier in the history is longer than the current
    1-day run — longest must reflect the past run, current only the
    present one."""
    dates = {
        date(2026, 8, 1), date(2026, 8, 2), date(2026, 8, 3),
        date(2026, 8, 4), date(2026, 8, 5),
        date(2026, 8, 21),
    }
    info = daily_streak(dates, date(2026, 8, 21))
    assert info.current == 1
    assert info.longest == 5


def test_daily_streak_leap_year_boundary() -> None:
    """Feb 28 -> Feb 29 -> Mar 1 in a leap year (2028) must count as three
    consecutive days, not break at the month boundary."""
    dates = {date(2028, 2, 28), date(2028, 2, 29), date(2028, 3, 1)}
    info = daily_streak(dates, date(2028, 3, 1))
    assert info.current == 3
    assert info.longest == 3


def test_daily_streak_non_leap_year_feb_to_mar() -> None:
    """In a non-leap year Feb has 28 days, so Feb 28 and Mar 1 are
    genuinely one calendar day apart — confirms the engine relies on real
    date arithmetic (timedelta) rather than a hardcoded days-per-month
    assumption that could misfire around this boundary."""
    dates = {date(2027, 2, 28), date(2027, 3, 1)}
    info = daily_streak(dates, date(2027, 3, 1))
    assert info.current == 2
    assert info.longest == 2


# ── weekly_streak ────────────────────────────────────────────────────────

def test_weekly_streak_empty_history() -> None:
    info = weekly_streak(set(), date(2026, 8, 21))
    assert info.current == 0
    assert info.longest == 0


def test_weekly_streak_consecutive_weeks() -> None:
    # Fridays in three consecutive ISO weeks.
    dates = {date(2026, 8, 2), date(2026, 8, 9), date(2026, 8, 16)}
    info = weekly_streak(dates, date(2026, 8, 16))
    assert info.current == 3
    assert info.longest == 3


def test_weekly_streak_same_week_different_days_counts_once() -> None:
    dates = {date(2026, 8, 3), date(2026, 8, 5), date(2026, 8, 7)}  # all ISO week 32
    info = weekly_streak(dates, date(2026, 8, 7))
    assert info.current == 1
    assert info.longest == 1


def test_weekly_streak_grace_period_last_week_only() -> None:
    """This week has nothing yet, but last week does — still current."""
    dates = {date(2026, 8, 9)}  # a week before as_of
    info = weekly_streak(dates, date(2026, 8, 16))
    assert info.current == 1


def test_weekly_streak_broken_two_weeks_ago() -> None:
    dates = {date(2026, 8, 2)}
    info = weekly_streak(dates, date(2026, 8, 16))
    assert info.current == 0
    assert info.longest == 1


# ── completion_rate ──────────────────────────────────────────────────────

def test_completion_rate_daily_full_window() -> None:
    dates = {date(2026, 8, 1), date(2026, 8, 2), date(2026, 8, 3)}
    rate = completion_rate(dates, date(2026, 8, 1), date(2026, 8, 3), "daily")
    assert rate == 1.0


def test_completion_rate_daily_partial_window() -> None:
    dates = {date(2026, 8, 1), date(2026, 8, 3)}
    rate = completion_rate(dates, date(2026, 8, 1), date(2026, 8, 4), "daily")
    assert rate == 0.5


def test_completion_rate_no_completions_is_zero_not_error() -> None:
    rate = completion_rate(set(), date(2026, 8, 1), date(2026, 8, 10), "daily")
    assert rate == 0.0


def test_completion_rate_inverted_range_is_zero() -> None:
    rate = completion_rate({date(2026, 8, 5)}, date(2026, 8, 10), date(2026, 8, 1), "daily")
    assert rate == 0.0


def test_completion_rate_weekly() -> None:
    # Two of three ISO weeks touched by the range have a completion.
    dates = {date(2026, 8, 3), date(2026, 8, 17)}
    rate = completion_rate(dates, date(2026, 8, 3), date(2026, 8, 17), "weekly")
    assert round(rate, 4) == round(2 / 3, 4)
