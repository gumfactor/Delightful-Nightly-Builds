"""CSV loaders for Effort Ledger. Malformed rows become Flags, never exceptions."""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

from src.models import BudgetLine, EffortLine, Flag, Severity

BUDGET_COLUMNS = [
    "grant_id",
    "grant_name",
    "fiscal_year",
    "category",
    "description",
    "direct_cost",
]

EFFORT_COLUMNS = [
    "person_name",
    "grant_id",
    "grant_name",
    "period_start",
    "period_end",
    "percent_effort",
]


def _missing_columns(fieldnames: list | None, required: list[str]) -> list[str]:
    present = set(fieldnames or [])
    return [c for c in required if c not in present]


def _parse_date(value: str) -> date:
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def load_budget_csv(path: str | Path) -> tuple[list[BudgetLine], list[Flag]]:
    lines: list[BudgetLine] = []
    flags: list[Flag] = []

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = _missing_columns(reader.fieldnames, BUDGET_COLUMNS)
        if missing:
            flags.append(
                Flag(
                    Severity.ERROR,
                    "missing_columns",
                    f"budget.csv is missing required column(s): {', '.join(missing)}",
                )
            )
            return lines, flags

        for row_number, row in enumerate(reader, start=2):
            try:
                direct_cost = float(row["direct_cost"])
            except (TypeError, ValueError):
                flags.append(
                    Flag(
                        Severity.ERROR,
                        "malformed_direct_cost",
                        f"Row {row_number}: direct_cost '{row.get('direct_cost')}' is not a number — row skipped",
                        grant_id=row.get("grant_id", ""),
                        row_numbers=(row_number,),
                    )
                )
                continue

            grant_id = (row.get("grant_id") or "").strip()
            if not grant_id:
                flags.append(
                    Flag(
                        Severity.ERROR,
                        "missing_grant_id",
                        f"Row {row_number}: grant_id is empty — row skipped",
                        row_numbers=(row_number,),
                    )
                )
                continue

            lines.append(
                BudgetLine(
                    grant_id=grant_id,
                    grant_name=(row.get("grant_name") or "").strip(),
                    fiscal_year=(row.get("fiscal_year") or "").strip(),
                    category=(row.get("category") or "").strip(),
                    description=(row.get("description") or "").strip(),
                    direct_cost=direct_cost,
                    row_number=row_number,
                )
            )

    return lines, flags


def load_effort_csv(path: str | Path) -> tuple[list[EffortLine], list[Flag]]:
    lines: list[EffortLine] = []
    flags: list[Flag] = []

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = _missing_columns(reader.fieldnames, EFFORT_COLUMNS)
        if missing:
            flags.append(
                Flag(
                    Severity.ERROR,
                    "missing_columns",
                    f"effort.csv is missing required column(s): {', '.join(missing)}",
                )
            )
            return lines, flags

        for row_number, row in enumerate(reader, start=2):
            grant_id = (row.get("grant_id") or "").strip()
            person_name = (row.get("person_name") or "").strip()

            if not grant_id or not person_name:
                flags.append(
                    Flag(
                        Severity.ERROR,
                        "missing_required_field",
                        f"Row {row_number}: person_name and grant_id are both required — row skipped",
                        row_numbers=(row_number,),
                    )
                )
                continue

            try:
                percent_effort = float(row["percent_effort"])
            except (TypeError, ValueError):
                flags.append(
                    Flag(
                        Severity.ERROR,
                        "malformed_percent_effort",
                        f"Row {row_number}: percent_effort '{row.get('percent_effort')}' is not a number — row skipped",
                        grant_id=grant_id,
                        person_name=person_name,
                        row_numbers=(row_number,),
                    )
                )
                continue

            try:
                start = _parse_date(row["period_start"])
                end = _parse_date(row["period_end"])
            except (TypeError, ValueError, KeyError):
                flags.append(
                    Flag(
                        Severity.ERROR,
                        "malformed_date",
                        f"Row {row_number}: period_start/period_end must be YYYY-MM-DD — row skipped",
                        grant_id=grant_id,
                        person_name=person_name,
                        row_numbers=(row_number,),
                    )
                )
                continue

            lines.append(
                EffortLine(
                    person_name=person_name,
                    grant_id=grant_id,
                    grant_name=(row.get("grant_name") or "").strip(),
                    period_start=start,
                    period_end=end,
                    percent_effort=percent_effort,
                    row_number=row_number,
                )
            )

    return lines, flags
