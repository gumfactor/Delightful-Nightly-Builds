"""Business CSV ingestion, verdict filtering, and selection helpers."""

from __future__ import annotations

import csv

REQUIRED_COLUMNS = {"name", "category"}
KNOWN_TEXT_COLUMNS = ["name", "category", "description", "city", "province", "website"]


def load_businesses(path: str) -> tuple[list[dict], bool]:
    """Load and validate a business CSV.

    Returns (businesses, has_verdict_column). Raises ValueError on a missing
    required column, a blank required field, or an empty file.
    """
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"CSV file '{path}' is empty or has no header row.")

        fieldnames = set(reader.fieldnames)
        missing = REQUIRED_COLUMNS - fieldnames
        if missing:
            raise ValueError(
                f"CSV is missing required column(s): {', '.join(sorted(missing))}. "
                f"Required columns are: {', '.join(sorted(REQUIRED_COLUMNS))}."
            )

        has_verdict_column = "verdict" in fieldnames

        businesses = []
        for line_number, row in enumerate(reader, start=2):
            name = (row.get("name") or "").strip()
            category = (row.get("category") or "").strip()
            if not name or not category:
                raise ValueError(
                    f"Row {line_number}: 'name' and 'category' are required and "
                    "cannot be blank."
                )

            business = {
                "name": name,
                "category": category,
                "description": (row.get("description") or "").strip(),
                "city": (row.get("city") or "").strip(),
                "province": (row.get("province") or "").strip(),
                "website": (row.get("website") or "").strip(),
            }

            if has_verdict_column:
                verdict = (row.get("verdict") or "").strip().lower()
                business["verdict"] = verdict if verdict else "uncertain"
                confidence_raw = row.get("confidence")
                try:
                    business["confidence"] = (
                        float(confidence_raw)
                        if confidence_raw not in (None, "")
                        else None
                    )
                except ValueError:
                    business["confidence"] = None
                business["evidence"] = (row.get("evidence") or "").strip()

            businesses.append(business)

    if not businesses:
        raise ValueError(f"CSV '{path}' contains no business rows.")

    return businesses, has_verdict_column


def filter_by_verdict(
    businesses: list[dict], has_verdict_column: bool, include_unverified: bool
) -> list[dict]:
    """Filter businesses by Canadian-ownership verdict.

    When the CSV has no verdict column at all, every business is included but
    tagged unverified — downstream copy carries a disclaimer for each one.
    When the CSV has a verdict column, only verdict == 'canadian' is kept
    unless include_unverified is set, in which case everything is kept but
    each business is tagged verified/unverified individually.
    """
    result = []
    for original in businesses:
        business = dict(original)
        if has_verdict_column:
            business["verified"] = business.get("verdict") == "canadian"
            if not include_unverified and not business["verified"]:
                continue
        else:
            business["verified"] = False
        result.append(business)
    return result


def select_for_spotlight(businesses: list[dict], business_name: str) -> list[dict]:
    matches = [b for b in businesses if b["name"].lower() == business_name.strip().lower()]
    if not matches:
        raise ValueError(
            f"No business named '{business_name}' found in the filtered set "
            "(check spelling, or try --include-unverified if it may lack a "
            "canadian verdict)."
        )
    return matches[:1]


def select_by_category(businesses: list[dict], category: str) -> list[dict]:
    return [b for b in businesses if b["category"].strip().lower() == category.strip().lower()]


def select_by_province(businesses: list[dict], province: str) -> list[dict]:
    return [b for b in businesses if b["province"].strip().lower() == province.strip().lower()]
