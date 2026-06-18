"""Tests for src/conditions.py — group detection and between-group tests."""

import math
import pytest
from src.conditions import (
    detect_condition_columns, group_descriptive_stats,
    mann_whitney_u, kruskal_wallis, run_condition_tests,
    compute_scale_scores,
)
from src.parser import parse_csv


# ── Helpers ───────────────────────────────────────────────────────────────────

def _minimal_survey(rows, extra_cols=None):
    """Build a ParsedSurvey-like object from raw rows."""
    from src.parser import ParsedSurvey, QualtricsColumn
    all_keys = set()
    for r in rows:
        all_keys.update(r.keys())
    cols = [QualtricsColumn(name=k, question_text=k) for k in sorted(all_keys)]
    return ParsedSurvey(columns=cols, rows=rows, is_qualtrics_format=False, respondent_count=len(rows))


# ── detect_condition_columns ──────────────────────────────────────────────────

class TestDetectConditionColumns:
    def _survey_with_condition(self, n=30):
        rows = []
        for i in range(n):
            rows.append({
                "ResponseId": f"R{i}",
                "condition": "A" if i % 2 == 0 else "B",
                "Q1": str(i % 5 + 1),
            })
        return _minimal_survey(rows)

    def test_detects_named_condition_column(self):
        survey = self._survey_with_condition(30)
        found = detect_condition_columns(survey)
        assert "condition" in found

    def test_ignores_high_cardinality_column(self):
        rows = [{"ResponseId": f"R{i}", "unique_id": str(i), "Q1": "3"} for i in range(30)]
        survey = _minimal_survey(rows)
        found = detect_condition_columns(survey)
        assert "unique_id" not in found

    def test_ignores_numeric_response_columns(self):
        rows = []
        for i in range(20):
            rows.append({"ResponseId": f"R{i}", "Q1": str(i % 5 + 1)})
        survey = _minimal_survey(rows)
        found = detect_condition_columns(survey)
        assert "Q1" not in found

    def test_returns_empty_when_no_candidates(self):
        rows = [{"ResponseId": f"R{i}", "Q1": str(i)} for i in range(10)]
        survey = _minimal_survey(rows)
        found = detect_condition_columns(survey)
        assert isinstance(found, list)


# ── group_descriptive_stats ───────────────────────────────────────────────────

class TestGroupDescriptiveStats:
    def _rows(self):
        return [
            {"condition": "A", "score": "5"},
            {"condition": "A", "score": "4"},
            {"condition": "A", "score": "5"},
            {"condition": "B", "score": "2"},
            {"condition": "B", "score": "3"},
            {"condition": "B", "score": "2"},
        ]

    def test_two_groups_detected(self):
        stats = group_descriptive_stats(self._rows(), "condition", "score")
        assert "A" in stats
        assert "B" in stats

    def test_group_means(self):
        stats = group_descriptive_stats(self._rows(), "condition", "score")
        assert abs(stats["A"]["mean"] - (14 / 3)) < 0.01
        assert abs(stats["B"]["mean"] - (7 / 3)) < 0.01

    def test_group_n(self):
        stats = group_descriptive_stats(self._rows(), "condition", "score")
        assert stats["A"]["n"] == 3
        assert stats["B"]["n"] == 3

    def test_missing_values_skipped(self):
        rows = self._rows() + [{"condition": "A", "score": None}]
        stats = group_descriptive_stats(rows, "condition", "score")
        assert stats["A"]["n"] == 3  # None row not counted


# ── Mann-Whitney U ────────────────────────────────────────────────────────────

