"""Parse a Garmin Connect 'Activities' CSV export and compute a 7-day activity load.

Garmin Connect's web export ("Export CSV" on the Activities list) uses columns
including at minimum: Date, Activity Type, Distance, Calories, Time.
This parser is tolerant of the exact column set Garmin ships (extra columns are
ignored) but requires Date and Calories to compute a load; anything else missing
degrades gracefully rather than crashing.
"""
from __future__ import annotations

import csv
import datetime as dt
from dataclasses import dataclass

REQUIRED_COLUMNS = {"Date", "Calories"}
OPTIONAL_NUMERIC_COLUMNS = {"Distance", "Time"}

# Cap on how much extra daily calorie budget the activity adjustment can add,
# regardless of how much training load a given week shows. Keeps a single
# unusually large logged activity from producing an unrealistic target.
MAX_DAILY_ADJUSTMENT_KCAL = 900.0

WINDOW_DAYS = 7


class GarminImportWarning(Warning):
    """Raised (as a return-value warning, not thrown) for a degraded-but-handled import."""


@dataclass
class GarminSummary:
    window_start: str
    window_end: str
    total_distance_km: float
    total_duration_min: float
    total_calories: float
    activity_count: int
    daily_adjustment_kcal: float
    warnings: list


def _parse_float(value: str) -> float:
    if value is None:
        return 0.0
    cleaned = value.strip().replace(",", "")
    if cleaned in ("", "--"):
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _parse_date(value: str):
    """Garmin exports dates like '2026-08-01 07:15:32' or plain '2026-08-01'."""
    value = value.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_activities_csv(path: str, as_of: dt.date | None = None) -> GarminSummary:
    """Parse a Garmin CSV and summarize the most recent 7-day window.

    `as_of` defaults to the latest activity date found in the file (so the
    "most recent 7 days" is relative to the data, not to whenever the CLI runs).
    """
    warnings: list = []

    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = set(reader.fieldnames or [])
            missing = REQUIRED_COLUMNS - fieldnames
            if missing:
                warnings.append(
                    f"CSV is missing required column(s) {sorted(missing)} — "
                    "skipping activity import, using zero adjustment."
                )
                return GarminSummary("", "", 0.0, 0.0, 0.0, 0, 0.0, warnings)

            rows = list(reader)
    except FileNotFoundError:
        warnings.append(f"File not found: {path} — using zero adjustment.")
        return GarminSummary("", "", 0.0, 0.0, 0.0, 0, 0.0, warnings)
    except (OSError, csv.Error) as exc:
        warnings.append(f"Could not read CSV ({exc}) — using zero adjustment.")
        return GarminSummary("", "", 0.0, 0.0, 0.0, 0, 0.0, warnings)

    parsed_rows = []
    for row in rows:
        date = _parse_date(row.get("Date", ""))
        if date is None:
            continue
        parsed_rows.append((date, row))

    if not parsed_rows:
        warnings.append("No rows with a parseable Date column — using zero adjustment.")
        return GarminSummary("", "", 0.0, 0.0, 0.0, 0, 0.0, warnings)

    if as_of is None:
        as_of = max(d for d, _ in parsed_rows)
    window_start = as_of - dt.timedelta(days=WINDOW_DAYS - 1)

    in_window = [(d, row) for d, row in parsed_rows if window_start <= d <= as_of]

    total_distance = sum(_parse_float(row.get("Distance", "0")) for _, row in in_window)
    total_duration = sum(_parse_float(row.get("Time", "0")) for _, row in in_window)
    total_calories = sum(_parse_float(row.get("Calories", "0")) for _, row in in_window)

    # Not every logged calorie burn should raise the day's eating target — Garmin's
    # "Calories" figure already includes resting metabolism for the activity's
    # duration, which TDEE already accounts for. Use half the logged total as the
    # net *additional* daily budget, averaged across the 7-day window.
    daily_adjustment = min((total_calories * 0.5) / WINDOW_DAYS, MAX_DAILY_ADJUSTMENT_KCAL)

    return GarminSummary(
        window_start=window_start.isoformat(),
        window_end=as_of.isoformat(),
        total_distance_km=round(total_distance, 2),
        total_duration_min=round(total_duration, 1),
        total_calories=round(total_calories, 1),
        activity_count=len(in_window),
        daily_adjustment_kcal=round(daily_adjustment, 1),
        warnings=warnings,
    )
