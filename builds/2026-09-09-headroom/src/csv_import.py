"""CSV import for contribution/withdrawal and income history files.

Column names are matched case-insensitively so an export from any bank,
brokerage, or spreadsheet works without the user renaming headers first —
the same auto-detection pattern this catalog's other CSV-ingesting builds
(Ledger Lens, TrialScope) use.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

CONTRIBUTION_COLUMNS = {"date", "amount"}
INCOME_COLUMNS = {"year", "earned_income"}


class CSVImportError(ValueError):
    pass


def _normalize_headers(fieldnames: list[str]) -> dict[str, str]:
    return {name.strip().lower(): name for name in fieldnames}


def import_contributions(path: Path) -> list[dict]:
    """Returns a list of {"date": date, "amount": float} rows."""
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise CSVImportError(f"{path} has no header row.")
        headers = _normalize_headers(reader.fieldnames)
        missing = CONTRIBUTION_COLUMNS - headers.keys()
        if missing:
            raise CSVImportError(
                f"{path} is missing required column(s): {', '.join(sorted(missing))}"
            )
        rows = []
        for i, raw_row in enumerate(reader, start=2):
            try:
                row_date = date.fromisoformat(raw_row[headers["date"]].strip())
                amount = float(raw_row[headers["amount"]])
            except (KeyError, ValueError) as exc:
                raise CSVImportError(f"{path} line {i}: {exc}") from exc
            rows.append({"date": row_date, "amount": amount})
        return rows


def import_income(path: Path) -> list[dict]:
    """Returns a list of {"year": int, "earned_income": float, "pension_adjustment": float}."""
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise CSVImportError(f"{path} has no header row.")
        headers = _normalize_headers(reader.fieldnames)
        missing = INCOME_COLUMNS - headers.keys()
        if missing:
            raise CSVImportError(
                f"{path} is missing required column(s): {', '.join(sorted(missing))}"
            )
        pension_key = headers.get("pension_adjustment")
        rows = []
        for i, raw_row in enumerate(reader, start=2):
            try:
                year = int(raw_row[headers["year"]])
                earned_income = float(raw_row[headers["earned_income"]])
                pension_adjustment = (
                    float(raw_row[pension_key]) if pension_key and raw_row[pension_key] else 0.0
                )
            except (KeyError, ValueError) as exc:
                raise CSVImportError(f"{path} line {i}: {exc}") from exc
            rows.append(
                {"year": year, "earned_income": earned_income, "pension_adjustment": pension_adjustment}
            )
        return rows
