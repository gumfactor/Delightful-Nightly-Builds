"""Deadline computations for RRSP contributions and TFSA room.

Every function here takes the "as of" date explicitly rather than calling
`date.today()` internally, so the whole module is deterministic and
testable regardless of which real calendar day the tests run on. Only the
CLI entrypoint supplies the real current date.
"""

from __future__ import annotations

from datetime import date, timedelta

from .rrsp import rrif_conversion_year

_SATURDAY = 5
_SUNDAY = 6


def rrsp_contribution_deadline(tax_year: int) -> date:
    """The last day a contribution can still count toward `tax_year`.

    CRA rule: 60 days after the end of the calendar year, shifted to the
    next business day if that lands on a weekend.
    """
    deadline = date(tax_year, 12, 31) + timedelta(days=60)
    while deadline.weekday() in (_SATURDAY, _SUNDAY):
        deadline += timedelta(days=1)
    return deadline


def current_rrsp_grace_window(as_of: date) -> tuple[bool, int | None]:
    """Is `as_of` inside the first-60-days window for the prior tax year?

    Returns (in_window, tax_year_it_applies_to).
    """
    prior_tax_year = as_of.year - 1
    prior_deadline = rrsp_contribution_deadline(prior_tax_year)
    if as_of <= prior_deadline:
        return True, prior_tax_year
    return False, None


def next_rrsp_deadline(as_of: date) -> tuple[date, int]:
    """The next upcoming RRSP contribution deadline and the tax year it covers.

    If `as_of` is still inside the grace window for the prior tax year,
    that deadline is the one returned; otherwise it's the deadline for the
    current tax year (falling in the following calendar year).
    """
    in_window, tax_year = current_rrsp_grace_window(as_of)
    if in_window:
        assert tax_year is not None
        return rrsp_contribution_deadline(tax_year), tax_year
    return rrsp_contribution_deadline(as_of.year), as_of.year


def next_tfsa_room_date(as_of: date) -> date:
    """January 1 of the year following `as_of` — when the next TFSA room opens."""
    return date(as_of.year + 1, 1, 1)


def days_until(target: date, as_of: date) -> int:
    return (target - as_of).days


def rrif_deadline_date(birth_year: int) -> date:
    """December 31 of the year the holder must have converted to a RRIF."""
    return date(rrif_conversion_year(birth_year), 12, 31)


def rrif_deadline_status(birth_year: int, as_of: date) -> tuple[date, int, bool]:
    """Returns (deadline_date, years_until_71, already_past_deadline)."""
    deadline = rrif_deadline_date(birth_year)
    years_until_71 = rrif_conversion_year(birth_year) - as_of.year
    already_past = as_of > deadline
    return deadline, years_until_71, already_past