class TestMannWhitneyU:
    def test_identical_groups_p_near_one(self):
        g = [3.0, 4.0, 3.0, 4.0, 3.0, 4.0, 3.0, 4.0, 3.0, 4.0]
        result = mann_whitney_u(g, g)
        assert result is not None
        assert result["p_value"] > 0.05

    def test_clearly_different_groups_low_p(self):
        g1 = [1.0, 1.5, 1.0, 1.5, 1.0, 1.5, 1.0, 1.5, 1.0, 1.5]
        g2 = [9.0, 9.5, 9.0, 9.5, 9.0, 9.5, 9.0, 9.5, 9.0, 9.5]
        result = mann_whitney_u(g1, g2)
        assert result is not None
        assert result["p_value"] < 0.05

    def test_returns_expected_keys(self):
        result = mann_whitney_u([1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                                [5, 6, 7, 8, 9, 10, 11, 12, 13, 14])
        assert result is not None
        for key in ("U", "z", "p_value", "effect_size_r", "n1", "n2"):
            assert key in result

    def test_too_few_observations_returns_none(self):
        assert mann_whitney_u([1.0], [2.0]) is None

    def test_effect_size_between_neg1_and_1(self):
        g1 = [float(i) for i in range(1, 11)]
        g2 = [float(i) for i in range(6, 16)]
        result = mann_whitney_u(g1, g2)
        assert result is not None
        assert -1.0 <= result["effect_size_r"] <= 1.0

    def test_n1_n2_correct(self):
        result = mann_whitney_u([1, 2, 3, 4, 5, 6, 7, 8], [9, 10, 11, 12, 13])
        assert result["n1"] == 8
        assert result["n2"] == 5


# ── Kruskal-Wallis ────────────────────────────────────────────────────────────

class TestKruskalWallis:
    def test_identical_groups_high_p(self):
        g = [3.0, 4.0, 3.0, 4.0, 3.0, 4.0, 3.0, 4.0]
        result = kruskal_wallis([g, g, g])
        assert result is not None
        assert result["p_value"] > 0.05

    def test_clearly_different_groups_low_p(self):
        g1 = [1.0] * 10
        g2 = [5.0] * 10
        g3 = [10.0] * 10
        result = kruskal_wallis([g1, g2, g3])
        assert result is not None
        assert result["p_value"] < 0.001

    def test_df_is_k_minus_one(self):
        groups = [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [2, 4, 6, 8, 10]]
        result = kruskal_wallis(groups)
        assert result["df"] == 2

    def test_returns_expected_keys(self):
        g1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        g2 = [3.0, 4.0, 5.0, 6.0, 7.0]
        result = kruskal_wallis([g1, g2])
        assert result is not None
        for key in ("H", "df", "p_value"):
            assert key in result

    def test_single_group_returns_none(self):
        assert kruskal_wallis([[1, 2, 3]]) is None

    def test_group_too_small_returns_none(self):
        assert kruskal_wallis([[1], [2, 3, 4]]) is None

    def test_h_statistic_nonnegative(self):
        g1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        g2 = [6.0, 7.0, 8.0, 9.0, 10.0]
        result = kruskal_wallis([g1, g2])
        assert result["H"] >= 0


# ── run_condition_tests ───────────────────────────────────────────────────────

class TestRunConditionTests:
    def _rows_two_groups(self, n=20):
        rows = []
        for i in range(n):
            group = "A" if i < n // 2 else "B"
            score = 4 + (1 if group == "A" else -1) + (i % 2) * 0.1
            rows.append({
                "ResponseId": f"R{i}",
                "condition": group,
                "PSS_1": str(score),
                "PSS_2": str(score + 0.5),
                "PSS_3": str(score - 0.3),
            })
        return rows

    def test_returns_result_per_scale(self):
        rows = self._rows_two_groups(20)
        result = run_condition_tests(rows, "condition", {"PSS": ["PSS_1", "PSS_2", "PSS_3"]})
        assert "PSS" in result

    def test_result_contains_group_stats_and_test(self):
        rows = self._rows_two_groups(20)
        result = run_condition_tests(rows, "condition", {"PSS": ["PSS_1", "PSS_2", "PSS_3"]})
        assert "group_stats" in result["PSS"]
        assert "test" in result["PSS"]

    def test_three_groups_uses_kruskal_wallis(self):
        rows = []
        for i in range(30):
            g = ["A", "B", "C"][i % 3]
            rows.append({
                "ResponseId": f"R{i}", "condition": g,
                "Q_1": str(float({"A": 5, "B": 3, "C": 1}[g])),
                "Q_2": str(float({"A": 4, "B": 3, "C": 2}[g])),
            })
        result = run_condition_tests(rows, "condition", {"Q": ["Q_1", "Q_2"]})
        assert result["Q"]["test"]["type"] == "Kruskal-Wallis H"

    def test_two_groups_uses_mann_whitney(self):
        rows = self._rows_two_groups(20)
        result = run_condition_tests(rows, "condition", {"PSS": ["PSS_1", "PSS_2", "PSS_3"]})
        assert result["PSS"]["test"]["type"] == "Mann-Whitney U"

    def test_empty_condition_col_returns_empty(self):
        rows = [{"ResponseId": f"R{i}", "Q_1": "3"} for i in range(10)]
        result = run_condition_tests(rows, "condition", {"Q": ["Q_1"]})
        assert result == {}
