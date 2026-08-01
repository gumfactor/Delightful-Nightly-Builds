import statistics

import pytest

from itemscope.parser import ScoredMatrix
from itemscope.stats import (
    NON_FUNCTIONING_LABEL,
    REVERSED_PULL_LABEL,
    _upper_lower_split,
    analyze,
    distractor_analysis,
    kr20,
    p_value,
    pearson_correlation,
    point_biserial_discrimination,
)


def test_p_value_basic():
    assert p_value([1, 1, 1, 0, 0]) == pytest.approx(0.6)


def test_p_value_empty_list():
    assert p_value([]) == 0.0


def test_pearson_correlation_zero_variance_x_returns_none():
    assert pearson_correlation([1, 1, 1, 1], [1, 2, 3, 4]) is None


def test_pearson_correlation_zero_variance_y_returns_none():
    assert pearson_correlation([1, 0, 1, 0], [5, 5, 5, 5]) is None


def test_pearson_correlation_matches_stdlib_reference():
    x = [1.0, 1.0, 1.0, 0.0, 1.0]
    y = [2.0, 1.0, 0.0, 0.0, 2.0]
    expected = statistics.correlation(x, y)
    assert pearson_correlation(x, y) == pytest.approx(expected)


def test_point_biserial_matches_stdlib_reference():
    item_column = [1, 1, 0, 0, 1]
    corrected_total = [2.0, 1.0, 0.0, 0.0, 2.0]
    expected = statistics.correlation([float(v) for v in item_column], corrected_total)
    assert point_biserial_discrimination(item_column, corrected_total) == pytest.approx(expected)


def test_point_biserial_undefined_for_zero_variance_item():
    # every student got this item correct -> zero variance -> undefined
    item_column = [1, 1, 1, 1]
    corrected_total = [3.0, 4.0, 5.0, 6.0]
    assert point_biserial_discrimination(item_column, corrected_total) is None


def test_kr20_matches_hand_computed_reference():
    # 5 students x 3 items, worked by hand in PRD/BUILD_LOG:
    # sum(p*q) = 0.64, population variance of totals = 1.36, k = 3
    # KR-20 = (3/2) * (1 - 0.64/1.36) = 0.7941176470588235
    scores = [
        [1, 1, 1],
        [1, 1, 0],
        [1, 0, 0],
        [0, 0, 0],
        [1, 1, 1],
    ]
    value, note = kr20(scores)
    assert note is None
    assert value == pytest.approx(0.7941176470588235)


def test_kr20_single_item_not_meaningful():
    scores = [[1], [0], [1], [1]]
    value, note = kr20(scores)
    assert value is None
    assert "single item" in note


def test_kr20_zero_variance_total_not_meaningful():
    scores = [[1, 1], [1, 1], [1, 1]]
    value, note = kr20(scores)
    assert value is None
    assert "identically" in note


def test_upper_lower_split_basic():
    total_scores = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    upper, lower, small_n = _upper_lower_split(total_scores)
    # 27% of 10 = 2.7 -> round to 3
    assert len(upper) == 3
    assert len(lower) == 3
    assert not small_n
    # upper indices should be the highest-scoring students
    assert set(upper) == {7, 8, 9}
    assert set(lower) == {0, 1, 2}


def test_upper_lower_split_small_class_flagged_small_n():
    total_scores = [5, 3]
    upper, lower, small_n = _upper_lower_split(total_scores)
    assert small_n is True
    assert len(upper) >= 1
    assert len(lower) >= 1


def test_distractor_analysis_flags_non_functioning_distractor():
    # indices 0,1 = lower group (choose 'A'), 2,3 = middle (choose 'C'/'D'),
    # 4,5 = upper group (choose correct 'B')
    raw_options = ["A", "A", "C", "D", "B", "B"]
    result = distractor_analysis(
        raw_options, correct_answer="B", upper_indices=[4, 5], lower_indices=[0, 1]
    )

    flag_types = {f["option"]: f["type"] for f in result["flags"]}
    assert flag_types["C"] == NON_FUNCTIONING_LABEL
    assert flag_types["D"] == NON_FUNCTIONING_LABEL
    assert "A" not in flag_types  # chosen by the lower group, not non-functioning


def test_distractor_analysis_flags_reversed_pull():
    # upper group picks the distractor 'A' more than the lower group does
    raw_options = ["B", "B", "A", "B"]
    result = distractor_analysis(
        raw_options, correct_answer="B", upper_indices=[2, 3], lower_indices=[0, 1]
    )

    flag_types = {f["option"]: f["type"] for f in result["flags"]}
    assert flag_types["A"] == REVERSED_PULL_LABEL


def test_distractor_analysis_no_flags_for_well_behaved_item():
    raw_options = ["A", "A", "B", "B"]
    result = distractor_analysis(
        raw_options, correct_answer="B", upper_indices=[2, 3], lower_indices=[0, 1]
    )
    assert result["flags"] == []


def test_analyze_flags_too_easy_and_too_hard_items():
    n = 20
    scores = []
    for i in range(n):
        row = [
            1 if i >= 1 else 0,   # item_easy: p = 19/20 = 0.95 -> not quite too easy
            1 if i >= 0 else 0,   # item_all_correct: p = 1.0 -> too easy, zero variance
            1 if i >= 19 else 0,  # item_hard: p = 1/20 = 0.05 -> too hard
        ]
        scores.append(row)
    matrix = ScoredMatrix(
        student_ids=[f"S{i}" for i in range(n)],
        item_ids=["item_easy", "item_all_correct", "item_hard"],
        scores=scores,
        raw_options=[[None, None, None] for _ in range(n)],
        answer_key=None,
    )

    result = analyze(matrix)
    by_id = {item.item_id: item for item in result.items}

    assert "too_easy" in by_id["item_all_correct"].flags
    assert by_id["item_all_correct"].discrimination is None
    assert by_id["item_all_correct"].discrimination_note == "undefined (zero variance)"
    assert "too_hard" in by_id["item_hard"].flags


def test_analyze_end_to_end_with_raw_options_produces_distractor_flags():
    key = {"q1": "B"}
    # 6 students: lower 2 choose A, middle 2 choose C/D, upper 2 choose B (correct)
    raw = ["A", "A", "C", "D", "B", "B"]
    scores = [[1 if v == "B" else 0] for v in raw]
    matrix = ScoredMatrix(
        student_ids=[f"S{i}" for i in range(6)],
        item_ids=["q1"],
        scores=scores,
        raw_options=[[v] for v in raw],
        answer_key=key,
    )

    result = analyze(matrix)
    item = result.items[0]
    assert item.distractor_analysis is not None
    flag_types = {f["option"] for f in item.distractor_analysis["flags"]}
    assert "C" in flag_types
    assert "D" in flag_types
