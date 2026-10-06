"""Recurring-charge detection: cadence, amount levels, price changes, lifecycle."""
from __future__ import annotations

import calendar
import statistics
from collections import defaultdict
from datetime import date, timedelta

from .models import PriceChange, Series, Transaction
from .normalize import display_name, merchant_key
from .rules import Rules

# name -> (nominal days, tolerance days)
CADENCES: dict[str, tuple[int, int]] = {
    "weekly": (7, 2),
    "biweekly": (14, 3),
    "monthly": (30, 4),
    "quarterly": (91, 9),
    "annual": (365, 14),
}
PRICE_CHANGE_PCT = 4.0
PRICE_CHANGE_ABS = 0.50
MIN_CONFIDENCE = 0.5
PARALLEL_OVERLAP_DAYS = 45


def add_months(start: date, months: int) -> date:
    index = start.month - 1 + months
    year, month = start.year + index // 12, index % 12 + 1
    return date(year, month, min(start.day, calendar.monthrange(year, month)[1]))


def advance(start: date, cadence: str, steps: int = 1) -> date:
    if cadence == "monthly":
        return add_months(start, steps)
    if cadence == "quarterly":
        return add_months(start, 3 * steps)
    if cadence == "annual":
        return add_months(start, 12 * steps)
    return start + timedelta(days=CADENCES[cadence][0] * steps)


def classify_cadence(gaps: list[int]) -> tuple[str, float] | None:
    """Return (cadence, fraction of gaps that fit it) or None."""
    if not gaps:
        return None
    median = statistics.median(gaps)
    for name, (nominal, tolerance) in CADENCES.items():
        if abs(median - nominal) <= tolerance:
            fits = sum(1 for gap in gaps if abs(gap - nominal) <= tolerance)
            # A skipped period (gap ~ 2x) is a miss, but not a disqualifier.
            return name, fits / len(gaps)
    return None


def _relative_diff(a: float, b: float) -> float:
    return abs(a - b) / b * 100 if b else 0.0


def _is_change(new: float, level: float) -> bool:
    return _relative_diff(new, level) >= PRICE_CHANGE_PCT and abs(new - level) >= PRICE_CHANGE_ABS


def segment_levels(charges: list[Transaction]) -> tuple[list[PriceChange], int]:
    """Walk amounts and return confirmed price changes plus the count of unconfirmed jumps.

    A new level is confirmed when the next charge agrees with it, or when it is the
    most recent charge (so a fresh price hike is flagged immediately).
    """
    amounts = [txn.amount for txn in charges]
    changes: list[PriceChange] = []
    noisy = 0
    level = amounts[0]
    run = [amounts[0]]
    i = 1
    while i < len(amounts):
        amount = amounts[i]
        if not _is_change(amount, level):
            run.append(amount)
            level = statistics.median(run)
            i += 1
            continue
        is_last = i == len(amounts) - 1
        confirmed = is_last or not _is_change(amounts[i + 1], amount)
        if confirmed:
            changes.append(PriceChange(charges[i].date, round(level, 2), round(amount, 2)))
            level, run = amount, [amount]
        else:
            noisy += 1  # one-off spike: keep the baseline level untouched
        i += 1
    return changes, noisy


def _collapse_same_day(charges: list[Transaction]) -> list[Transaction]:
    seen: set[tuple[date, float]] = set()
    out = []
    for txn in charges:
        key = (txn.date, txn.amount)
        if key not in seen:
            seen.add(key)
            out.append(txn)
    return out


