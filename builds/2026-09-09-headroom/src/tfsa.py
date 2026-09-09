"""TFSA contribution room engine.

Implements the actual CRA rules, not an approximation:
- Room starts accumulating the later of 2009 or the year the holder turned 18
  (and, if given, the year they became a Canadian resident).
- Each year's full annual limit becomes available on January 1 of that year.
- A withdrawal is added back to contribution room, but only on January 1 of
  the *following* calendar year — never immediately.
- Contributing more than available room triggers a 1%-per-month tax (this
  module estimates that tax; it does not file anything).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .limits import (
    OVERCONTRIBUTION_MONTHLY_PENALTY_RATE,
    TFSA_ELIGIBILITY_AGE,
    TFSA_FIRST_YEAR,
    tfsa_limit,
)


@dataclass(frozen=True)
class Transaction:
    txn_date: date
    amount: float


@dataclass(frozen=True)
class TFSAYearSnapshot:
    year: int
    room_added: float
    withdrawals_readded: float
    contributions: float
    ending_balance: float


@dataclass(frozen=True)
class TFSAResult:
    start_year: int
    as_of: date
    available_room: float
    is_overcontributed: bool
    overcontribution_amount: float
    estimated_monthly_penalty: float
    year_snapshots: list[TFSAYearSnapshot] = field(default_factory=list)


def tfsa_start_year(birth_year: int, resident_since_year: int | None = None) -> int:
    """The first year TFSA room begins accumulating for this person."""
    turned_18_year = birth_year + TFSA_ELIGIBILITY_AGE
    start = max(TFSA_FIRST_YEAR, turned_18_year)
    if resident_since_year is not None:
        start = max(start, resident_since_year)
    return start


def compute_tfsa(
    birth_year: int,
    contributions: list[Transaction],
    withdrawals: list[Transaction],
    as_of: date,
    resident_since_year: int | None = None,
) -> TFSAResult:
    start_year = tfsa_start_year(birth_year, resident_since_year)

    if as_of.year < start_year:
        return TFSAResult(
            start_year=start_year,
            as_of=as_of,
            available_room=0.0,
            is_overcontributed=False,
            overcontribution_amount=0.0,
            estimated_monthly_penalty=0.0,
            year_snapshots=[],
        )

    past_contributions = [t for t in contributions if t.txn_date <= as_of]
    past_withdrawals = [t for t in withdrawals if t.txn_date <= as_of]

    contributions_by_year: dict[int, float] = {}
    for t in past_contributions:
        contributions_by_year[t.txn_date.year] = (
            contributions_by_year.get(t.txn_date.year, 0.0) + t.amount
        )

    withdrawals_by_year: dict[int, float] = {}
    for t in past_withdrawals:
        withdrawals_by_year[t.txn_date.year] = (
            withdrawals_by_year.get(t.txn_date.year, 0.0) + t.amount
        )

    balance = 0.0
    snapshots: list[TFSAYearSnapshot] = []
    for year in range(start_year, as_of.year + 1):
        room_added = tfsa_limit(year)
        withdrawals_readded = withdrawals_by_year.get(year - 1, 0.0)
        contributions_this_year = contributions_by_year.get(year, 0.0)
        balance += room_added + withdrawals_readded - contributions_this_year
        snapshots.append(
            TFSAYearSnapshot(
                year=year,
                room_added=room_added,
                withdrawals_readded=withdrawals_readded,
                contributions=contributions_this_year,
                ending_balance=balance,
            )
        )

    is_over = balance < 0
    overcontribution_amount = abs(balance) if is_over else 0.0
    monthly_penalty = (
        overcontribution_amount * OVERCONTRIBUTION_MONTHLY_PENALTY_RATE if is_over else 0.0
    )

    return TFSAResult(
        start_year=start_year,
        as_of=as_of,
        available_room=max(balance, 0.0) if not is_over else 0.0,
        is_overcontributed=is_over,
        overcontribution_amount=overcontribution_amount,
        estimated_monthly_penalty=monthly_penalty,
        year_snapshots=snapshots,
    )
