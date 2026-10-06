"""Parse bank / credit-card CSV exports into Transactions.

Handles RBC, TD, CIBC, Scotiabank, BMO and generic header-based files. Files may
have a preamble, no header row, split debit/credit columns or one signed column.
"""
from __future__ import annotations

import csv
import io
import re
from datetime import date, datetime
from pathlib import Path

from .models import Transaction

DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%Y%m%d", "%b %d, %Y", "%d %b %Y", "%m/%d/%y")

_DATE_HEADERS = ("transaction date", "posting date", "posted date", "date", "trans date", "booking date")
_DESC_HEADERS = ("description 1", "description", "merchant", "details", "payee", "memo", "transaction details", "name")
_DEBIT_HEADERS = ("debit", "withdrawals", "withdrawal", "debits", "money out", "funds out")
_CREDIT_HEADERS = ("credit", "deposits", "deposit", "credits", "money in", "funds in")
_AMOUNT_HEADERS = ("amount", "cad$", "cad", "transaction amount", "amount (cad)")


class ParseError(ValueError):
    """Raised when a file cannot be understood as a transaction export."""


def parse_date(text: str) -> date | None:
    value = text.strip().strip('"')
    if not value:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_amount(text: str) -> float | None:
    value = text.strip().replace("$", "").replace(",", "").replace(" ", "")
    if not value:
        return None
    negative = value.startswith("(") and value.endswith(")")
    value = value.strip("()")
    if value.endswith("-"):
        negative, value = True, value[:-1]
    if value.endswith("CR"):
        negative, value = True, value[:-2]
    if value.endswith("DR"):
        value = value[:-2]
    try:
        number = float(value)
    except ValueError:
        return None
    return -abs(number) if negative else number


def _norm(header: str) -> str:
    return re.sub(r"\s+", " ", header.strip().lower())


def _find(headers: list[str], candidates: tuple[str, ...]) -> int | None:
    for candidate in candidates:
        if candidate in headers:
            return headers.index(candidate)
    return None


def _header_row_index(rows: list[list[str]]) -> int | None:
    for index, row in enumerate(rows[:30]):
        normed = [_norm(cell) for cell in row]
        if _find(normed, _DATE_HEADERS) is not None and (
            _find(normed, _DESC_HEADERS) is not None
        ) and (
            _find(normed, _AMOUNT_HEADERS) is not None
            or _find(normed, _DEBIT_HEADERS) is not None
        ):
            return index
    return None


def _cell(row: list[str], index: int | None) -> str:
    return row[index] if index is not None and index < len(row) else ""


def _parse_with_header(rows: list[list[str]], header_index: int, source: str) -> list[Transaction]:
    headers = [_norm(cell) for cell in rows[header_index]]
    date_col = _find(headers, _DATE_HEADERS)
    desc_col = _find(headers, _DESC_HEADERS)
    desc2_col = headers.index("description 2") if "description 2" in headers else None
    debit_col = _find(headers, _DEBIT_HEADERS)
    credit_col = _find(headers, _CREDIT_HEADERS)
    amount_col = _find(headers, _AMOUNT_HEADERS)
    out: list[Transaction] = []
    for row in rows[header_index + 1:]:
        when = parse_date(_cell(row, date_col))
        if when is None:
            continue
        description = " ".join(f"{_cell(row, desc_col)} {_cell(row, desc2_col)}".split())
        if not description:
            continue
        if debit_col is not None:
            debit = parse_amount(_cell(row, debit_col))
            credit = parse_amount(_cell(row, credit_col))
            if debit:
                amount = abs(debit)
            elif credit and amount_col is None:
                continue
            else:
                amount = None
            if amount is None and amount_col is not None:
                signed = parse_amount(_cell(row, amount_col))
                amount = -signed if signed is not None and signed < 0 else None
        else:
            signed = parse_amount(_cell(row, amount_col))
            # Signed export: negatives are purchases (RBC, Scotiabank, BMO, TD Visa).
            amount = -signed if signed is not None and signed < 0 else None
        if amount:
            out.append(Transaction(when, description, round(amount, 2), source))
    return out


def _parse_headerless(rows: list[list[str]], source: str) -> list[Transaction]:
    """TD / CIBC style: date, description, debit, credit[, balance|card]."""
    out: list[Transaction] = []
    for row in rows:
        if len(row) < 3:
            continue
        when = parse_date(row[0])
        if when is None:
            continue
        description = row[1].strip()
        debit = parse_amount(row[2]) if len(row) > 2 else None
        if not description or not debit or debit <= 0:
            continue
        out.append(Transaction(when, description, round(debit, 2), source))
    return out


def parse_text(text: str, source: str = "") -> list[Transaction]:
    text = text.lstrip("﻿")
    if not text.strip():
        raise ParseError(f"{source or 'input'}: file is empty")
    dialect = csv.excel
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        pass
    rows = [row for row in csv.reader(io.StringIO(text), dialect) if any(cell.strip() for cell in row)]
    header_index = _header_row_index(rows)
    if header_index is not None:
        transactions = _parse_with_header(rows, header_index, source)
    else:
        transactions = _parse_headerless(rows, source)
    if not transactions:
        raise ParseError(
            f"{source or 'input'}: no purchases found. Expected columns like Date, Description, "
            "Amount (or Debit/Credit), or a header-less date,description,debit,credit layout."
        )
    return transactions


def parse_file(path: str | Path) -> list[Transaction]:
    file_path = Path(path)
    try:
        raw = file_path.read_bytes()
    except OSError as exc:
        raise ParseError(f"{path}: cannot read file ({exc.strerror})") from exc
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    return parse_text(text, source=file_path.name)


def dedupe(transactions: list[Transaction]) -> list[Transaction]:
    """Drop duplicates that appear because exports from different files overlap.

    Identical same-day, same-amount charges inside one file are legitimate, so a
    transaction is kept only from the first file that contained it.
    """
    first_owner: dict[tuple, str] = {}
    out: list[Transaction] = []
    for txn in transactions:
        key = (txn.date, txn.description, txn.amount)
        owner = first_owner.setdefault(key, txn.source)
        if owner == txn.source:
            out.append(txn)
    return out
