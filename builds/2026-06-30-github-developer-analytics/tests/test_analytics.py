"""Tests for analytics aggregation logic."""

import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from analytics import (
    generate_month_labels,
    build_timeline_heatmap,
    build_hour_heatmap,
    build_weekday_heatmap,
    build_top_repos,
    build_language_chart,
    aggregate,
)


def _dt(year: int, month: int, day: int, hour: int = 12) -> datetime:
    return datetime(year, month, day, hour, 0, 0, tzinfo=timezone.utc)


class TestGenerateMonthLabels:
    def test_correct_count(self):
        labels = generate_month_labels(12)
        assert len(labels) == 12

    def test_ends_with_current_month(self):
        now = datetime.now(timezone.utc)
        labels = generate_month_labels(3)
        assert labels[-1] == f"{now.year:04d}-{now.month:02d}"

    def test_format_yyyy_mm(self):
        labels = generate_month_labels(1)
        assert len(labels[0]) == 7
        assert labels[0][4] == "-"


class TestBuildTimelineHeatmap:
    def test_empty_input_returns_empty_repos(self):
        result = build_timeline_heatmap({})
        assert result["repos"] == []
        assert result["data"] == []
        assert result["max_val"] == 0

    def test_single_repo_single_month(self):
        commits = {"repo1": [_dt(2026, 6, 15), _dt(2026, 6, 20)]}
        result = build_timeline_heatmap(commits, months_back=12)
        assert "repo1" in result["repos"]
        idx = result["repos"].index("repo1")
        month_idx = result["months"].index("2026-06")
        assert result["data"][idx][month_idx] == 2

    def test_top_n_limit_applied(self):
        commits = {f"repo{i}": [_dt(2026, 6, 1)] * i for i in range(1, 20)}
        result = build_timeline_heatmap(commits, months_back=12, top_n=5)
        assert len(result["repos"]) == 5

    def test_repos_ordered_by_commit_count(self):
        commits = {
            "low": [_dt(2026, 6, 1)],
            "high": [_dt(2026, 6, 1)] * 10,
            "mid": [_dt(2026, 6, 1)] * 5,
        }
        result = build_timeline_heatmap(commits, months_back=12)
        assert result["repos"][0] == "high"
        assert result["repos"][1] == "mid"

    def test_max_val_reflects_busiest_cell(self):
        commits = {"repo1": [_dt(2026, 6, 1)] * 7}
        result = build_timeline_heatmap(commits, months_back=12)
        assert result["max_val"] == 7

    def test_commits_outside_window_excluded(self):
        commits = {"repo1": [_dt(2020, 1, 1)]}  # 5+ years ago
        result = build_timeline_heatmap(commits, months_back=12)
        # Repo should appear but with zero commits in the window
        if "repo1" in result["repos"]:
            idx = result["repos"].index("repo1")
            assert all(v == 0 for v in result["data"][idx])


class TestBuildHourHeatmap:
    def test_empty_returns_24_zeros(self):
        counts = build_hour_heatmap([])
        assert counts == [0] * 24

    def test_correct_length(self):
        counts = build_hour_heatmap([_dt(2026, 6, 1, h) for h in range(24)])
        assert len(counts) == 24

    def test_counts_accumulate_correctly(self):
        dts = [_dt(2026, 6, 1, 9), _dt(2026, 6, 2, 9), _dt(2026, 6, 1, 14)]
        counts = build_hour_heatmap(dts)
        assert counts[9] == 2
        assert counts[14] == 1
        assert counts[0] == 0


class TestBuildWeekdayHeatmap:
    def test_empty_returns_7_zeros(self):
        counts = build_weekday_heatmap([])
        assert counts == [0] * 7

    def test_correct_length(self):
        counts = build_weekday_heatmap([_dt(2026, 6, 1)])
        assert len(counts) == 7

    def test_monday_is_index_0(self):
        # 2026-06-01 is a Monday
        counts = build_weekday_heatmap([_dt(2026, 6, 1)])
        assert counts[0] == 1

    def test_total_equals_input_length(self):
        dts = [_dt(2026, 6, i + 1) for i in range(7)]
        counts = build_weekday_heatmap(dts)
        assert sum(counts) == 7


class TestBuildTopRepos:
    def test_ordering_by_commits_descending(self):
        commits = {"a": [_dt(2026, 6, 1)], "b": [_dt(2026, 6, 1)] * 5}
        result = build_top_repos(commits)
        assert result[0]["name"] == "b"
        assert result[0]["commits"] == 5

    def test_top_n_limit(self):
        commits = {f"repo{i}": [_dt(2026, 6, 1)] * i for i in range(1, 15)}
        result = build_top_repos(commits, top_n=5)
        assert len(result) == 5

    def test_empty_input(self):
        result = build_top_repos({})
        assert result == []


class TestBuildLanguageChart:
    def test_empty_input(self):
        result = build_language_chart({})
        assert result["repos"] == []
        assert result["langs"] == []
        assert result["data"] == []

    def test_top_langs_limit(self):
        langs = {"repo1": {f"Lang{i}": 1000 * i for i in range(1, 15)}}
        result = build_language_chart(langs, top_langs_n=5)
        assert len(result["langs"]) == 5

    def test_langs_sorted_by_total_bytes(self):
        langs = {"repo1": {"Python": 5000, "JS": 1000}}
        result = build_language_chart(langs)
        assert result["langs"][0] == "Python"

    def test_data_dimensions_match(self):
        langs = {"repo1": {"Python": 5000}, "repo2": {"JS": 1000, "Python": 200}}
        result = build_language_chart(langs)
        assert len(result["data"]) == len(result["repos"])
        for row in result["data"]:
            assert len(row) == len(result["langs"])


class TestAggregate:
    def test_returns_required_keys(self):
        commits = {"repo1": [_dt(2026, 6, 1)]}
        langs = {"repo1": {"Python": 1000}}
        result = aggregate(commits, langs)
        for key in ["total_commits", "active_repos", "timeline", "hour_counts",
                    "weekday_counts", "top_repos", "languages", "generated_at"]:
            assert key in result

    def test_total_commits_sum(self):
        commits = {"a": [_dt(2026, 6, 1)] * 3, "b": [_dt(2026, 6, 2)] * 2}
        result = aggregate(commits, {})
        assert result["total_commits"] == 5

    def test_active_repos_count(self):
        commits = {"a": [_dt(2026, 6, 1)], "b": [], "c": [_dt(2026, 6, 2)]}
        result = aggregate(commits, {})
        assert result["active_repos"] == 2

    def test_most_active_repo_identified(self):
        commits = {"slow": [_dt(2026, 6, 1)], "fast": [_dt(2026, 6, 1)] * 5}
        result = aggregate(commits, {})
        assert result["most_active_repo"] == "fast"

    def test_empty_data_safe(self):
        result = aggregate({}, {})
        assert result["total_commits"] == 0
        assert result["active_repos"] == 0
