"""CSV ingestion and column auto-detection for bank/credit-card transaction exports."""

from __future__ import annotations

import csv
import datetime
from dataclasses import dataclass, field


class ParseError(Exception):
    """Raised when the input CSV cannot be interpreted as a transaction export."""


@dataclass
class Transaction:
    date: datetime.date
    description: str
    amount: float
    category: str = "Other"
    category_source: str = "rule"
    recurring: bool = False


@dataclass
class ParseResult:
    transactions: list = field(default_factory=list)
    skipped_rows: int = 0
    total_rows: int = 0


DATE_COLUMN_NAMES = [
    "date", "transaction date", "posting date", "trans date", "post date",
]
DESCRIPTION_COLUMN_NAMES = [
    "description", "details", "memo", "merchant", "narrative", "payee", "transaction",
]
AMOUNT_COLUMN_NAMES = ["amount", "value", "transaction amount"]
DEBIT_COLUMN_NAMES = ["debit", "withdrawal", "amount debit"]
CREDIT_COLUMN_NAMES = ["credit", "deposit", "amount credit"]
EXISTING_CATEGORY_COLUMN_NAMES = ["category", "type"]

DATE_FORMATS = [
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%m/%d/%y",
    "%d-%b-%Y",
    "%d-%b-%y",
    "%B %d, %Y",
    "%b %d, %Y",
]


def _find_column(headers: list, candidates: list) -> str | None:
    lowered = {h.strip().lower(): h for h in headers}
    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]
    return None


def _parse_date(raw: str) -> datetime.date | None:
    raw = raw.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _parse_amount(raw: str) -> float | None:
    cleaned = raw.strip().replace(",", "").replace("$", "")
    if not cleaned:
        return None
    negative = False
    if cleaned.startswith("(") and cleaned.endswith(")"):
        negative = True
        cleaned = cleaned[1:-1]
    try:
        value = float(cleaned)
    except ValueError:
        return None
    return -value if negative else value


def detect_columns(headers: list) -> dict:
    """Detect which headers map to date/description/amount (or debit+credit)."""
    date_col = _find_column(headers, DATE_COLUMN_NAMES)
    desc_col = _find_column(headers, DESCRIPTION_COLUMN_NAMES)
    amount_col = _find_column(headers, AMOUNT_COLUMN_NAMES)
    debit_col = _find_column(headers, DEBIT_COLUMN_NAMES)
    credit_col = _find_column(headers, CREDIT_COLUMN_NAMES)
    category_col = _find_column(headers, EXISTING_CATEGORY_COLUMN_NAMES)

    missing = []
    if date_col is None:
        missing.append("date")
    if desc_col is None:
        missing.append("description")
    if amount_col is None and (debit_col is None or credit_col is None):
        missing.append("amount (or debit+credit)")

    if missing:
        raise ParseError(
            f"Could not identify required column(s): {', '.join(missing)}. "
            f"Found headers: {headers}"
        )

    return {
        "date": date_col,
        "description": desc_col,
        "amount": amount_col,
        "debit": debit_col,
        "credit": credit_col,
        "category": category_col,
    }


def parse_csv(path: str, invert_sign: bool = False) -> ParseResult:
    """Parse a transaction CSV into a list of Transaction records.

    Convention: negative amount = expense, positive = income, unless invert_sign
    is set (for exports where charges are recorded as positive values).
    """
    try:
        with open(path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            headers = reader.fieldnames
            if not headers:
                raise ParseError(f"'{path}' has no header row or is empty.")
            columns = detect_columns(headers)

            result = ParseResult()
            for row in reader:
                result.total_rows += 1
                txn = _row_to_transaction(row, columns, invert_sign)
                if txn is None:
                    result.skipped_rows += 1
                    continue
                result.transactions.append(txn)
    except FileNotFoundError:
        raise ParseError(f"Input file not found: '{path}'")

    return result


def _row_to_transaction(row: dict, columns: dict, invert_sign: bool) -> Transaction | None:
    raw_date = row.get(columns["date"], "")
    raw_desc = row.get(columns["description"], "")
    date = _parse_date(raw_date) if raw_date else None
    description = raw_desc.strip() if raw_desc else ""

    if columns["amount"]:
        amount = _parse_amount(row.get(columns["amount"], ""))
    else:
        debit = _parse_amount(row.get(columns["debit"], "")) or 0.0
        credit = _parse_amount(row.get(columns["credit"], "")) or 0.0
        amount = credit - abs(debit)

    if date is None or not description or amount is None:
        return None

    if invert_sign:
        amount = -amount

    existing_category = None
    if columns["category"]:
        existing_category = row.get(columns["category"], "").strip() or None

    if existing_category:
        return Transaction(
            date=date, description=description, amount=amount,
            category=existing_category, category_source="existing",
        )
    return Transaction(date=date, description=description, amount=amount)
