import json

from itemscope.parser import ScoredMatrix
from itemscope.report import render_html, render_json, render_text, to_dict
from itemscope.stats import analyze


def _matrix_with_item_id(item_id: str) -> ScoredMatrix:
    n = 10
    scores = [[1 if i >= 3 else 0] for i in range(n)]
    return ScoredMatrix(
        student_ids=[f"S{i}" for i in range(n)],
        item_ids=[item_id],
        scores=scores,
        raw_options=[[None] for _ in range(n)],
        answer_key=None,
    )


def test_html_report_escapes_script_injection_in_item_id():
    malicious_id = "<script>alert(1)</script>"
    stats = analyze(_matrix_with_item_id(malicious_id))

    output = render_html(stats)

    # the raw closing tag must never appear unescaped inside the HTML,
    # otherwise it would break out of the surrounding <script> block
    assert "</script>alert(1)" not in output
    # the JSON payload should still contain the item id, with its closing
    # </script> substring escaped so it can't terminate the script block
    assert "<script>alert(1)<\\/script>" in output


def test_json_report_round_trips_and_has_expected_keys():
    stats = analyze(_matrix_with_item_id("item_1"))
    output = render_json(stats)

    data = json.loads(output)
    assert data["n_students"] == 10
    assert data["n_items"] == 1
    assert data["items"][0]["item_id"] == "item_1"
    assert "p_value" in data["items"][0]
    assert "discrimination" in data["items"][0]


def test_to_dict_rounds_floats():
    stats = analyze(_matrix_with_item_id("item_1"))
    data = to_dict(stats)
    assert isinstance(data["mean_score"], float)


def test_text_report_lists_flagged_items():
    # item scored 1 for everyone -> zero variance, too_easy
    n = 10
    scores = [[1] for _ in range(n)]
    matrix = ScoredMatrix(
        student_ids=[f"S{i}" for i in range(n)],
        item_ids=["always_right"],
        scores=scores,
        raw_options=[[None] for _ in range(n)],
        answer_key=None,
    )
    stats = analyze(matrix)

    output = render_text(stats)

    assert "Flagged items" in output
    assert "always_right" in output


def test_text_report_no_flags_message():
    # a well-behaved discriminating item, difficulty in the middle
    n = 20
    scores = [[1 if i >= 10 else 0] for i in range(n)]
    matrix = ScoredMatrix(
        student_ids=[f"S{i}" for i in range(n)],
        item_ids=["good_item"],
        scores=scores,
        raw_options=[[None] for _ in range(n)],
        answer_key=None,
    )
    stats = analyze(matrix)

    output = render_text(stats)

    assert "No items flagged." in output
