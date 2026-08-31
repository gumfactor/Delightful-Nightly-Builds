"""Pure streak/consistency math. No I/O — every function takes plain data in
and returns plain data out, so the whole engine is testable without a
database or a clock.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class StreakInfo:
    current: int
    longest: int


def _iso_week(day: date) -> tuple[int, int]:
    year, week, _ = day.isocalendar()
    return (year, week)


def _week_start(day: date) -> date:
    """Return the Monday of the ISO week containing ``day``."""
    return day - timedelta(days=day.weekday())


def daily_streak(done_dates: set[date], as_of: date) -> StreakInfo:
    """Current and longest run of consecutive calendar days.

    ``current`` counts backward from ``as_of``. If ``as_of`` itself has no
    completion, a single grace day is allowed: the streak still counts as
    "current" if ``as_of - 1`` was completed (the habit isn't broken until a
    full day has passed with nothing logged). Once two consecutive days are
    missing, the current streak is 0.
    """
    if not done_dates:
        return StreakInfo(current=0, longest=0)

    sorted_dates = sorted(done_dates)

    longest = 1
    run = 1
    for prev, nxt in zip(sorted_dates, sorted_dates[1:]):
        if nxt - prev == timedelta(days=1):
            run += 1
        else:
            run = 1
        longest = max(longest, run)

    if as_of in done_dates:
        anchor = as_of
    elif (as_of - timedelta(days=1)) in done_dates:
        anchor = as_of - timedelta(days=1)
    else:
        return StreakInfo(current=0, longest=longest)

    current = 1
    cursor = anchor
    while (cursor - timedelta(days=1)) in done_dates:
        cursor -= timedelta(days=1)
        current += 1

    return StreakInfo(current=current, longest=longest)


def weekly_streak(done_dates: set[date], as_of: date) -> StreakInfo:
    """Current and longest run of consecutive ISO weeks with >=1 completion.

    Mirrors ``daily_streak``'s grace period one level up: if the current
    week has nothing yet, the streak still counts as current so long as last
    week had a completion (this week isn't over).
    """
    if not done_dates:
        return StreakInfo(current=0, longest=0)

    done_weeks = sorted({_week_start(d) for d in done_dates})

    longest = 1
    run = 1
    for prev, nxt in zip(done_weeks, done_weeks[1:]):
        if nxt - prev == timedelta(days=7):
            run += 1
        else:
            run = 1
        longest = max(longest, run)

    this_week = _week_start(as_of)
    last_week = this_week - timedelta(days=7)

    if this_week in done_weeks:
        anchor = this_week
    elif last_week in done_weeks:
        anchor = last_week
    else:
        return StreakInfo(current=0, longest=longest)

    done_week_set = set(done_weeks)
    current = 1
    cursor = anchor
    while (cursor - timedelta(days=7)) in done_week_set:
        cursor -= timedelta(days=7)
        current += 1

    return StreakInfo(current=current, longest=longest)


def completion_rate(
    done_dates: set[date],
    start: date,
    end: date,
    cadence: str,
) -> float:
    """Fraction of periods in [start, end] (inclusive) with >=1 completion.

    ``cadence`` is ``"daily"`` (periods are calendar days) or ``"weekly"``
    (periods are ISO weeks touched by the range). Returns 0.0 for an empty
    or inverted range rather than raising a divide-by-zero error.
    """
    if end < start:
        return 0.0

    if cadence == "weekly":
        total_weeks = ((_week_start(end) - _week_start(start)).days // 7) + 1
        if total_weeks <= 0:
            return 0.0
        done_weeks = {_week_start(d) for d in done_dates if start <= d <= end}
        return len(done_weeks) / total_weeks

    total_days = (end - start).days + 1
    if total_days <= 0:
        return 0.0
    done_days = {d for d in done_dates if start <= d <= end}
    return len(done_days) / total_days
