"""
Tests for analyzer.py — 20 tests covering all analysis functions.

Timestamp notes (for local-time assertions):
  January 2026 = EST (UTC-5)
  June 2026    = EDT (UTC-4)

  2026-01-05T14:00:00Z = Mon Jan 5, 09:00 EST  → hour=9,  weekday=0 (Mon)
  2026-01-06T23:00:00Z = Tue Jan 6, 18:00 EST  → hour=18, weekday=1 (Tue)
  2026-01-07T04:00:00Z = Tue Jan 6, 23:00 EST  → hour=23, weekday=1 (Tue)
  2026-01-07T14:00:00Z = Wed Jan 7, 09:00 EST  → hour=9,  weekday=2 (Wed)
  2026-01-08T14:00:00Z = Thu Jan 8, 09:00 EST  → hour=9,  weekday=3 (Thu)
  2026-01-09T14:00:00Z = Fri Jan 9, 09:00 EST  → hour=9,  weekday=4 (Fri)
  2026-01-10T14:00:00Z = Sat Jan 10, 09:00 EST → hour=9,  weekday=5 (Sat)
  2026-01-11T14:00:00Z = Sun Jan 11, 09:00 EST → hour=9,  weekday=6 (Sun)
  2026-06-24T14:00:00Z = Wed Jun 24, 10:00 EDT → date=2026-06-24
  2026-06-25T14:00:00Z = Thu Jun 25, 10:00 EDT → date=2026-06-25
  2026-06-26T14:00:00Z = Fri Jun 26, 10:00 EDT → date=2026-06-26 (today)
"""

import sys
import os
from datetime import date as real_date, timedelta
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.analyzer import (
    hourly_distribution,
    day_of_week_distribution,
    weekly_aggregation,
    repo_breakdown,
    compute_streak,
    compute_stats,
)


def make_commit(timestamp: str, repo: str = "owner/repo") -> dict:
    return {"repo": repo, "sha": "abc1234", "timestamp": timestamp, "message": "test"}


# ─────────────────────────────────────────────────
# hourly_distribution
# ─────────────────────────────────────────────────

def test_hourly_distribution_empty():
    result = hourly_distribution([])
    assert result == {h: 0 for h in range(24)}


def test_hourly_distribution_returns_24_keys():
    result = hourly_distribution([make_commit("2026-01-05T14:00:00Z")])
    assert len(result) == 24
    assert set(result.keys()) == set(range(24))


def test_hourly_distribution_correct_hour():
    # 2026-01-05T14:00:00Z = 09:00 EST
    commits = [make_commit("2026-01-05T14:00:00Z")]
    result = hourly_distribution(commits)
    assert result[9] == 1
    assert result[14] == 0


def test_hourly_distribution_late_night():
    # 2026-01-07T04:00:00Z = Tue Jan 6 at 23:00 EST
    commits = [make_commit("2026-01-07T04:00:00Z")]
    result = hourly_distribution(commits)
    assert result[23] == 1


def test_hourly_distribution_multiple_commits_same_hour():
    commits = [
        make_commit("2026-01-05T14:00:00Z"),  # 09:00 EST
        make_commit("2026-01-06T14:30:00Z"),  # 09:30 EST (rounded down to 9)
    ]
    result = hourly_distribution(commits)
    assert result[9] == 2


def test_hourly_distribution_skips_empty_timestamp():
    commits = [{"repo": "owner/repo", "sha": "abc", "timestamp": "", "message": ""}]
    result = hourly_distribution(commits)
    assert sum(result.values()) == 0


# ─────────────────────────────────────────────────
# day_of_week_distribution
# ─────────────────────────────────────────────────

def test_day_of_week_empty():
    result = day_of_week_distribution([])
    assert result == {d: 0 for d in range(7)}


def test_day_of_week_correct_mapping():
    # Jan 5-11 2026 = Mon-Sun
    timestamps = [
        "2026-01-05T14:00:00Z",  # Mon
        "2026-01-06T14:00:00Z",  # Tue
        "2026-01-07T14:00:00Z",  # Wed
        "2026-01-08T14:00:00Z",  # Thu
        "2026-01-09T14:00:00Z",  # Fri
        "2026-01-10T14:00:00Z",  # Sat
        "2026-01-11T14:00:00Z",  # Sun
    ]
    commits = [make_commit(ts) for ts in timestamps]
    result = day_of_week_distribution(commits)
    for day in range(7):
        assert result[day] == 1, f"Expected 1 commit on weekday {day}"


def test_day_of_week_accumulates_same_day():
    # Two commits on Monday
    commits = [
        make_commit("2026-01-05T14:00:00Z"),
        make_commit("2026-01-12T14:00:00Z"),  # next Monday
    ]
    result = day_of_week_distribution(commits)
    assert result[0] == 2  # Mon=0


# ─────────────────────────────────────────────────
# weekly_aggregation
# ─────────────────────────────────────────────────

def test_weekly_aggregation_length():
    result = weekly_aggregation([], weeks=52)
    assert len(result) == 52


def test_weekly_aggregation_empty_all_zeros():
    result = weekly_aggregation([], weeks=4)
    assert all(w["count"] == 0 for w in result)


def test_weekly_aggregation_keys_format():
    result = weekly_aggregation([], weeks=4)
    for entry in result:
        assert "week" in entry and "count" in entry
        assert entry["week"].startswith("20")
        assert "-W" in entry["week"]


def test_weekly_aggregation_counts_commit():
    # Jan 5 2026 is in week 2026-W02
    commits = [make_commit("2026-01-05T14:00:00Z")]
    result = weekly_aggregation(commits, weeks=52)
    total = sum(w["count"] for w in result)
    assert total == 1


