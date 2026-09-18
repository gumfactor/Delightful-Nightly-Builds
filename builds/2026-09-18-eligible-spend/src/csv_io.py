"""CSV parsing and validation for Eligible Spend budget input."""

from __future__ import annotations

import csv
import io
from datetime import date, datetime

from rules import LineItem

REQUIRED_COLUMNS = ("item", "category", "amount", "date")
OPTIONAL_COLUMNS = ("justification",)


class BudgetCsvError(ValueError):
    """Raised when the input CSV is missing columns or contains bad data."""


def _parse_date(raw: str, row_num: int) -> date:
    raw = raw.strip()
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError as exc:
        raise BudgetCsvError(
            f"Row {row_num}: invalid date {raw!r} -- expected YYYY-MM-DD"
        ) from exc


def _parse_amount(raw: str, row_num: int) -> float:
    raw = raw.strip().replace("$", "").replace(",", "")
    try:
        amount = float(raw)
    except ValueError as exc:
        raise BudgetCsvError(f"Row {row_num}: invalid amount {raw!r}") from exc
    if amount < 0:
        raise BudgetCsvError(f"Row {row_num}: amount cannot be negative ({amount})")
    return amount


def parse_budget_csv(text: str) -> list[LineItem]:
    """Parse budget CSV text into a list of LineItem.

    Raises BudgetCsvError on a missing required column or malformed rows.
    """
    text = text.lstrip("﻿")  # strip BOM if present
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise BudgetCsvError("CSV file is empty -- no header row found")

    fieldnames = {name.strip().lower() for name in reader.fieldnames}
    missing = [col for col in REQUIRED_COLUMNS if col not in fieldnames]
    if missing:
        raise BudgetCsvError(f"CSV is missing required column(s): {', '.join(missing)}")

    lines: list[LineItem] = []
    row_num = 1  # header is row 0
    for row in reader:
        row_num += 1
        normalized = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
        item = normalized.get("item", "")
        category = normalized.get("category", "")
        if not item:
            raise BudgetCsvError(f"Row {row_num}: 'item' cannot be empty")
        amount = _parse_amount(normalized.get("amount", ""), row_num)
        item_date = _parse_date(normalized.get("date", ""), row_num)
        justification = normalized.get("justification", "")
        lines.append(
            LineItem(
                item=item,
                category=category,
                amount=amount,
                item_date=item_date,
                justification=justification,
            )
        )

    if not lines:
        raise BudgetCsvError("CSV has a header row but no data rows")

    return lines


def load_budget_csv(path: str) -> list[LineItem]:
    with open(path, "r", encoding="utf-8") as f:
        return parse_budget_csv(f.read())
