"""Weekly stats, streaks, and mileage aggregation."""

from datetime import date, datetime, timedelta
from typing import List, Optional


def _run_date(run: dict) -> date:
    return datetime.strptime(run["date"], "%Y-%m-%d").date()


def weekly_mileage(runs: List[dict], year: int, week: int) -> float:
    """Sum distance_km for runs in the given ISO year/week."""
    total = 0.0
    for run in runs:
        d = _run_date(run)
        iso = d.isocalendar()
        if iso[0] == year and iso[1] == week:
            total += run["distance_km"]
    return round(total, 2)


def mileage_by_week(runs: List[dict]) -> List[dict]:
    """Return [{year, week, km}] for every week that has at least one run, sorted chronologically."""
    weeks: dict = {}
    for run in runs:
        d = _run_date(run)
        iso = d.isocalendar()
        key = (iso[0], iso[1])
        weeks[key] = round(weeks.get(key, 0.0) + run["distance_km"], 2)
    return [
        {"year": y, "week": w, "km": km}
        for (y, w), km in sorted(weeks.items())
    ]


def average_pace_seconds(runs: List[dict]) -> float:
    """Return average pace in seconds per km across all runs with positive distance."""
    valid = [r for r in runs if r.get("distance_km", 0) > 0]
    if not valid:
        return 0.0
    paces = [r["duration_seconds"] / r["distance_km"] for r in valid]
    return sum(paces) / len(paces)


def current_streak(runs: List[dict], reference_date: Optional[date] = None) -> int:
    """Count consecutive days ending on reference_date (default: today) with at least one run."""
    if not runs:
        return 0

    today = reference_date or date.today()
    run_dates = sorted({r["date"] for r in runs}, reverse=True)

    most_recent = datetime.strptime(run_dates[0], "%Y-%m-%d").date()
    if (today - most_recent).days > 1:
        return 0

    streak = 1
    for i in range(1, len(run_dates)):
        prev_date = datetime.strptime(run_dates[i - 1], "%Y-%m-%d").date()
        curr_date = datetime.strptime(run_dates[i], "%Y-%m-%d").date()
        if (prev_date - curr_date).days == 1:
            streak += 1
        else:
            break
    return streak


def weekly_summary(runs: List[dict], reference_date: Optional[date] = None) -> dict:
    """Return stats for the ISO week that contains reference_date (default: today)."""
    today = reference_date or date.today()
    today_iso = today.isocalendar()

    week_runs = [
        r for r in runs
        if _run_date(r).isocalendar()[:2] == (today_iso[0], today_iso[1])
    ]

    total_km = round(sum(r["distance_km"] for r in week_runs), 2)
    avg_pace_sec = average_pace_seconds(week_runs)
    avg_min = int(avg_pace_sec // 60)
    avg_sec = int(avg_pace_sec % 60)

    return {
        "run_count": len(week_runs),
        "total_km": total_km,
        "total_seconds": sum(r["duration_seconds"] for r in week_runs),
        "avg_pace": f"{avg_min}:{avg_sec:02d}" if week_runs else "--:--",
        "week_runs": week_runs,
    }
