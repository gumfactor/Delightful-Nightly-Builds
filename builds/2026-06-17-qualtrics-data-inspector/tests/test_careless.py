"""Tests for src/careless.py — careless responding composite index."""

import pytest
from src.careless import compute_careless_index, careless_summary


# ── Stub ──────────────────────────────────────────────────────────────────────

class _Quality:
    def __init__(
        self,
        fast_ids=None,
        straight_ids=None,
        high_missing_ids=None,
        outlier_counts=None,
    ):
        self.fast_response_ids = fast_ids or []
        self.straight_liner_ids = straight_ids or []
        self.high_missing_respondents = high_missing_ids or []
        self.respondent_outlier_counts = outlier_counts or {}


# ── compute_careless_index ────────────────────────────────────────────────────

class TestComputeCarelessIndex:
    def test_empty_quality_returns_empty(self):
        result = compute_careless_index(_Quality())
        assert result == {}

    def test_fast_response_flag(self):
        q = _Quality(fast_ids=["R1"])
        result = compute_careless_index(q)
        assert "R1" in result
        assert result["R1"]["components"]["fast_response"] == 1.0
        assert result["R1"]["components"]["straight_liner"] == 0.0
        assert "fast_response" in result["R1"]["flags"]

    def test_straight_liner_flag(self):
        q = _Quality(straight_ids=["R2"])
        result = compute_careless_index(q)
        assert "straight_liner" in result["R2"]["flags"]
        assert result["R2"]["components"]["straight_liner"] == 1.0

    def test_high_missing_flag(self):
        q = _Quality(high_missing_ids=["R3"])
        result = compute_careless_index(q)
        assert "high_missing" in result["R3"]["flags"]
        assert result["R3"]["components"]["high_missing"] == 1.0

    def test_outlier_breadth_capped_at_one(self):
        q = _Quality(outlier_counts={"R4": 6})
        result = compute_careless_index(q)
        assert result["R4"]["components"]["outlier_breadth"] == 1.0

    def test_outlier_breadth_one_column(self):
        q = _Quality(outlier_counts={"R5": 1})
        result = compute_careless_index(q)
        assert abs(result["R5"]["components"]["outlier_breadth"] - 1 / 3) < 0.001

    def test_outlier_breadth_two_columns(self):
        q = _Quality(outlier_counts={"R5b": 2})
        result = compute_careless_index(q)
        assert abs(result["R5b"]["components"]["outlier_breadth"] - 2 / 3) < 0.001

    def test_all_non_attention_flags_score_one(self):
        q = _Quality(
            fast_ids=["R6"],
            straight_ids=["R6"],
            high_missing_ids=["R6"],
            outlier_counts={"R6": 3},
        )
        result = compute_careless_index(q)
        # 4 components: fast=1, straight=1, high_missing=1, outlier=1 → score=1.0
        assert result["R6"]["score"] == 1.0

    def test_attention_fail_rate_component_present(self):
        q = _Quality(fast_ids=["R7"])
        attn = {
            "ATTN1": {"failed_ids": ["R7"]},
            "ATTN2": {"failed_ids": []},
        }
        result = compute_careless_index(q, attention_results=attn)
        assert "attention_fail_rate" in result["R7"]["components"]
        rate = result["R7"]["components"]["attention_fail_rate"]
        assert abs(rate - 0.5) < 0.001

    def test_attention_fail_rate_full_failure(self):
        q = _Quality()
        attn = {
            "ATTN1": {"failed_ids": ["R8"]},
            "ATTN2": {"failed_ids": ["R8"]},
        }
        result = compute_careless_index(q, attention_results=attn)
        assert result["R8"]["components"]["attention_fail_rate"] == 1.0

    def test_respondent_from_attention_only_is_included(self):
        q = _Quality()
        attn = {"ATTN1": {"failed_ids": ["R9"]}}
        result = compute_careless_index(q, attention_results=attn)
        assert "R9" in result

    def test_score_is_mean_of_components(self):
        q = _Quality(fast_ids=["R10"])
        result = compute_careless_index(q)
        data = result["R10"]
        expected = sum(data["components"].values()) / len(data["components"])
        assert abs(data["score"] - expected) < 0.0001

    def test_score_range_zero_to_one(self):
        q = _Quality(
            fast_ids=["R11"],
            straight_ids=["R12"],
            outlier_counts={"R13": 2},
        )
        result = compute_careless_index(q)
        for data in result.values():
            assert 0.0 <= data["score"] <= 1.0

    def test_clean_respondent_not_included_without_attention(self):
        q = _Quality()
        result = compute_careless_index(q)
        assert result == {}

    def test_flags_list_is_human_readable_strings(self):
        q = _Quality(fast_ids=["R14"], outlier_counts={"R14": 2})
        result = compute_careless_index(q)
        flags = result["R14"]["flags"]
        assert "fast_response" in flags
        assert any("outlier" in f for f in flags)

    def test_respondent_in_multiple_flag_sets(self):
        q = _Quality(fast_ids=["R15"], straight_ids=["R15"])
        result = compute_careless_index(q)
        assert result["R15"]["components"]["fast_response"] == 1.0
        assert result["R15"]["components"]["straight_liner"] == 1.0

    def test_no_attention_results_no_attention_component(self):
        q = _Quality(fast_ids=["R16"])
        result = compute_careless_index(q, attention_results=None)
        assert "attention_fail_rate" not in result["R16"]["components"]

    def test_empty_attention_results_no_attention_component(self):
        q = _Quality(fast_ids=["R17"])
        result = compute_careless_index(q, attention_results={})
        assert "attention_fail_rate" not in result["R17"]["components"]


