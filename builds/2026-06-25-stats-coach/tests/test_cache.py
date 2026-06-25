"""Tests for the SQLite cache layer."""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from cache import AdviceCache


@pytest.fixture
def tmp_cache(tmp_path):
    return AdviceCache(tmp_path / "test.db")


SAMPLE_PARAMS = {
    "outcome_type": "continuous",
    "num_groups": 2,
    "paired": False,
    "normality": "assumed",
    "relationship": False,
}

SAMPLE_DATA = {
    "test_name": "Independent Samples t-test",
    "ai_explanation": "This is a test explanation.",
    "r_code": "t.test(outcome ~ group, data = df)",
    "python_code": "stats.ttest_ind(a, b)",
    "interpretation": "Report t(df) = X.XX, p = .XXX",
}


def test_cache_miss_returns_none(tmp_cache):
    result = tmp_cache.get(SAMPLE_PARAMS)
    assert result is None


def test_cache_put_and_get(tmp_cache):
    tmp_cache.put(SAMPLE_PARAMS, SAMPLE_DATA)
    result = tmp_cache.get(SAMPLE_PARAMS)
    assert result is not None
    assert result["test_name"] == "Independent Samples t-test"


def test_cache_get_returns_correct_fields(tmp_cache):
    tmp_cache.put(SAMPLE_PARAMS, SAMPLE_DATA)
    result = tmp_cache.get(SAMPLE_PARAMS)
    assert result["ai_explanation"] == "This is a test explanation."
    assert result["r_code"] == "t.test(outcome ~ group, data = df)"
    assert result["python_code"] == "stats.ttest_ind(a, b)"
    assert result["interpretation"] == "Report t(df) = X.XX, p = .XXX"


def test_hash_is_stable_for_same_params(tmp_cache):
    h1 = tmp_cache.hash_for(SAMPLE_PARAMS)
    h2 = tmp_cache.hash_for(SAMPLE_PARAMS)
    assert h1 == h2


def test_hash_differs_for_different_params(tmp_cache):
    params_a = {**SAMPLE_PARAMS}
    params_b = {**SAMPLE_PARAMS, "paired": True}
    assert tmp_cache.hash_for(params_a) != tmp_cache.hash_for(params_b)


def test_hash_order_independent(tmp_cache):
    params_ordered = {"a": 1, "b": 2}
    params_reversed = {"b": 2, "a": 1}
    assert tmp_cache.hash_for(params_ordered) == tmp_cache.hash_for(params_reversed)


def test_cache_upsert_replaces_existing(tmp_cache):
    tmp_cache.put(SAMPLE_PARAMS, SAMPLE_DATA)
    new_data = {**SAMPLE_DATA, "ai_explanation": "Updated explanation."}
    tmp_cache.put(SAMPLE_PARAMS, new_data)
    result = tmp_cache.get(SAMPLE_PARAMS)
    assert result["ai_explanation"] == "Updated explanation."


def test_cache_different_params_stored_separately(tmp_cache):
    params_b = {**SAMPLE_PARAMS, "num_groups": 3}
    data_b = {**SAMPLE_DATA, "test_name": "One-Way ANOVA"}
    tmp_cache.put(SAMPLE_PARAMS, SAMPLE_DATA)
    tmp_cache.put(params_b, data_b)

    result_a = tmp_cache.get(SAMPLE_PARAMS)
    result_b = tmp_cache.get(params_b)

    assert result_a["test_name"] == "Independent Samples t-test"
    assert result_b["test_name"] == "One-Way ANOVA"


def test_cache_persists_across_instances(tmp_path):
    db_path = tmp_path / "persist.db"
    cache1 = AdviceCache(db_path)
    cache1.put(SAMPLE_PARAMS, SAMPLE_DATA)

    cache2 = AdviceCache(db_path)
    result = cache2.get(SAMPLE_PARAMS)
    assert result is not None
    assert result["test_name"] == "Independent Samples t-test"
