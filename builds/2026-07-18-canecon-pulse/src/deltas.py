"""Period-over-period delta computation over an indicator's observation history."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Optional, Tuple

# (lookback in days, tolerance in days) — tolerance keeps a delta from being
# mislabeled: a monthly-frequency series (CPI, unemployment) has no genuine
# "day-over-day" comparison point, so that delta is simply omitted rather
# than silently substituting a much older value.
LOOKBACKS = {
    "day": (1, 2),
    "week": (7, 3),
    "month": (30, 10),
}


@dataclass(frozen=True)
class PeriodDelta:
    compare_date: date
    compare_value: float
    change: float
    pct_change: Optional[float]


@dataclass(frozen=True)
class DeltaSummary:
    latest_date: date
    latest_value: float
    day: Optional[PeriodDelta]
    week: Optional[PeriodDelta]
    month: Optional[PeriodDelta]


def compute_deltas(history: List[Tuple[date, float]]) -> Optional[DeltaSummary]:
    """Compute latest value plus day/week/month deltas from observation history.

    history: list of (date, value) pairs, any order, no duplicate dates assumed.
    Returns None if history is empty.
    """
    if not history:
        return None

    ordered = sorted(history, key=lambda pair: pair[0])
    latest_date, latest_value = ordered[-1]
    earlier = ordered[:-1]

    period_deltas = {}
    for label, (lookback_days, tolerance_days) in LOOKBACKS.items():
        target = latest_date - timedelta(days=lookback_days)
        match = _closest_on_or_before(earlier, target)
        period_deltas[label] = _build_delta(latest_value, target, tolerance_days, match)

    return DeltaSummary(
        latest_date=latest_date,
        latest_value=latest_value,
        day=period_deltas["day"],
        week=period_deltas["week"],
        month=period_deltas["month"],
    )


def _closest_on_or_before(
    history: List[Tuple[date, float]], target: date
) -> Optional[Tuple[date, float]]:
    candidates = [pair for pair in history if pair[0] <= target]
    if not candidates:
        return None
    return max(candidates, key=lambda pair: pair[0])


def _build_delta(
    latest_value: float,
    target: date,
    tolerance_days: int,
    match: Optional[Tuple[date, float]],
) -> Optional[PeriodDelta]:
    if match is None:
        return None
    match_date, match_value = match
    if abs((target - match_date).days) > tolerance_days:
        return None
    change = latest_value - match_value
    pct_change = (change / match_value * 100) if match_value != 0 else None
    return PeriodDelta(
        compare_date=match_date,
        compare_value=match_value,
        change=change,
        pct_change=pct_change,
    )
