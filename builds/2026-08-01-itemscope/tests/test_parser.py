import pytest

from itemscope.parser import (
    ItemScopeParseError,
    load_answer_key,
    load_response_csv,
    score_matrix,
)


def test_binary_csv_parses_with_id_column(tmp_path):
    csv_path = tmp_path / "responses.csv"
    csv_path.write_text("student_id,item_1,item_2\nS001,1,0\nS002,0,1\n")

    matrix = load_response_csv(str(csv_path))

    assert matrix.student_ids == ["S001", "S002"]
    assert matrix.item_ids == ["item_1", "item_2"]
    assert matrix.raw == [["1", "0"], ["0", "1"]]


def test_binary_csv_scores_true_false_tokens(tmp_path):
    csv_path = tmp_path / "responses.csv"
    csv_path.write_text("student_id,item_1,item_2\nS001,true,False\nS002,correct,incorrect\n")

    matrix = load_response_csv(str(csv_path))
    scored = score_matrix(matrix, answer_key=None)

    assert scored.scores == [[1, 0], [1, 0]]


def test_no_id_column_generates_synthetic_ids(tmp_path):
    csv_path = tmp_path / "responses.csv"
    # both columns look like item responses (0/1) so no id column is detected
    csv_path.write_text("item_1,item_2\n1,0\n0,1\n")

    matrix = load_response_csv(str(csv_path))

    assert matrix.student_ids == ["student_1", "student_2"]
    assert matrix.item_ids == ["item_1", "item_2"]


def test_explicit_student_id_col(tmp_path):
    csv_path = tmp_path / "responses.csv"
    csv_path.write_text("item_1,student_id,item_2\n1,S001,0\n0,S002,1\n")

    matrix = load_response_csv(str(csv_path), student_id_col="student_id")

    assert matrix.student_ids == ["S001", "S002"]
    assert matrix.item_ids == ["item_1", "item_2"]


def test_missing_explicit_student_id_col_raises(tmp_path):
    csv_path = tmp_path / "responses.csv"
    csv_path.write_text("item_1,item_2\n1,0\n")

    with pytest.raises(ItemScopeParseError, match="not found in header"):
        load_response_csv(str(csv_path), student_id_col="nope")


def test_empty_file_raises(tmp_path):
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("")

    with pytest.raises(ItemScopeParseError, match="empty"):
        load_response_csv(str(csv_path))


def test_header_only_file_raises(tmp_path):
    csv_path = tmp_path / "header_only.csv"
    csv_path.write_text("student_id,item_1\n")

    with pytest.raises(ItemScopeParseError, match="no data rows"):
        load_response_csv(str(csv_path))


def test_missing_file_raises(tmp_path):
    with pytest.raises(ItemScopeParseError, match="not found"):
        load_response_csv(str(tmp_path / "does_not_exist.csv"))


def test_mismatched_column_count_raises(tmp_path):
    csv_path = tmp_path / "responses.csv"
    csv_path.write_text("student_id,item_1,item_2\nS001,1,0\nS002,1\n")

    with pytest.raises(ItemScopeParseError, match="columns, expected"):
        load_response_csv(str(csv_path))


def test_raw_option_scoring_with_answer_key(tmp_path):
    responses_path = tmp_path / "responses.csv"
    responses_path.write_text("student_id,q1,q2\nS001,B,C\nS002,A,C\n")
    key_path = tmp_path / "key.csv"
    key_path.write_text("item,answer\nq1,B\nq2,C\n")

    matrix = load_response_csv(str(responses_path))
    key = load_answer_key(str(key_path))
    scored = score_matrix(matrix, key)

    assert scored.scores == [[1, 1], [0, 1]]
    assert scored.raw_options == [["B", "C"], ["A", "C"]]


def test_answer_key_missing_item_raises(tmp_path):
    responses_path = tmp_path / "responses.csv"
    responses_path.write_text("student_id,q1,q2\nS001,B,C\n")
    key_path = tmp_path / "key.csv"
    key_path.write_text("item,answer\nq1,B\n")

    matrix = load_response_csv(str(responses_path))
    key = load_answer_key(str(key_path))

    with pytest.raises(ItemScopeParseError, match="missing entries"):
        score_matrix(matrix, key)


def test_unrecognized_binary_token_without_key_raises(tmp_path):
    csv_path = tmp_path / "responses.csv"
    csv_path.write_text("student_id,q1\nS001,B\n")

    matrix = load_response_csv(str(csv_path))

    with pytest.raises(ItemScopeParseError, match="not a recognized binary value"):
        score_matrix(matrix, answer_key=None)


def test_answer_key_without_header_row(tmp_path):
    key_path = tmp_path / "key.csv"
    key_path.write_text("q1,B\nq2,C\n")

    key = load_answer_key(str(key_path))

    assert key == {"q1": "B", "q2": "C"}
