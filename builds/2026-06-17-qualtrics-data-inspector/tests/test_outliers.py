"""Tests for src/outliers.py — Z-score and IQR outlier detection."""

import pytest
from src.outliers import zscore_outliers, iqr_outliers, respondent_outlier_counts


def _rows(data):
    """Build minimal row dicts from {id: value} data."""
    return [{"ResponseId": rid, "Q1": str(v)} for rid, v in data.items()]


CLEAN_ROWS = [
    {"ResponseId": "R01", "Q1": "3", "Q2": "4"},
    {"ResponseId": "R02", "Q1": "4", "Q2": "3"},
    {"ResponseId": "R03", "Q1": "3", "Q2": "4"},
    {"ResponseId": "R04", "Q1": "5", "Q2": "5"},
    {"ResponseId": "R05", "Q1": "4", "Q2": "3"},
    {"ResponseId": "R06", "Q1": "3", "Q2": "4"},
    {"ResponseId": "R07", "Q1": "4", "Q2": "3"},
    {"ResponseId": "R08", "Q1": "3", "Q2": "4"},
    {"ResponseId": "R09", "Q1": "4", "Q2": "5"},
    {"ResponseId": "R10", "Q1": "3", "Q2": "3"},
]

ROWS_WITH_OUTLIER = CLEAN_ROWS + [{"ResponseId": "R_OUT", "Q1": "100", "Q2": "4"}]


class TestZscoreOutliers:
    def test_detects_extreme_outlier(self):
        result = zscore_outliers(ROWS_WITH_OUTLIER, ["Q1"], threshold=3.0)
        assert "Q1" in result
        assert "R_OUT" in result["Q1"]

    def test_z_score_is_positive(self):
        result = zscore_outliers(ROWS_WITH_OUTLIER, ["Q1"], threshold=3.0)
        assert result["Q1"]["R_OUT"] > 3.0

    def test_clean_data_no_outliers(self):
        result = zscore_outliers(CLEAN_ROWS, ["Q1"], threshold=3.0)
        assert "Q1" not in result

    def test_multiple_columns_checked(self):
        rows = [{"ResponseId": f"R{i}", "Q1": "3", "Q2": "3"} for i in range(10)]
        rows.append({"ResponseId": "ROUT", "Q1": "100", "Q2": "100"})
        result = zscore_outliers(rows, ["Q1", "Q2"], threshold=3.0)
        assert "Q1" in result
        assert "Q2" in result

    def test_zero_variance_column_skipped(self):
        rows = [{"ResponseId": f"R{i}", "Q1": "5"} for i in range(10)]
        result = zscore_outliers(rows, ["Q1"], threshold=3.0)
        assert "Q1" not in result

    def test_non_numeric_values_skipped(self):
        rows = CLEAN_ROWS + [{"ResponseId": "R_TEXT", "Q1": "text"}]
        result = zscore_outliers(rows, ["Q1"], threshold=3.0)
        # No crash; text row should be ignored
        assert isinstance(result, dict)

    def test_fewer_than_3_values_skipped(self):
        rows = [{"ResponseId": "R1", "Q1": "1"}, {"ResponseId": "R2", "Q1": "10"}]
        result = zscore_outliers(rows, ["Q1"], threshold=3.0)
        assert "Q1" not in result


class TestIqrOutliers:
    def test_detects_extreme_outlier(self):
        result = iqr_outliers(ROWS_WITH_OUTLIER, ["Q1"])
        assert "Q1" in result
        assert "R_OUT" in result["Q1"]

    def test_clean_data_no_outliers(self):
        result = iqr_outliers(CLEAN_ROWS, ["Q1"])
        assert "Q1" not in result

    def test_outlier_value_returned(self):
        result = iqr_outliers(ROWS_WITH_OUTLIER, ["Q1"])
        assert result["Q1"]["R_OUT"] == 100.0

    def test_zero_iqr_column_skipped(self):
        rows = [{"ResponseId": f"R{i}", "Q1": "5"} for i in range(10)]
        result = iqr_outliers(rows, ["Q1"])
        assert "Q1" not in result

    def test_fewer_than_4_skipped(self):
        rows = [{"ResponseId": f"R{i}", "Q1": str(i)} for i in range(3)]
        result = iqr_outliers(rows, ["Q1"])
        assert "Q1" not in result


class TestRespondentOutlierCounts:
    def test_single_column_outlier(self):
        z = {"Q1": {"R_OUT": 4.5}}
        iq = {}
        counts = respondent_outlier_counts(z, iq)
        assert counts["R_OUT"] == 1

    def test_two_column_outlier(self):
        z = {"Q1": {"R_OUT": 4.5}, "Q2": {"R_OUT": 5.0}}
        iq = {}
        counts = respondent_outlier_counts(z, iq)
        assert counts["R_OUT"] == 2

    def test_same_column_both_methods_counts_once(self):
        z = {"Q1": {"R_OUT": 4.5}}
        iq = {"Q1": {"R_OUT": 100.0}}
        counts = respondent_outlier_counts(z, iq)
        assert counts["R_OUT"] == 1  # same column, not double-counted

    def test_empty_inputs(self):
        counts = respondent_outlier_counts({}, {})
        assert counts == {}

    def test_multiple_respondents(self):
        z = {"Q1": {"R1": 3.5, "R2": 4.0}}
        iq = {}
        counts = respondent_outlier_counts(z, iq)
        assert counts["R1"] == 1
        assert counts["R2"] == 1
