from datetime import date

from src.deadlines import (
    current_rrsp_grace_window,
    days_until,
    next_rrsp_deadline,
    next_tfsa_room_date,
    rrif_deadline_date,
    rrif_deadline_status,
    rrsp_contribution_deadline,
)


def test_rrsp_deadline_basic_case():
    # Dec 31 2022 + 60 days = a Wednesday, no weekend shift needed.
    assert rrsp_contribution_deadline(2022) == date(2023, 3, 1)


def test_rrsp_deadline_shifts_off_a_weekend():
    # Real, historical case: the raw 60-day calculation for the 2013 tax
    # year lands on Saturday 2014-03-01; the actual CRA deadline that year
    # was the following Monday, 2014-03-03.
    deadline = rrsp_contribution_deadline(2013)
    assert deadline == date(2014, 3, 3)
    assert deadline.weekday() == 0  # Monday


def test_rrsp_deadline_handles_leap_year_correctly():
    # 2011 + 60 days crosses into leap-year February 2012 -> Feb 29, a
    # Wednesday, so no shift, but only correct if leap-day math is right.
    deadline = rrsp_contribution_deadline(2011)
    assert deadline == date(2012, 2, 29)


def test_grace_window_true_in_january():
    in_window, tax_year = current_rrsp_grace_window(date(2024, 1, 15))
    assert in_window
    assert tax_year == 2023


def test_grace_window_false_after_deadline_passes():
    in_window, tax_year = current_rrsp_grace_window(date(2024, 6, 1))
    assert not in_window
    assert tax_year is None


def test_next_rrsp_deadline_during_grace_window():
    deadline, tax_year = next_rrsp_deadline(date(2024, 2, 1))
    assert tax_year == 2023
    assert deadline == rrsp_contribution_deadline(2023)


def test_next_rrsp_deadline_outside_grace_window():
    deadline, tax_year = next_rrsp_deadline(date(2024, 6, 1))
    assert tax_year == 2024
    assert deadline == rrsp_contribution_deadline(2024)


def test_next_tfsa_room_date_is_next_january_first():
    assert next_tfsa_room_date(date(2026, 9, 9)) == date(2027, 1, 1)
    assert next_tfsa_room_date(date(2026, 1, 1)) == date(2027, 1, 1)


def test_days_until_counts_forward():
    assert days_until(date(2026, 1, 10), date(2026, 1, 1)) == 9


def test_rrif_deadline_date_is_december_31():
    assert rrif_deadline_date(1955) == date(2026, 12, 31)


def test_rrif_deadline_status_before_71():
    deadline, years_until, past = rrif_deadline_status(1960, date(2026, 6, 1))
    assert deadline == date(2031, 12, 31)
    assert years_until == 5
    assert not past


def test_rrif_deadline_status_after_71():
    deadline, years_until, past = rrif_deadline_status(1950, date(2026, 6, 1))
    assert past
    assert years_until < 0