def analyse_series(
    name: str, raw_charges: list[Transaction], as_of: date, rules: Rules
) -> Series | None:
    charges = sorted(_collapse_same_day(raw_charges), key=lambda t: t.date)
    if len(charges) < 2:
        return None
    gaps = [(b.date - a.date).days for a, b in zip(charges, charges[1:])]
    found = classify_cadence(gaps)
    if found is None:
        return None
    cadence, fit = found
    count = len(charges)
    if cadence != "annual" and count < 3:
        return None
    if cadence == "annual" and fit < 1.0:
        return None
    if fit < 0.7:
        return None

    amounts = [txn.amount for txn in charges]
    median_amount = statistics.median(amounts)
    changes, noisy = segment_levels(charges)
    variable = noisy >= max(1, count // 4) or len(changes) > max(1, count // 3)
    if variable:
        changes = []
        if not all(0.4 * median_amount <= a <= 2.5 * median_amount for a in amounts):
            return None
        if cadence in ("weekly", "biweekly"):
            return None  # groceries, coffee runs: variable and frequent is spending, not a subscription
    typical = round(median_amount if variable else amounts[-1], 2)

    confidence = fit * (0.6 + 0.4 * min(1.0, count / 6))
    if variable:
        confidence *= 0.85
    confidence = round(confidence, 2)
    if confidence < MIN_CONFIDENCE:
        return None

    period_days = CADENCES[cadence][0]
    last = charges[-1].date
    cancelled_on = rules.cancelled_on(name)
    if cancelled_on is not None:
        post_cancel = [t for t in charges if t.date > cancelled_on + timedelta(days=3)]
        status = "zombie" if post_cancel else "cancelled"
    else:
        silent_days = (as_of - last).days
        status = "lapsed" if silent_days > period_days * 1.6 + 7 else "active"

    next_expected: date | None = None
    if status == "active":
        steps = 1
        next_expected = advance(last, cadence, steps)
        while next_expected < as_of:
            steps += 1
            next_expected = advance(last, cadence, steps)
    elif status == "zombie":
        next_expected = advance(last, cadence)
        while next_expected < as_of:
            next_expected = advance(next_expected, cadence)

    return Series(
        merchant=name,
        cadence=cadence,
        period_days=period_days,
        typical_amount=typical,
        variable=variable,
        charges=charges,
        confidence=confidence,
        status=status,
        next_expected=next_expected,
        price_changes=changes,
        cancelled_on=cancelled_on,
    )


def _amount_clusters(charges: list[Transaction]) -> list[list[Transaction]]:
    clusters: list[list[Transaction]] = []
    for txn in sorted(charges, key=lambda t: t.amount):
        if clusters and not _is_change(txn.amount, statistics.median(c.amount for c in clusters[-1])):
            clusters[-1].append(txn)
        else:
            clusters.append([txn])
    return clusters


def _overlap_days(a: list[Transaction], b: list[Transaction]) -> int:
    start = max(min(t.date for t in a), min(t.date for t in b))
    end = min(max(t.date for t in a), max(t.date for t in b))
    return (end - start).days


def _parallel_clusters(clusters: list[list[Transaction]]) -> list[list[Transaction]] | None:
    """Clusters that coexist in time are separate subscriptions from one merchant."""
    solid = [c for c in clusters if len(c) >= 3]
    if len(solid) < 2:
        return None
    for i, first in enumerate(solid):
        for second in solid[i + 1:]:
            if _overlap_days(first, second) >= PARALLEL_OVERLAP_DAYS:
                return solid
    return None


def detect(
    transactions: list[Transaction], rules: Rules | None = None, as_of: date | None = None
) -> list[Series]:
    """Find all recurring series. ``as_of`` defaults to the newest transaction date."""
    rules = rules or Rules()
    if not transactions:
        return []
    as_of = as_of or max(t.date for t in transactions)

    groups: dict[str, list[Transaction]] = defaultdict(list)
    names: dict[str, str] = {}
    for txn in transactions:
        if rules.is_ignored(txn.description):
            continue
        alias = rules.alias_for(txn.description)
        key = alias.lower() if alias else merchant_key(txn.description)
        if not key:
            continue
        groups[key].append(txn)
        names.setdefault(key, alias or display_name(txn.description))

    series: list[Series] = []
    for key, charges in groups.items():
        name = names[key]
        parallel = _parallel_clusters(_amount_clusters(charges))
        if parallel:
            for cluster in parallel:
                label = f"{name} (${statistics.median(c.amount for c in cluster):.2f})"
                found = analyse_series(label, cluster, as_of, rules)
                if found:
                    series.append(found)
            continue
        found = analyse_series(name, charges, as_of, rules)
        if found:
            series.append(found)

    series.sort(key=lambda s: s.annual_cost, reverse=True)
    return series
