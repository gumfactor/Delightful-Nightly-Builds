"""Parse a real Garmin Connect "Activities" CSV export and match rows
against configured habits.

Garmin's export includes many columns (pace, HR, cadence, etc.) that this
tool doesn't need — only ``Activity Type``, ``Date``, and ``Title`` are
read. The date column is exported as a local timestamp string; Garmin has
used a couple of different formats over the years, so a short list of
known patterns is tried before a row is treated as unparseable.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from src.db import StreakDB

_DATE_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%b %d, %Y, %I:%M %p",
    "%Y-%m-%d",
)


@dataclass(frozen=True)
class ActivityRow:
    activity_date: date
    activity_type: str
    title: str


@dataclass
class ImportSummary:
    total_rows: int = 0
    matched_rows: int = 0
    inserted: int = 0
    already_recorded: int = 0
    skipped_rows: list[str] = None
    unmatched_types: set[str] = None

    def __post_init__(self) -> None:
        if self.skipped_rows is None:
            self.skipped_rows = []
        if self.unmatched_types is None:
            self.unmatched_types = set()


def _parse_date(raw: str) -> date | None:
    raw = raw.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def parse_garmin_csv(path: Path) -> tuple[list[ActivityRow], list[str]]:
    """Read a Garmin Activities export. Returns (rows, warnings) — a
    malformed row is skipped and recorded in ``warnings`` rather than
    raising, since a real export can contain the occasional in-progress or
    corrupted row.
    """
    rows: list[ActivityRow] = []
    warnings: list[str] = []

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return rows, ["CSV has no header row"]

        fieldnames = {name.strip().lower(): name for name in reader.fieldnames}
        type_col = fieldnames.get("activity type")
        date_col = fieldnames.get("date")
        title_col = fieldnames.get("title")

        if type_col is None or date_col is None:
            warnings.append(
                "CSV is missing a required 'Activity Type' or 'Date' column"
            )
            return rows, warnings

        for line_num, row in enumerate(reader, start=2):
            activity_type = (row.get(type_col) or "").strip()
            raw_date = (row.get(date_col) or "").strip()
            title = (row.get(title_col) or "").strip() if title_col else ""

            if not activity_type or not raw_date:
                warnings.append(f"line {line_num}: missing activity type or date, skipped")
                continue

            parsed = _parse_date(raw_date)
            if parsed is None:
                warnings.append(f"line {line_num}: unparseable date '{raw_date}', skipped")
                continue

            rows.append(ActivityRow(activity_date=parsed, activity_type=activity_type, title=title))

    return rows, warnings


def list_activity_types(rows: list[ActivityRow]) -> list[str]:
    return sorted({r.activity_type for r in rows})


def _matches(activity_type: str, garmin_types: list[str]) -> bool:
    normalized = activity_type.strip().lower()
    return normalized in {t.strip().lower() for t in garmin_types}


def import_activities(rows: list[ActivityRow], habits: list[dict], db: StreakDB) -> ImportSummary:
    """Match parsed rows against Garmin-sourced habits and write completions.

    Multiple matching activities on the same day for the same habit
    collapse into a single completion (the DB's UNIQUE constraint plus
    ``add_completion``'s "already recorded" semantics handle that for
    free — no special-casing needed here).
    """
    summary = ImportSummary(total_rows=len(rows))
    garmin_habits = [h for h in habits if h.get("source") == "garmin"]

    for row in rows:
        matched_habit = None
        for habit in garmin_habits:
            if _matches(row.activity_type, habit.get("garmin_activity_types", [])):
                matched_habit = habit
                break

        if matched_habit is None:
            summary.unmatched_types.add(row.activity_type)
            continue

        summary.matched_rows += 1
        inserted = db.add_completion(
            habit_id=matched_habit["id"],
            completion_date=row.activity_date,
            source="garmin",
            detail=row.title or row.activity_type,
        )
        if inserted:
            summary.inserted += 1
        else:
            summary.already_recorded += 1

    return summary
