"""Leap-year- and month-length-safe recurrence date math."""

from __future__ import annotations

import calendar
from datetime import date


def _add_months(start: date, months: int) -> date:
    """Add whole months to a date, clamping the day to the target month's length.

    Feb 29 + 12 months lands on Feb 28 in a non-leap year. Jan 31 + 1 month
    lands on Feb 28/29 rather than overflowing into March.
    """
    total_month_index = start.month - 1 + months
    target_year = start.year + total_month_index // 12
    target_month = total_month_index % 12 + 1
    last_day = calendar.monthrange(target_year, target_month)[1]
    target_day = min(start.day, last_day)
    return date(target_year, target_month, target_day)


def next_occurrence(due_date: date, recurrence: str, recurrence_n: int | None = None) -> date | None:
    """Return the next due date after completing an occurrence, or None for one-time items."""
    if recurrence == "one-time":
        return None
    if recurrence == "monthly":
        return _add_months(due_date, 1)
    if recurrence == "annual":
        return _add_months(due_date, 12)
    if recurrence == "every-N-months":
        if not recurrence_n or recurrence_n < 1:
            raise ValueError("recurrence_n must be a positive integer for 'every-N-months' recurrence")
        return _add_months(due_date, recurrence_n)
    raise ValueError(f"Unknown recurrence type: {recurrence}")


def days_until(target: date, today: date) -> int:
    """Positive if target is in the future, negative if overdue, 0 if today."""
    return (target - today).days
