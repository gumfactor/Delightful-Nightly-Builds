"""
Pattern analysis for GitHub commit data.
All functions are pure (no I/O) and accept a list of commit dicts:
  {"repo": str, "sha": str, "timestamp": str (ISO 8601 UTC), "message": str}
Timestamps are converted to America/Toronto before analysis.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TORONTO = ZoneInfo("America/Toronto")

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
HOUR_LABELS = [
    "12am", "1am", "2am", "3am", "4am", "5am",
    "6am", "7am", "8am", "9am", "10am", "11am",
    "12pm", "1pm", "2pm", "3pm", "4pm", "5pm",
    "6pm", "7pm", "8pm", "9pm", "10pm", "11pm",
]


def _parse_ts(ts: str) -> datetime:
    """Parse ISO 8601 UTC string to Toronto-local datetime."""
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt.astimezone(TORONTO)


def _commit_dates(commits: list[dict]) -> set[date]:
    dates: set[date] = set()
    for c in commits:
        if c.get("timestamp"):
            dates.add(_parse_ts(c["timestamp"]).date())
    return dates


def hourly_distribution(commits: list[dict]) -> dict[int, int]:
    """Return commit counts keyed by hour-of-day (0–23, local time)."""
    counts: dict[int, int] = {h: 0 for h in range(24)}
    for c in commits:
        if c.get("timestamp"):
            counts[_parse_ts(c["timestamp"]).hour] += 1
    return counts


def day_of_week_distribution(commits: list[dict]) -> dict[int, int]:
    """Return commit counts keyed by weekday (0=Mon, 6=Sun, local time)."""
    counts: dict[int, int] = {d: 0 for d in range(7)}
    for c in commits:
        if c.get("timestamp"):
            counts[_parse_ts(c["timestamp"]).weekday()] += 1
    return counts


def weekly_aggregation(commits: list[dict], weeks: int = 52) -> list[dict]:
    """
    Return ordered list of {week, count} for the past `weeks` ISO weeks.
    Missing weeks are included with count=0.
    """
    week_counts: dict[str, int] = defaultdict(int)
    for c in commits:
        if c.get("timestamp"):
            d = _parse_ts(c["timestamp"]).date()
            iso = d.isocalendar()
            key = f"{iso.year}-W{iso.week:02d}"
            week_counts[key] += 1

    today = date.today()
    result: list[dict] = []
    for i in range(weeks - 1, -1, -1):
        d = today - timedelta(weeks=i)
        iso = d.isocalendar()
        key = f"{iso.year}-W{iso.week:02d}"
        result.append({"week": key, "count": week_counts.get(key, 0)})

    return result


def repo_breakdown(commits: list[dict], top_n: int = 10) -> list[dict]:
    """Return top-N repos by commit count, sorted descending."""
    counts: dict[str, int] = defaultdict(int)
    for c in commits:
        if c.get("repo"):
            counts[c["repo"]] += 1
    sorted_repos = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return [{"repo": r, "count": n} for r, n in sorted_repos[:top_n]]


def compute_streak(commits: list[dict]) -> dict[str, int]:
    """
    Return {current_streak, longest_streak} in calendar days.
    Current streak: consecutive days ending today or yesterday
    (allows for the fact that today may not be over yet).
    """
    if not commits:
        return {"current_streak": 0, "longest_streak": 0}

    dates = _commit_dates(commits)
    if not dates:
        return {"current_streak": 0, "longest_streak": 0}

    sorted_dates = sorted(dates)

    # Longest run of consecutive calendar days
    longest = 1
    run = 1
    for i in range(1, len(sorted_dates)):
        if sorted_dates[i] - sorted_dates[i - 1] == timedelta(days=1):
            run += 1
            longest = max(longest, run)
        else:
            run = 1

    # Current streak: walk backwards from today (or yesterday)
    today = date.today()
    yesterday = today - timedelta(days=1)
    anchor = today if today in dates else (yesterday if yesterday in dates else None)

    if anchor is None:
        return {"current_streak": 0, "longest_streak": longest}

    current = 1
    check = anchor - timedelta(days=1)
    while check in dates:
        current += 1
        check -= timedelta(days=1)

    return {"current_streak": current, "longest_streak": max(longest, current)}


def compute_stats(commits: list[dict], username: str = "", months: int = 12) -> dict:
    """Aggregate all metrics into a single stats dict for the renderer and AI."""
    if not commits:
        return {
            "username": username,
            "total_commits": 0,
            "active_days": 0,
            "commits_per_active_day": 0.0,
            "most_productive_hour": 0,
            "most_productive_day": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "top_repo": "",
            "top_repo_count": 0,
            "months": months,
            "hourly_distribution": {h: 0 for h in range(24)},
            "day_distribution": {d: 0 for d in range(7)},
            "weekly_series": weekly_aggregation([], weeks=52),
            "repo_breakdown": [],
        }

    hourly = hourly_distribution(commits)
    daily = day_of_week_distribution(commits)
    active_days = len(_commit_dates(commits))
    streak = compute_streak(commits)
    repos = repo_breakdown(commits, top_n=10)
    top_repo = repos[0]["repo"] if repos else ""
    top_repo_count = repos[0]["count"] if repos else 0

    most_productive_hour = max(hourly, key=lambda h: hourly[h])
    most_productive_day = max(daily, key=lambda d: daily[d])

    return {
        "username": username,
        "total_commits": len(commits),
        "active_days": active_days,
        "commits_per_active_day": round(len(commits) / max(active_days, 1), 1),
        "most_productive_hour": most_productive_hour,
        "most_productive_day": most_productive_day,
        "current_streak": streak["current_streak"],
        "longest_streak": streak["longest_streak"],
        "top_repo": top_repo,
        "top_repo_count": top_repo_count,
        "months": months,
        "hourly_distribution": hourly,
        "day_distribution": daily,
        "weekly_series": weekly_aggregation(commits, weeks=52),
        "repo_breakdown": repos,
    }
