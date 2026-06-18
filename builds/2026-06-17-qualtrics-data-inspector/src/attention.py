"""Attention check column detection and pass/fail scoring."""

import re
from typing import Optional

from src.quality import _get_response_id

# Column name fragments that suggest an attention check item
_ATTENTION_HINTS = frozenset({
    "attn", "attention", "catch", "check", "manipulation",
    "instructed", "infreq", "bot", "trap", "vigilance",
})


def detect_attention_check_columns(survey, expected_answers: Optional[dict] = None) -> list:
    """
    Detect attention check columns and resolve expected answers where possible.

    Detection strategy:
    1. If expected_answers dict provided, include any column explicitly listed.
    2. Also include columns whose name contains a known hint keyword.
    3. For each included column, try to parse the expected answer from the
       Qualtrics question text (matches "please select X" patterns).

    Returns a list of dicts:
        [{'col': str, 'question_text': str, 'expected': str|None}]
    """
    specs = []
    already_added: set = set()
    expected_answers = expected_answers or {}

    for col_obj in survey.columns:
        col = col_obj.name
        qt = col_obj.question_text or ""
        name_lower = col.lower()

        is_hint = any(hint in name_lower for hint in _ATTENTION_HINTS)
        is_explicit = col in expected_answers

        if not (is_hint or is_explicit):
            continue
        if col in already_added:
            continue

        if is_explicit:
            expected = str(expected_answers[col])
        else:
            expected = _extract_expected_from_text(qt)

        specs.append({"col": col, "question_text": qt, "expected": expected})
        already_added.add(col)

    return specs


def _extract_expected_from_text(text: str) -> Optional[str]:
    """
    Try to extract the expected response value from Qualtrics question text.

    Handles patterns like:
    - Please select 'Strongly Agree' for this item
    - Please choose 4 to show you are paying attention
    - Please answer "Disagree" for quality control purposes
    """
    if not text:
        return None

    # Triple-quoted raw strings avoid all quoting ambiguity
    patterns = [
        r"""please\s+(?:select|choose|answer|respond\s+with)\s+['"]([^'".,;]+)['"]""",
        r"""please\s+(?:select|choose|answer)\s+(\d+)""",
        r"""select\s+['"]([^'"]+)['"]""",
        r"""choose\s+['"]([^'"]+)['"]""",
    ]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def score_attention_checks(survey, specs: list) -> dict:
    """
    Score each attention check column.

    For columns with a known expected answer, computes pass/fail per respondent
    using case-insensitive string matching with whitespace stripping.

    Returns:
    {
        col_name: {
            'expected': str|None,
            'pass_rate': float|None,   # None if expected answer unknown
            'n_checked': int,          # respondents who answered this item
            'failed_ids': list,        # IDs of respondents who failed
            'question_text': str,
        }
    }
    """
    results: dict = {}

    for spec in specs:
        col = spec["col"]
        expected = spec["expected"]
        qt = spec.get("question_text", "")

        answered_rows = [(row, row.get(col)) for row in survey.rows if row.get(col) is not None]
        n_checked = len(answered_rows)

        if expected is None or n_checked == 0:
            results[col] = {
                "expected": None,
                "pass_rate": None,
                "n_checked": n_checked,
                "failed_ids": [],
                "question_text": qt,
            }
            continue

        expected_norm = expected.strip().lower()
        failed_ids = []
        for row, val in answered_rows:
            if str(val).strip().lower() != expected_norm:
                failed_ids.append(_get_response_id(row))

        pass_rate = (n_checked - len(failed_ids)) / n_checked

        results[col] = {
            "expected": expected,
            "pass_rate": round(pass_rate, 4),
            "n_checked": n_checked,
            "failed_ids": failed_ids,
            "question_text": qt,
        }

    return results


def attention_failed_ids(attention_results: dict) -> dict:
    """
    Return {respondent_id: n_failed} for respondents who failed >= 1 check.
    """
    counts: dict = {}
    for col, result in attention_results.items():
        for rid in result.get("failed_ids", []):
            counts[rid] = counts.get(rid, 0) + 1
    return counts
