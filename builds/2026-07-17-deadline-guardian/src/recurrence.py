"""Date math for recurring deadlines."""

from __future__ import annotations

import calendar
from datetime import date

VALID_RECURRENCES = ("none", "annual", "semesterly", "every_N_months")


class InvalidRecurrenceError(ValueError):
    """Raised when a recurrence rule or its parameters are invalid."""


def add_months(d: date, months: int) -> date:
    """Add a number of months to a date, clamping the day to the target
    month's length (e.g. Jan 31 + 1 month -> Feb 28, or Feb 29 in a leap year).
    """
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(d.day, last_day)
    return date(year, month, day)


def next_due_date(due_date: date, recurrence: str, recurrence_months: int | None) -> date | None:
    """Compute the next occurrence's due date after `due_date` is completed.

    Returns None for a non-recurring deadline.
    """
    if recurrence == "none":
        return None
    if recurrence == "annual":
        return add_months(due_date, 12)
    if recurrence == "semesterly":
        return add_months(due_date, 6)
    if recurrence == "every_N_months":
        if not recurrence_months or recurrence_months < 1:
            raise InvalidRecurrenceError(
                "every_N_months recurrence requires a positive recurrence_months value"
            )
        return add_months(due_date, recurrence_months)
    raise InvalidRecurrenceError(f"Unknown recurrence rule: {recurrence!r}")


def validate_recurrence(recurrence: str, recurrence_months: int | None) -> None:
    if recurrence not in VALID_RECURRENCES:
        raise InvalidRecurrenceError(
            f"recurrence must be one of {VALID_RECURRENCES}, got {recurrence!r}"
        )
    if recurrence == "every_N_months" and (not recurrence_months or recurrence_months < 1):
        raise InvalidRecurrenceError(
            "recurrence 'every_N_months' requires a positive recurrence_months value"
        )
    if recurrence != "every_N_months" and recurrence_months is not None:
        raise InvalidRecurrenceError(
            f"recurrence_months must be None unless recurrence is 'every_N_months' "
            f"(got recurrence={recurrence!r}, recurrence_months={recurrence_months!r})"
        )
