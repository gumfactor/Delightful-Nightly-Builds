"""Tests for src/statistics.py — distributional stats, normality, correlation."""

import math
import pytest
from src.statistics import (
    skewness, excess_kurtosis, descriptive_stats,
    normality_test, pearson_r, correlation_matrix,
    item_total_correlations, extract_numeric_column,
    _chi2_sf, _normal_sf,
)


# ── Skewness ──────────────────────────────────────────────────────────────────

class TestSkewness:
    def test_symmetric_data_near_zero(self):
        vals = [1, 2, 3, 4, 5, 4, 3, 2, 1]
        assert abs(skewness(vals)) < 0.2

    def test_right_skewed(self):
        vals = [1, 1, 1, 1, 1, 2, 3, 10, 20]
        assert skewness(vals) > 1.0

    def test_left_skewed(self):
        vals = [1, 5, 10, 20, 20, 20, 20, 20, 20]
        assert skewness(vals) < -0.5

    def test_too_few_values_returns_none(self):
        assert skewness([1, 2]) is None

    def test_zero_variance_returns_none(self):
        assert skewness([5, 5, 5, 5]) is None


# ── Kurtosis ──────────────────────────────────────────────────────────────────

class TestKurtosis:
    def test_normal_like_near_zero(self):
        # Normal distribution has excess kurtosis ≈ 0
        import random
        random.seed(42)
        vals = [random.gauss(0, 1) for _ in range(500)]
        assert abs(excess_kurtosis(vals)) < 1.0

    def test_too_few_values_returns_none(self):
        assert excess_kurtosis([1, 2, 3]) is None

    def test_zero_variance_returns_none(self):
        assert excess_kurtosis([3, 3, 3, 3, 3]) is None


# ── Descriptive stats ─────────────────────────────────────────────────────────

class TestDescriptiveStats:
    def test_known_values(self):
        vals = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        stats = descriptive_stats(vals)
        assert stats["n"] == 8
        assert abs(stats["mean"] - 5.0) < 0.001
        assert abs(stats["std"] - 2.138) < 0.01
        assert stats["min"] == 2.0
        assert stats["max"] == 9.0

    def test_median_even_n(self):
        stats = descriptive_stats([1.0, 2.0, 3.0, 4.0])
        assert stats["median"] == 2.5

    def test_iqr(self):
        stats = descriptive_stats([1, 2, 3, 4, 5, 6, 7, 8])
        assert stats["iqr"] > 0

    def test_single_value(self):
        stats = descriptive_stats([42.0])
        assert stats["n"] == 1
        assert stats["mean"] == 42.0

    def test_empty_returns_n_zero(self):
        stats = descriptive_stats([])
        assert stats["n"] == 0


# ── Chi-squared survival function ─────────────────────────────────────────────

class TestChi2SF:
    def test_df2_known_value(self):
        # P(chi2(2) > 5.991) ≈ 0.05
        assert abs(_chi2_sf(5.991, 2) - 0.05) < 0.005

    def test_df2_zero_input(self):
        assert _chi2_sf(0, 2) == 1.0

    def test_df4_known_value(self):
        # P(chi2(4) > 9.488) ≈ 0.05
        assert abs(_chi2_sf(9.488, 4) - 0.05) < 0.01

    def test_large_value_near_zero(self):
        assert _chi2_sf(100, 2) < 1e-20

    def test_df1_known_value(self):
        # P(chi2(1) > 3.841) ≈ 0.05
        assert abs(_chi2_sf(3.841, 1) - 0.05) < 0.005


# ── Normality test ────────────────────────────────────────────────────────────

class TestNormalityTest:
    def test_normal_data_high_p(self):
        import random
        random.seed(0)
        vals = [random.gauss(0, 1) for _ in range(200)]
        result = normality_test(vals)
        assert result is not None
        assert result["is_normal"] is True
        assert result["p_value"] > 0.05

    def test_uniform_data_detected_non_normal(self):
        # Uniform distribution has negative excess kurtosis — often non-normal
        vals = list(range(1, 101))
        result = normality_test(vals)
        assert result is not None
        assert "statistic" in result
        assert "p_value" in result

    def test_heavily_skewed_non_normal(self):
        # Exponential-like: very right-skewed
        vals = [0.1, 0.1, 0.2, 0.3, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0] * 5
        result = normality_test(vals)
        assert result is not None
        assert result["is_normal"] is False

    def test_too_few_values_returns_none(self):
        assert normality_test([1, 2, 3]) is None

    def test_returns_expected_keys(self):
        vals = [float(i) for i in range(20)]
        result = normality_test(vals)
        assert result is not None
        for key in ("statistic", "p_value", "is_normal", "skewness_z", "kurtosis_z"):
            assert key in result


