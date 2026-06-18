"""Tests for src/quality.py — quality metric computation."""

import pytest
from src.quality import (
    compute_missing_rate,
    compute_completion_rate,
    compute_timing_stats,
    detect_straight_liners,
    detect_duplicate_ips,
    cronbach_alpha,
    auto_detect_scales,
    compute_quality,
    _sample_variance,
)
from src.parser import parse_csv

# Shared test rows that mirror the parser test fixture
ROWS = [
    {"ResponseId": "R_001", "IPAddress": "192.168.1.1", "Progress": "100",
     "Duration (in seconds)": "180", "Q1": "4", "Q2_1": "3", "Q2_2": "4", "Q2_3": "3"},
    {"ResponseId": "R_002", "IPAddress": "192.168.1.2", "Progress": "100",
     "Duration (in seconds)": "45",  "Q1": "5", "Q2_1": "5", "Q2_2": "5", "Q2_3": "5"},
    {"ResponseId": "R_003", "IPAddress": "192.168.1.3", "Progress": "75",
     "Duration (in seconds)": "120", "Q1": "3", "Q2_1": None, "Q2_2": "2", "Q2_3": None},
    {"ResponseId": "R_004", "IPAddress": "192.168.1.1", "Progress": "100",
     "Duration (in seconds)": "200", "Q1": "2", "Q2_1": "4", "Q2_2": "3", "Q2_3": "5"},
]


class TestMissingRate:
    def test_no_missing(self):
        assert compute_missing_rate(["a", "b", "c"]) == 0.0

    def test_all_missing(self):
        assert compute_missing_rate([None, None, None]) == 1.0

    def test_half_missing(self):
        assert compute_missing_rate([None, "a", None, "b"]) == 0.5

    def test_empty_list(self):
        assert compute_missing_rate([]) == 0.0


class TestCompletionRate:
    def test_all_complete(self):
        rows = [{"Progress": "100"}, {"Progress": "100"}]
        assert compute_completion_rate(rows) == 1.0

    def test_none_complete(self):
        rows = [{"Progress": "75"}, {"Progress": "50"}]
        assert compute_completion_rate(rows) == 0.0

    def test_partial_completion(self):
        # 3 of 4 rows complete
        rate = compute_completion_rate(ROWS)
        assert abs(rate - 0.75) < 0.001

    def test_empty_rows(self):
        assert compute_completion_rate([]) == 0.0


class TestTimingStats:
    def test_mean_and_median(self):
        stats = compute_timing_stats(ROWS)
        # Durations: 180, 45, 120, 200 → mean = 136.25, median = (120+180)/2 = 150
        assert stats["mean"] == 136.25 or abs(stats["mean"] - 136.25) < 0.1
        assert stats["median"] == 150.0

    def test_fast_count(self):
        stats = compute_timing_stats(ROWS, threshold_seconds=60)
        assert stats["fast_count"] == 1  # R_002 at 45s

    def test_min_max(self):
        stats = compute_timing_stats(ROWS)
        assert stats["min"] == 45.0
        assert stats["max"] == 200.0

    def test_no_timing_data(self):
        rows = [{"Progress": "100"}, {"Progress": "75"}]
        stats = compute_timing_stats(rows)
        assert stats["count"] == 0
        assert stats["mean"] is None


class TestStraightLiners:
    def test_detects_straight_liner(self):
        # R_002 gives 5,5,5 on Q2 items
        ids = detect_straight_liners(ROWS, ["Q2_1", "Q2_2", "Q2_3"])
        assert "R_002" in ids

    def test_no_false_positives(self):
        # R_001 gives 3,4,3 — varied enough
        ids = detect_straight_liners(ROWS, ["Q2_1", "Q2_2", "Q2_3"])
        assert "R_001" not in ids
        assert "R_004" not in ids

    def test_skips_rows_with_too_few_items(self):
        # R_003 only has 1 non-None Q2 item — not enough to flag
        ids = detect_straight_liners(ROWS, ["Q2_1", "Q2_2", "Q2_3"])
        assert "R_003" not in ids

    def test_empty_scale_columns(self):
        ids = detect_straight_liners(ROWS, [])
        assert ids == []


class TestDuplicateIPs:
    def test_finds_duplicate(self):
        ips = detect_duplicate_ips(ROWS)
        assert "192.168.1.1" in ips

    def test_no_duplicates_in_unique_ips(self):
        rows = [
            {"IPAddress": "10.0.0.1"},
            {"IPAddress": "10.0.0.2"},
            {"IPAddress": "10.0.0.3"},
        ]
        assert detect_duplicate_ips(rows) == []

    def test_handles_missing_ip(self):
        rows = [{"IPAddress": None}, {"IPAddress": None}]
        assert detect_duplicate_ips(rows) == []


class TestCronbachAlpha:
    def test_perfect_correlation(self):
        # Items perfectly correlated → alpha = 1.0
        item_scores = [[1, 2, 3], [1, 2, 3], [1, 2, 3]]
        alpha = cronbach_alpha(item_scores)
        assert alpha is not None
        assert abs(alpha - 1.0) < 0.001

    def test_reasonable_value(self):
        # Q2 items for respondents R_001, R_002, R_004 (R_003 excluded — missing)
        # Q2_1: 3,5,4  Q2_2: 4,5,3  Q2_3: 3,5,5
        item_scores = [[3, 5, 4], [4, 5, 3], [3, 5, 5]]
        alpha = cronbach_alpha(item_scores)
        assert alpha is not None
        assert 0.5 < alpha < 1.0

    def test_returns_none_for_single_item(self):
        assert cronbach_alpha([[1, 2, 3]]) is None

    def test_returns_none_for_single_respondent(self):
        assert cronbach_alpha([[5], [5]]) is None

    def test_returns_none_for_zero_total_variance(self):
        # All respondents give identical total scores → total variance = 0
        item_scores = [[1, 2, 3], [2, 1, 0]]  # totals: [3, 3, 3] → var = 0
        result = cronbach_alpha(item_scores)
        assert result is None


class TestAutoDetectScales:
    def test_groups_prefixed_columns(self):
        cols = ["ResponseId", "Q1", "Q2_1", "Q2_2", "Q2_3", "Q3_1", "Q3_2"]
        scales = auto_detect_scales(cols)
        assert "Q2" in scales
        assert scales["Q2"] == ["Q2_1", "Q2_2", "Q2_3"]
        assert "Q3" in scales

    def test_ignores_singleton_columns(self):
        cols = ["Q1", "Q2_1"]  # Q2 has only 1 item — not a scale
        scales = auto_detect_scales(cols)
        assert "Q2" not in scales

    def test_handles_empty_list(self):
        assert auto_detect_scales([]) == {}
