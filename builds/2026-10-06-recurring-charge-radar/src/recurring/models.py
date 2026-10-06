from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Transaction:
    """A single outgoing payment. ``amount`` is positive money out."""

    date: date
    description: str
    amount: float
    source: str = ""


@dataclass
class PriceChange:
    date: date
    old: float
    new: float

    @property
    def delta(self) -> float:
        return round(self.new - self.old, 2)

    @property
    def percent(self) -> float:
        return round((self.new - self.old) / self.old * 100, 1) if self.old else 0.0


@dataclass
class Series:
    """A detected recurring charge."""

    merchant: str
    cadence: str
    period_days: int
    typical_amount: float
    variable: bool
    charges: list[Transaction]
    confidence: float
    status: str  # active | lapsed | zombie
    next_expected: date | None
    price_changes: list[PriceChange] = field(default_factory=list)
    cancelled_on: date | None = None

    @property
    def last_amount(self) -> float:
        return self.charges[-1].amount

    @property
    def last_date(self) -> date:
        return self.charges[-1].date

    @property
    def annual_cost(self) -> float:
        return round(self.typical_amount * 365 / self.period_days, 2)

    @property
    def monthly_cost(self) -> float:
        return round(self.annual_cost / 12, 2)