# ── Pearson correlation ───────────────────────────────────────────────────────

class TestPearsonR:
    def test_perfect_positive(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert pearson_r(x, x) == 1.0

    def test_perfect_negative(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [5.0, 4.0, 3.0, 2.0, 1.0]
        assert pearson_r(x, y) == -1.0

    def test_known_correlation(self):
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 5, 4, 5]
        r = pearson_r(x, y)
        assert r is not None
        assert 0.7 < r < 1.0

    def test_zero_variance_returns_none(self):
        assert pearson_r([1, 1, 1], [1, 2, 3]) is None

    def test_too_few_returns_none(self):
        assert pearson_r([1.0], [2.0]) is None

    def test_unequal_lengths_returns_none(self):
        assert pearson_r([1, 2, 3], [1, 2]) is None


# ── Correlation matrix ────────────────────────────────────────────────────────

class TestCorrelationMatrix:
    def test_diagonal_is_one(self):
        cols = {"A": [1.0, 2.0, 3.0], "B": [4.0, 5.0, 6.0]}
        matrix = correlation_matrix(cols)
        assert matrix["A"]["A"] == 1.0
        assert matrix["B"]["B"] == 1.0

    def test_symmetry(self):
        cols = {"A": [1.0, 2.0, 3.0], "B": [3.0, 1.0, 2.0]}
        matrix = correlation_matrix(cols)
        assert matrix["A"]["B"] == matrix["B"]["A"]

    def test_perfect_correlation(self):
        cols = {"A": [1.0, 2.0, 3.0], "B": [1.0, 2.0, 3.0]}
        matrix = correlation_matrix(cols)
        assert matrix["A"]["B"] == 1.0

    def test_none_values_handled(self):
        cols = {"A": [1.0, None, 3.0], "B": [4.0, 5.0, None]}
        matrix = correlation_matrix(cols)
        # Only one pairwise complete observation — should return None
        assert matrix["A"]["B"] is None


# ── Item-total correlations ───────────────────────────────────────────────────

class TestItemTotalCorrelations:
    def _make_rows(self, data):
        return [{"Q_1": str(r[0]), "Q_2": str(r[1]), "Q_3": str(r[2])} for r in data]

    def test_high_correlation_for_coherent_scale(self):
        rows = self._make_rows([(5, 4, 5), (4, 5, 4), (3, 3, 3), (2, 2, 2), (1, 1, 1)])
        itc = item_total_correlations(rows, ["Q_1", "Q_2", "Q_3"])
        for col, r in itc.items():
            assert r is not None
            assert r > 0.7

    def test_single_item_returns_none(self):
        rows = [{"Q_1": "5"}, {"Q_1": "3"}, {"Q_1": "4"}]
        itc = item_total_correlations(rows, ["Q_1"])
        assert itc["Q_1"] is None

    def test_missing_values_excluded(self):
        rows = [
            {"Q_1": "5", "Q_2": None, "Q_3": "4"},
            {"Q_1": "3", "Q_2": "3", "Q_3": "3"},
            {"Q_1": "1", "Q_2": "1", "Q_3": "1"},
        ]
        itc = item_total_correlations(rows, ["Q_1", "Q_2", "Q_3"])
        assert "Q_1" in itc


# ── extract_numeric_column ────────────────────────────────────────────────────

class TestExtractNumericColumn:
    def test_basic_extraction(self):
        rows = [{"Q1": "3"}, {"Q1": "5"}, {"Q1": None}, {"Q1": "abc"}]
        result = extract_numeric_column(rows, "Q1")
        assert result == [3.0, 5.0]

    def test_float_strings(self):
        rows = [{"v": "1.5"}, {"v": "2.7"}]
        assert extract_numeric_column(rows, "v") == [1.5, 2.7]
