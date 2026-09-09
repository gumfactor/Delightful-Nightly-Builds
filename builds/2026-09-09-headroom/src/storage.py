"""Load and save the local Headroom data file.

The data file holds only the user's own birth year and transaction/income
history — plain numbers and dates, no names, addresses, or account
numbers. It lives wherever the caller points it (default `data/headroom.json`
next to this build) and is never sent anywhere.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from . import rrsp, tfsa


class StorageError(ValueError):
    pass


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def default_profile() -> dict:
    return {
        "profile": {"birth_year": None, "resident_since_year": None},
        "tfsa_contributions": [],
        "tfsa_withdrawals": [],
        "rrsp_contributions": [],
        "rrsp_income": [],
        "rrsp_opening_balance": None,
    }


def load(path: Path) -> dict:
    if not path.exists():
        raise StorageError(f"No data file at {path}. Run `init` first.")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise StorageError(f"Data file at {path} is not valid JSON: {exc}") from exc
    if "profile" not in data or data["profile"].get("birth_year") is None:
        raise StorageError("Data file is missing a profile birth_year.")
    return data


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True))


def tfsa_transactions(data: dict) -> tuple[list[tfsa.Transaction], list[tfsa.Transaction]]:
    contributions = [
        tfsa.Transaction(_parse_date(t["date"]), float(t["amount"]))
        for t in data.get("tfsa_contributions", [])
    ]
    withdrawals = [
        tfsa.Transaction(_parse_date(t["date"]), float(t["amount"]))
        for t in data.get("tfsa_withdrawals", [])
    ]
    return contributions, withdrawals


def rrsp_records(
    data: dict,
) -> tuple[list[rrsp.Contribution], list[rrsp.IncomeRecord], rrsp.OpeningBalance | None]:
    contributions = [
        rrsp.Contribution(_parse_date(c["date"]), float(c["amount"]), int(c["tax_year"]))
        for c in data.get("rrsp_contributions", [])
    ]
    income = [
        rrsp.IncomeRecord(
            int(r["year"]), float(r["earned_income"]), float(r.get("pension_adjustment", 0.0))
        )
        for r in data.get("rrsp_income", [])
    ]
    opening = data.get("rrsp_opening_balance")
    opening_balance = (
        rrsp.OpeningBalance(int(opening["year"]), float(opening["amount"]))
        if opening
        else None
    )
    return contributions, income, opening_balance
