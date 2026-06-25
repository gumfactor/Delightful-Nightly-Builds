"""Tests for the statistical test decision tree."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from advisor import recommend_test, TestRecommendation


# ── Happy path: each major test type ──────────────────────────────────────────

def test_independent_samples_t_test():
    rec = recommend_test("continuous", 2, False, "assumed", False)
    assert rec.test_name == "Independent Samples t-test"
    assert rec.family == "parametric"


def test_paired_samples_t_test():
    rec = recommend_test("continuous", 2, True, "assumed", False)
    assert rec.test_name == "Paired Samples t-test"
    assert rec.family == "parametric"


def test_one_way_anova():
    rec = recommend_test("continuous", 3, False, "assumed", False)
    assert rec.test_name == "One-Way ANOVA"
    assert rec.family == "parametric"


def test_repeated_measures_anova():
    rec = recommend_test("continuous", 3, True, "assumed", False)
    assert rec.test_name == "Repeated Measures ANOVA"
    assert rec.family == "parametric"


def test_mann_whitney_continuous_violated():
    rec = recommend_test("continuous", 2, False, "violated", False)
    assert rec.test_name == "Mann-Whitney U Test"
    assert rec.family == "non-parametric"


def test_wilcoxon_signed_rank_continuous():
    rec = recommend_test("continuous", 2, True, "violated", False)
    assert rec.test_name == "Wilcoxon Signed-Rank Test"
    assert rec.family == "non-parametric"


def test_kruskal_wallis_violated():
    rec = recommend_test("continuous", 3, False, "violated", False)
    assert rec.test_name == "Kruskal-Wallis Test"
    assert rec.family == "non-parametric"


def test_kruskal_wallis_repeated_violated():
    rec = recommend_test("continuous", 3, True, "violated", False)
    assert rec.test_name == "Kruskal-Wallis Test"


def test_pearson_correlation():
    rec = recommend_test("continuous", 2, False, "assumed", True)
    assert rec.test_name == "Pearson Correlation"


def test_spearman_correlation_violated():
    rec = recommend_test("continuous", 2, False, "violated", True)
    assert rec.test_name == "Spearman Correlation"


def test_spearman_correlation_ordinal():
    rec = recommend_test("ordinal", 2, False, "assumed", True)
    assert rec.test_name == "Spearman Correlation"


def test_chi_square_three_groups():
    rec = recommend_test("categorical", 3, False, "assumed", False)
    assert rec.test_name == "Chi-Square Test of Independence"
    assert rec.family == "categorical"


def test_fishers_exact_two_groups():
    rec = recommend_test("categorical", 2, False, "assumed", False)
    assert rec.test_name == "Fisher's Exact Test"


def test_mcnemar_paired_categorical():
    rec = recommend_test("categorical", 2, True, "assumed", False)
    assert rec.test_name == "McNemar Test"


def test_one_sample_t_test():
    rec = recommend_test("continuous", 1, False, "assumed", False)
    assert rec.test_name == "One-Sample t-test"


def test_logistic_regression():
    rec = recommend_test("categorical", 2, False, "assumed", True)
    assert rec.test_name == "Logistic Regression"


def test_ordinal_two_groups_independent():
    rec = recommend_test("ordinal", 2, False, "assumed", False)
    assert rec.test_name == "Mann-Whitney U Test"


def test_ordinal_two_groups_paired():
    rec = recommend_test("ordinal", 2, True, "assumed", False)
    assert rec.test_name == "Wilcoxon Signed-Rank Test"


def test_ordinal_three_groups():
    rec = recommend_test("ordinal", 3, False, "assumed", False)
    assert rec.test_name == "Kruskal-Wallis Test"


# ── Unknown normality treated conservatively (non-parametric) ─────────────────

def test_unknown_normality_two_independent():
    rec = recommend_test("continuous", 2, False, "unknown", False)
    assert rec.test_name == "Mann-Whitney U Test"


def test_unknown_normality_two_paired():
    rec = recommend_test("continuous", 2, True, "unknown", False)
    assert rec.test_name == "Wilcoxon Signed-Rank Test"


def test_unknown_normality_three_groups():
    rec = recommend_test("continuous", 3, False, "unknown", False)
    assert rec.test_name == "Kruskal-Wallis Test"


# ── Return type shape ─────────────────────────────────────────────────────────

def test_returns_dataclass():
    rec = recommend_test("continuous", 2, False, "assumed", False)
    assert isinstance(rec, TestRecommendation)


def test_r_snippet_non_empty():
    rec = recommend_test("continuous", 2, False, "assumed", False)
    assert len(rec.r_snippet) > 10


def test_python_snippet_non_empty():
    rec = recommend_test("continuous", 2, False, "assumed", False)
    assert len(rec.python_snippet) > 10


def test_assumptions_non_empty():
    rec = recommend_test("continuous", 2, False, "assumed", False)
    assert len(rec.assumptions) >= 1


def test_interpretation_non_empty():
    rec = recommend_test("continuous", 2, False, "assumed", False)
    assert len(rec.interpretation_notes) > 10


# ── Error handling ─────────────────────────────────────────────────────────────

def test_invalid_outcome_type():
    with pytest.raises(ValueError):
        recommend_test("ratio", 2, False, "assumed", False)


def test_invalid_normality():
    with pytest.raises(ValueError):
        recommend_test("continuous", 2, False, "normal", False)


def test_zero_groups():
    with pytest.raises(ValueError):
        recommend_test("continuous", 0, False, "assumed", False)


def test_negative_groups():
    with pytest.raises(ValueError):
        recommend_test("continuous", -1, False, "assumed", False)


# ── Study context is accepted without error ───────────────────────────────────

def test_study_context_accepted():
    rec = recommend_test("continuous", 2, False, "assumed", False, "Comparing memory scores")
    assert rec.test_name == "Independent Samples t-test"
