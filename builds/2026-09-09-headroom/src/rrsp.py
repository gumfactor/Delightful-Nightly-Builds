"""RRSP contribution room engine.

Implements the actual CRA rules:
- Each year's new room = lesser of (18% of the *previous* year's earned
  income) or that year's published dollar limit, minus the previous year's
  pension adjustment (never below zero).
- Unused room carries forward indefinitely — there is no expiry.
- A $2,000 lifetime grace buffer exists before the 1%-per-month
  overcontribution tax applies.
- No new contribution room (or contributions) is generated once past the
  RRSP-to-RRIF conversion deadline: December 31 of the year the holder
  turns 71.

Because this tool has no way to know a user's pre-tracking RRSP history,
callers should seed `opening_balance` with the deduction limit shown on the
user's actual CRA Notice of Assessment as of a given year — see Manual.md.
Without an opening balance, room is only computed from the earliest year of
earned-income data the user supplies (a documented limitation).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .limits import (
    RRIF_CONVERSION_AGE,
    RRSP_FIRST_YEAR,
    RRSP_OVERCONTRIBUTION_GRACE,
    OVERCONTRIBUTION_MONTHLY_PENALTY_RATE,
    rrsp_limit,
)


@dataclass(frozen=True)
class Contribution:
    txn_date: date
    amount: float
    tax_year: int


@dataclass(frozen=True)
class IncomeRecord:
    year: int
    earned_income: float
    pension_adjustment: float = 0.0


@dataclass(frozen=True)
class OpeningBalance:
    year: int
    amount: float


@dataclass(frozen=True)
class RRSPYearSnapshot:
    year: int
    room_generated: float
    contributions: float
    ending_balance: float


@dataclass(frozen=True)
class RRSPResult:
    as_of: date
    available_room: float
    is_overcontributed: bool
    overcontribution_amount: float
    estimated_monthly_penalty: float
    rrif_deadline_year: int | None
    past_rrif_deadline: bool
    year_snapshots: list[RRSPYearSnapshot] = field(default_factory=list)


def rrif_conversion_year(birth_year: int) -> int:
    """The year by which the holder must convert their RRSP to a RRIF."""
    return birth_year + RRIF_CONVERSION_AGE


def compute_rrsp(
    birth_year: int,
    contributions: list[Contribution],
    income_history: list[IncomeRecord],
    as_of: date,
    opening_balance: OpeningBalance | None = None,
) -> RRSPResult:
    rrif_year = rrif_conversion_year(birth_year)
    income_by_year = {r.year: r for r in income_history}

    if opening_balance is not None:
        start_year = opening_balance.year
        balance = opening_balance.amount
    else:
        start_year = min([r.year for r in income_history], default=RRSP_FIRST_YEAR) + 1
        start_year = max(start_year, RRSP_FIRST_YEAR)
        balance = 0.0

    contributions_by_tax_year: dict[int, float] = {}
    for c in contributions:
        if c.txn_date <= as_of:
            contributions_by_tax_year[c.tax_year] = (
                contributions_by_tax_year.get(c.tax_year, 0.0) + c.amount
            )

    snapshots: list[RRSPYearSnapshot] = []
    for year in range(start_year, as_of.year + 1):
        room_generated = 0.0
        if year <= rrif_year:
            prior = income_by_year.get(year - 1)
            if prior is not None:
                dollar_cap = rrsp_limit(year)
                room_generated = max(
                    0.0,
                    min(prior.earned_income * 0.18, dollar_cap) - prior.pension_adjustment,
                )
        balance += room_generated
        contributions_this_year = contributions_by_tax_year.get(year, 0.0)
        balance -= contributions_this_year
        snapshots.append(
            RRSPYearSnapshot(
                year=year,
                room_generated=room_generated,
                contributions=contributions_this_year,
                ending_balance=balance,
            )
        )

    is_over = balance < -RRSP_OVERCONTRIBUTION_GRACE
    overcontribution_amount = (-balance - RRSP_OVERCONTRIBUTION_GRACE) if is_over else 0.0
    monthly_penalty = (
        overcontribution_amount * OVERCONTRIBUTION_MONTHLY_PENALTY_RATE if is_over else 0.0
    )

    return RRSPResult(
        as_of=as_of,
        available_room=max(balance, 0.0),
        is_overcontributed=is_over,
        overcontribution_amount=overcontribution_amount,
        estimated_monthly_penalty=monthly_penalty,
        rrif_deadline_year=rrif_year,
        past_rrif_deadline=as_of.year > rrif_year,
        year_snapshots=snapshots,
    )
