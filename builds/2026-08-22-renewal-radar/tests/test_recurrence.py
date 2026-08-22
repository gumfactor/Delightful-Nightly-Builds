from datetime import date

import pytest

from src.recurrence import days_until, next_occurrence


def test_one_time_has_no_next_occurrence():
    assert next_occurrence(date(2027, 1, 1), "one-time") is None


def test_monthly_advances_one_month():
    assert next_occurrence(date(2027, 1, 15), "monthly") == date(2027, 2, 15)


def test_annual_advances_one_year():
    assert next_occurrence(date(2027, 3, 10), "annual") == date(2028, 3, 10)


def test_every_n_months_advances_n_months():
    assert next_occurrence(date(2027, 1, 1), "every-N-months", recurrence_n=4) == date(2027, 5, 1)


def test_every_n_months_requires_positive_n():
    with pytest.raises(ValueError):
        next_occurrence(date(2027, 1, 1), "every-N-months", recurrence_n=0)
    with pytest.raises(ValueError):
        next_occurrence(date(2027, 1, 1), "every-N-months", recurrence_n=None)


def test_leap_year_feb29_annual_renewal_lands_on_feb28_in_non_leap_year():
    # 2028 is a leap year (Feb 29 exists); 2029 is not.
    assert next_occurrence(date(2028, 2, 29), "annual") == date(2029, 2, 28)


def test_31_day_month_due_date_clamps_into_shorter_month():
    # Jan 31 + 1 month must not overflow into March; Feb 2027 has 28 days.
    assert next_occurrence(date(2027, 1, 31), "monthly") == date(2027, 2, 28)


def test_31_day_month_due_date_clamps_in_leap_february():
    assert next_occurrence(date(2028, 1, 31), "monthly") == date(2028, 2, 29)


def test_unknown_recurrence_type_raises():
    with pytest.raises(ValueError):
        next_occurrence(date(2027, 1, 1), "weekly")


def test_days_until_future_is_positive():
    assert days_until(date(2027, 1, 10), date(2027, 1, 1)) == 9


def test_days_until_past_is_negative():
    assert days_until(date(2027, 1, 1), date(2027, 1, 10)) == -9


def test_days_until_today_is_zero():
    assert days_until(date(2027, 1, 1), date(2027, 1, 1)) == 0