def test_weekly_aggregation_most_recent_last():
    result = weekly_aggregation([], weeks=4)
    # Last entry should be the most recent week (today's week)
    assert result[-1]["count"] == 0
    # Entries should be ordered oldest to newest
    weeks = [entry["week"] for entry in result]
    assert weeks == sorted(weeks)


# ─────────────────────────────────────────────────
# repo_breakdown
# ─────────────────────────────────────────────────

def test_repo_breakdown_empty():
    assert repo_breakdown([]) == []


def test_repo_breakdown_sorted_descending():
    commits = (
        [make_commit("2026-01-05T14:00:00Z", repo="owner/repo-a")] * 5
        + [make_commit("2026-01-05T14:00:00Z", repo="owner/repo-b")] * 10
        + [make_commit("2026-01-05T14:00:00Z", repo="owner/repo-c")] * 2
    )
    result = repo_breakdown(commits)
    assert result[0]["repo"] == "owner/repo-b"
    assert result[0]["count"] == 10
    assert result[1]["repo"] == "owner/repo-a"
    assert result[1]["count"] == 5


def test_repo_breakdown_top_n_truncation():
    commits = [make_commit("2026-01-05T14:00:00Z", repo=f"owner/repo-{i}") for i in range(20)]
    result = repo_breakdown(commits, top_n=5)
    assert len(result) == 5


# ─────────────────────────────────────────────────
# compute_streak
# ─────────────────────────────────────────────────

def test_streak_empty_commits():
    result = compute_streak([])
    assert result == {"current_streak": 0, "longest_streak": 0}


def test_streak_commits_with_empty_timestamps():
    commits = [{"repo": "r", "sha": "a", "timestamp": "", "message": ""}]
    result = compute_streak(commits)
    assert result["current_streak"] == 0
    assert result["longest_streak"] == 0


def test_streak_longest_far_in_past():
    # 4 consecutive days Jan 5-8, then a gap, Jan 15-16 (2 more)
    commits = [
        make_commit("2026-01-05T14:00:00Z"),
        make_commit("2026-01-06T14:00:00Z"),
        make_commit("2026-01-07T14:00:00Z"),
        make_commit("2026-01-08T14:00:00Z"),
        make_commit("2026-01-15T14:00:00Z"),
        make_commit("2026-01-16T14:00:00Z"),
    ]
    result = compute_streak(commits)
    assert result["longest_streak"] == 4
    assert result["current_streak"] == 0  # all in the past


def test_streak_with_today_yields_current_streak():
    # Mock today = 2026-06-26; commits on Jun 24, 25, 26
    commits = [
        make_commit("2026-06-24T14:00:00Z"),
        make_commit("2026-06-25T14:00:00Z"),
        make_commit("2026-06-26T14:00:00Z"),
    ]
    with patch("src.analyzer.date") as mock_date:
        mock_date.today.return_value = real_date(2026, 6, 26)
        result = compute_streak(commits)
    assert result["current_streak"] == 3
    assert result["longest_streak"] == 3


def test_streak_yesterday_only_still_counts():
    # Mock today = 2026-06-26; commit only on Jun 25 (yesterday)
    commits = [make_commit("2026-06-25T14:00:00Z")]
    with patch("src.analyzer.date") as mock_date:
        mock_date.today.return_value = real_date(2026, 6, 26)
        result = compute_streak(commits)
    assert result["current_streak"] == 1


def test_streak_gap_resets_current():
    # Mock today = 2026-06-26; last commit was Jun 24 (gap on Jun 25)
    commits = [make_commit("2026-06-24T14:00:00Z")]
    with patch("src.analyzer.date") as mock_date:
        mock_date.today.return_value = real_date(2026, 6, 26)
        result = compute_streak(commits)
    assert result["current_streak"] == 0


# ─────────────────────────────────────────────────
# compute_stats
# ─────────────────────────────────────────────────

def test_compute_stats_empty():
    result = compute_stats([], username="alice", months=12)
    assert result["total_commits"] == 0
    assert result["active_days"] == 0
    assert result["commits_per_active_day"] == 0.0
    assert result["username"] == "alice"
    assert len(result["hourly_distribution"]) == 24
    assert len(result["day_distribution"]) == 7
    assert len(result["weekly_series"]) == 52
    assert result["repo_breakdown"] == []


def test_compute_stats_counts_correctly():
    commits = [
        make_commit("2026-01-05T14:00:00Z", repo="owner/repo-a"),
        make_commit("2026-01-05T14:00:00Z", repo="owner/repo-a"),
        make_commit("2026-01-06T14:00:00Z", repo="owner/repo-b"),
    ]
    result = compute_stats(commits, username="bob", months=6)
    assert result["total_commits"] == 3
    assert result["active_days"] == 2
    assert result["commits_per_active_day"] == 1.5
    assert result["username"] == "bob"
    assert result["months"] == 6


def test_compute_stats_top_repo():
    commits = (
        [make_commit("2026-01-05T14:00:00Z", repo="owner/busy-repo")] * 8
        + [make_commit("2026-01-06T14:00:00Z", repo="owner/quiet-repo")] * 2
    )
    result = compute_stats(commits)
    assert result["top_repo"] == "owner/busy-repo"
    assert result["top_repo_count"] == 8


def test_compute_stats_most_productive_hour():
    commits = (
        [make_commit("2026-01-05T14:00:00Z")] * 3   # 09:00 EST × 3
        + [make_commit("2026-01-06T23:00:00Z")]       # 18:00 EST × 1
    )
    result = compute_stats(commits)
    assert result["most_productive_hour"] == 9
