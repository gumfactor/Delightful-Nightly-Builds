"""Tests for src/attention.py — attention check detection and scoring."""

import pytest
from src.attention import (
    detect_attention_check_columns,
    _extract_expected_from_text,
    score_attention_checks,
    attention_failed_ids,
)


# ── Stubs ─────────────────────────────────────────────────────────────────────

class _Col:
    def __init__(self, name, question_text=""):
        self.name = name
        self.question_text = question_text


class _Survey:
    def __init__(self, columns, rows):
        self.columns = columns
        self.rows = rows


# ── _extract_expected_from_text ───────────────────────────────────────────────

class TestExtractExpectedFromText:
    def test_please_select_single_quotes(self):
        result = _extract_expected_from_text("Please select 'Strongly Agree' for this item")
        assert result == "Strongly Agree"

    def test_please_choose_number(self):
        result = _extract_expected_from_text("Please choose 4 to show you are paying attention")
        assert result == "4"

    def test_please_answer_double_quotes(self):
        result = _extract_expected_from_text('Please answer "Disagree" for quality control')
        assert result == "Disagree"

    def test_select_with_value(self):
        result = _extract_expected_from_text("select 'Yes'")
        assert result == "Yes"

    def test_choose_with_value(self):
        result = _extract_expected_from_text("choose 'No'")
        assert result == "No"

    def test_none_on_empty_string(self):
        assert _extract_expected_from_text("") is None

    def test_none_on_no_pattern(self):
        assert _extract_expected_from_text("What is your age?") is None

    def test_case_insensitive(self):
        result = _extract_expected_from_text("PLEASE SELECT '3'")
        assert result == "3"


# ── detect_attention_check_columns ───────────────────────────────────────────

class TestDetectAttentionCheckColumns:
    def test_detects_by_attn_hint(self):
        cols = [_Col("Q_attn_1"), _Col("Q1")]
        survey = _Survey(cols, [])
        specs = detect_attention_check_columns(survey)
        names = [s["col"] for s in specs]
        assert "Q_attn_1" in names
        assert "Q1" not in names

    def test_detects_by_attention_hint(self):
        cols = [_Col("attention_check"), _Col("Q1")]
        survey = _Survey(cols, [])
        specs = detect_attention_check_columns(survey)
        assert any(s["col"] == "attention_check" for s in specs)

    def test_explicit_expected_answer_overrides(self):
        cols = [_Col("ATTN1")]
        survey = _Survey(cols, [])
        specs = detect_attention_check_columns(survey, expected_answers={"ATTN1": "3"})
        assert specs[0]["expected"] == "3"

    def test_extracts_expected_from_question_text(self):
        col = _Col("trap_q", "Please select '5' to confirm you are human")
        survey = _Survey([col], [])
        specs = detect_attention_check_columns(survey)
        assert specs[0]["expected"] == "5"

    def test_no_matches_returns_empty(self):
        cols = [_Col("Q1"), _Col("Age"), _Col("Gender")]
        survey = _Survey(cols, [])
        assert detect_attention_check_columns(survey) == []

    def test_explicit_column_not_in_hint_set_is_included(self):
        cols = [_Col("SomeUnusualColumn")]
        survey = _Survey(cols, [])
        specs = detect_attention_check_columns(survey, expected_answers={"SomeUnusualColumn": "Yes"})
        assert len(specs) == 1
        assert specs[0]["expected"] == "Yes"

    def test_no_duplicates_when_hint_and_explicit(self):
        cols = [_Col("attention_check")]
        survey = _Survey(cols, [])
        specs = detect_attention_check_columns(survey, expected_answers={"attention_check": "5"})
        assert len(specs) == 1

    def test_hint_keywords_catch_bot_and_trap(self):
        cols = [_Col("bot_trap"), _Col("vigilance_q"), _Col("unrelated")]
        survey = _Survey(cols, [])
        specs = detect_attention_check_columns(survey)
        names = [s["col"] for s in specs]
        assert "bot_trap" in names
        assert "vigilance_q" in names
        assert "unrelated" not in names

    def test_hint_keywords_catch_infreq_and_catch(self):
        cols = [_Col("catch_item"), _Col("infreq_1")]
        survey = _Survey(cols, [])
        specs = detect_attention_check_columns(survey)
        names = [s["col"] for s in specs]
        assert "catch_item" in names
        assert "infreq_1" in names

    def test_unknown_expected_when_no_text(self):
        col = _Col("attn_q", "")
        survey = _Survey([col], [])
        specs = detect_attention_check_columns(survey)
        assert specs[0]["expected"] is None


