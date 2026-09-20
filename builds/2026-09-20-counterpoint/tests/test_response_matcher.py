from src.parser import Comment
from src.response_matcher import match


def make_comments(*ids):
    comments = []
    for comment_id in ids:
        reviewer, comment_num = comment_id[1:].split("C")
        comments.append(Comment(int(reviewer), int(comment_num), f"text for {comment_id}"))
    return comments


def test_all_responses_present_no_missing():
    comments = make_comments("R1C1", "R1C2", "R2C1")
    responses = {"R1C1": "a", "R1C2": "b", "R2C1": "c"}
    report = match(comments, responses)
    assert report.total == 3
    assert report.addressed == 3
    assert report.missing == []
    assert report.orphaned == []
    assert report.is_complete


def test_missing_response_flagged():
    comments = make_comments("R1C1", "R1C2")
    responses = {"R1C1": "a"}
    report = match(comments, responses)
    assert report.missing == ["R1C2"]
    assert report.addressed == 1
    assert not report.is_complete


def test_orphaned_response_flagged_not_fatal():
    comments = make_comments("R1C1")
    responses = {"R1C1": "a", "R2C5": "stale key from a renumbering mistake"}
    report = match(comments, responses)
    assert report.orphaned == ["R2C5"]
    assert report.missing == []
    assert report.is_complete  # orphaned keys don't block completeness


def test_missing_ids_sorted_numerically_not_lexicographically():
    comments = make_comments("R2C1", "R10C1", "R1C1")
    responses = {}
    report = match(comments, responses)
    # Lexicographic sort would put R10C1 before R2C1; numeric sort must not.
    assert report.missing == ["R1C1", "R2C1", "R10C1"]


def test_percentage_zero_comments():
    report = match([], {})
    assert report.total == 0
    assert report.percentage == 0
    assert report.is_complete


def test_percentage_partial_rounds_correctly():
    comments = make_comments("R1C1", "R1C2", "R1C3")
    responses = {"R1C1": "a"}
    report = match(comments, responses)
    assert report.percentage == 33  # 1/3 rounded


def test_percentage_full_is_100():
    comments = make_comments("R1C1", "R1C2")
    responses = {"R1C1": "a", "R1C2": "b"}
    report = match(comments, responses)
    assert report.percentage == 100
