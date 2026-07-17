from datetime import date

import pytest

from src.recurrence import (
    InvalidRecurrenceError,
    add_months,
    next_due_date,
    validate_recurrence,
)


def test_add_months_simple():
    assert add_months(date(2027, 1, 15), 2) == date(2027, 3, 15)


def test_add_months_year_rollover():
    assert add_months(date(2027, 11, 1), 3) == date(2028, 2, 1)


def test_add_months_day_clamp_jan31_to_feb():
    assert add_months(date(2027, 1, 31), 1) == date(2027, 2, 28)


def test_add_months_leap_year_feb29():
    # 2028 is a leap year; adding 12 months lands on a non-leap year, so
    # Feb 29 must clamp to Feb 28 rather than raise.
    assert add_months(date(2028, 2, 29), 12) == date(2029, 2, 28)


def test_next_due_date_none_returns_none():
    assert next_due_date(date(2027, 1, 1), "none", None) is None


def test_next_due_date_annual():
    assert next_due_date(date(2027, 3, 15), "annual", None) == date(2028, 3, 15)


def test_next_due_date_semesterly():
    assert next_due_date(date(2027, 1, 15), "semesterly", None) == date(2027, 7, 15)


def test_next_due_date_every_n_months():
    assert next_due_date(date(2027, 1, 15), "every_N_months", 3) == date(2027, 4, 15)


def test_next_due_date_every_n_months_missing_months_raises():
    with pytest.raises(InvalidRecurrenceError):
        next_due_date(date(2027, 1, 15), "every_N_months", None)


def test_next_due_date_unknown_recurrence_raises():
    with pytest.raises(InvalidRecurrenceError):
        next_due_date(date(2027, 1, 15), "weekly", None)


def test_validate_recurrence_accepts_none():
    validate_recurrence("none", None)  # should not raise


def test_validate_recurrence_every_n_months_requires_months():
    with pytest.raises(InvalidRecurrenceError):
        validate_recurrence("every_N_months", None)


def test_validate_recurrence_rejects_months_when_not_custom():
    with pytest.raises(InvalidRecurrenceError):
        validate_recurrence("annual", 6)


def test_validate_recurrence_rejects_unknown_rule():
    with pytest.raises(InvalidRecurrenceError):
        validate_recurrence("biweekly", None)