# ── score_attention_checks ────────────────────────────────────────────────────

class TestScoreAttentionChecks:
    def _make_survey(self, col_name, values):
        col = _Col(col_name)
        rows = [{col_name: v, "ResponseId": str(i)} for i, v in enumerate(values)]
        return _Survey([col], rows)

    def test_perfect_pass_rate(self):
        survey = self._make_survey("ATTN", ["5", "5", "5"])
        specs = [{"col": "ATTN", "expected": "5", "question_text": ""}]
        result = score_attention_checks(survey, specs)
        assert result["ATTN"]["pass_rate"] == 1.0
        assert result["ATTN"]["failed_ids"] == []

    def test_partial_pass_rate(self):
        survey = self._make_survey("ATTN", ["5", "3", "5", "2"])
        specs = [{"col": "ATTN", "expected": "5", "question_text": ""}]
        result = score_attention_checks(survey, specs)
        assert result["ATTN"]["pass_rate"] == 0.5
        assert len(result["ATTN"]["failed_ids"]) == 2

    def test_unknown_expected_returns_none_pass_rate(self):
        survey = self._make_survey("ATTN", ["5", "3"])
        specs = [{"col": "ATTN", "expected": None, "question_text": ""}]
        result = score_attention_checks(survey, specs)
        assert result["ATTN"]["pass_rate"] is None

    def test_case_insensitive_comparison(self):
        survey = self._make_survey("ATTN", ["Strongly Agree", "strongly agree", "STRONGLY AGREE"])
        specs = [{"col": "ATTN", "expected": "Strongly Agree", "question_text": ""}]
        result = score_attention_checks(survey, specs)
        assert result["ATTN"]["pass_rate"] == 1.0

    def test_whitespace_stripped(self):
        survey = self._make_survey("ATTN", ["  5 ", "5", " 5"])
        specs = [{"col": "ATTN", "expected": "5", "question_text": ""}]
        result = score_attention_checks(survey, specs)
        assert result["ATTN"]["pass_rate"] == 1.0

    def test_n_checked_excludes_none(self):
        col = _Col("ATTN")
        rows = [
            {"ATTN": "5", "ResponseId": "R1"},
            {"ATTN": None, "ResponseId": "R2"},
            {"ATTN": "5", "ResponseId": "R3"},
        ]
        survey = _Survey([col], rows)
        specs = [{"col": "ATTN", "expected": "5", "question_text": ""}]
        result = score_attention_checks(survey, specs)
        assert result["ATTN"]["n_checked"] == 2

    def test_empty_specs_returns_empty_dict(self):
        survey = self._make_survey("ATTN", ["5"])
        assert score_attention_checks(survey, []) == {}

    def test_failed_ids_are_response_ids(self):
        col = _Col("ATTN")
        rows = [
            {"ATTN": "5", "ResponseId": "PASS1"},
            {"ATTN": "3", "ResponseId": "FAIL1"},
            {"ATTN": "4", "ResponseId": "FAIL2"},
        ]
        survey = _Survey([col], rows)
        specs = [{"col": "ATTN", "expected": "5", "question_text": ""}]
        result = score_attention_checks(survey, specs)
        assert "FAIL1" in result["ATTN"]["failed_ids"]
        assert "FAIL2" in result["ATTN"]["failed_ids"]
        assert "PASS1" not in result["ATTN"]["failed_ids"]

    def test_zero_respondents_answered(self):
        col = _Col("ATTN")
        survey = _Survey([col], [{"ATTN": None, "ResponseId": "R1"}])
        specs = [{"col": "ATTN", "expected": "5", "question_text": ""}]
        result = score_attention_checks(survey, specs)
        assert result["ATTN"]["n_checked"] == 0
        assert result["ATTN"]["pass_rate"] is None


# ── attention_failed_ids ──────────────────────────────────────────────────────

class TestAttentionFailedIds:
    def test_counts_failures_across_checks(self):
        results = {
            "ATTN1": {"failed_ids": ["R1", "R2"]},
            "ATTN2": {"failed_ids": ["R1", "R3"]},
        }
        counts = attention_failed_ids(results)
        assert counts["R1"] == 2
        assert counts["R2"] == 1
        assert counts["R3"] == 1

    def test_empty_results_returns_empty(self):
        assert attention_failed_ids({}) == {}

    def test_all_pass_returns_empty(self):
        results = {"ATTN1": {"failed_ids": []}}
        assert attention_failed_ids(results) == {}
