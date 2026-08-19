"""Data models shared across Effort Ledger's audit pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


KNOWN_BUDGET_CATEGORIES = {
    "Personnel",
    "Fringe Benefits",
    "Equipment",
    "Travel",
    "Supplies",
    "Subcontract",
    "Other",
    "Indirect",
}


@dataclass
class BudgetLine:
    grant_id: str
    grant_name: str
    fiscal_year: str
    category: str
    description: str
    direct_cost: float
    row_number: int


@dataclass
class EffortLine:
    person_name: str
    grant_id: str
    grant_name: str
    period_start: date
    period_end: date
    percent_effort: float
    row_number: int


@dataclass
class Flag:
    severity: Severity
    code: str
    message: str
    grant_id: str = ""
    person_name: str = ""
    row_numbers: tuple = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "grant_id": self.grant_id,
            "person_name": self.person_name,
            "row_numbers": list(self.row_numbers),
        }


@dataclass
class GrantBudgetSummary:
    grant_id: str
    grant_name: str
    fiscal_year: str
    direct_total: float
    mtdc: float
    expected_indirect: float
    stated_indirect: float
    total: float

    def to_dict(self) -> dict:
        return {
            "grant_id": self.grant_id,
            "grant_name": self.grant_name,
            "fiscal_year": self.fiscal_year,
            "direct_total": round(self.direct_total, 2),
            "mtdc": round(self.mtdc, 2),
            "expected_indirect": round(self.expected_indirect, 2),
            "stated_indirect": round(self.stated_indirect, 2),
            "total": round(self.total, 2),
        }


@dataclass
class OvercommitmentWindow:
    person_name: str
    start: date
    end: date
    peak_percent: float
    grant_ids: tuple

    def to_dict(self) -> dict:
        return {
            "person_name": self.person_name,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "peak_percent": round(self.peak_percent, 2),
            "grant_ids": list(self.grant_ids),
        }


@dataclass
class AuditConfig:
    far_rate: float
    mtdc_exempt_categories: frozenset = field(default_factory=lambda: frozenset({"Equipment"}))
    subcontract_exempt_threshold: float = 25000.0
    effort_cap_percent: float = 100.0
    tolerance: float = 1.00