# ── careless_summary ──────────────────────────────────────────────────────────

class TestCarelessSummary:
    def test_empty_returns_zero_flagged(self):
        summary = careless_summary({})
        assert summary["n_flagged"] == 0
        assert summary["mean_score"] is None

    def test_counts_above_threshold(self):
        index = {
            "R1": {"score": 0.1},
            "R2": {"score": 0.5},
            "R3": {"score": 0.8},
        }
        summary = careless_summary(index, threshold=0.4)
        assert summary["n_flagged"] == 2

    def test_mean_score_calculated(self):
        index = {
            "R1": {"score": 0.2},
            "R2": {"score": 0.6},
        }
        summary = careless_summary(index)
        assert abs(summary["mean_score"] - 0.4) < 0.001

    def test_score_distribution_bins(self):
        index = {
            "R1": {"score": 0.1},
            "R2": {"score": 0.3},
            "R3": {"score": 0.5},
            "R4": {"score": 0.7},
            "R5": {"score": 0.9},
        }
        summary = careless_summary(index)
        dist = summary["score_distribution"]
        assert dist["0.0–0.2"] == 1
        assert dist["0.2–0.4"] == 1
        assert dist["0.4–0.6"] == 1
        assert dist["0.6–0.8"] == 1
        assert dist["0.8–1.0"] == 1

    def test_custom_threshold(self):
        index = {
            "R1": {"score": 0.3},
            "R2": {"score": 0.6},
        }
        summary = careless_summary(index, threshold=0.5)
        assert summary["n_flagged"] == 1

    def test_threshold_in_result(self):
        summary = careless_summary({}, threshold=0.3)
        assert summary["threshold"] == 0.3

    def test_all_below_threshold_zero_flagged(self):
        index = {"R1": {"score": 0.1}, "R2": {"score": 0.2}}
        summary = careless_summary(index, threshold=0.4)
        assert summary["n_flagged"] == 0

    def test_single_respondent(self):
        index = {"R1": {"score": 0.75}}
        summary = careless_summary(index)
        assert summary["n_flagged"] == 1
        assert summary["mean_score"] == 0.75
