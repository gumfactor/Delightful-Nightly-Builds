import pytest

from src.parser import ParseError, parse_comments, parse_responses


def test_parse_basic_two_reviewers():
    text = """
Reviewer 1

1. First point about the introduction.
2. Second point about sample size.

Reviewer 2

1. A figure quality issue.
"""
    comments = parse_comments(text)
    ids = [c.id for c in comments]
    assert ids == ["R1C1", "R1C2", "R2C1"]
    assert comments[0].text == "First point about the introduction."
    assert comments[2].reviewer_num == 2
    assert comments[2].comment_num == 1


def test_parse_alternate_reviewer_header_formats():
    text = """
## Reviewer #1
1. Point one.

REVIEWER 2
1. Point two.
"""
    comments = parse_comments(text)
    assert [c.id for c in comments] == ["R1C1", "R2C1"]


def test_parse_comment_number_formats_dot_and_paren():
    text = """
Reviewer 1
1. Point using a dot.
2) Point using a parenthesis.
"""
    comments = parse_comments(text)
    assert [c.text for c in comments] == [
        "Point using a dot.",
        "Point using a parenthesis.",
    ]


def test_parse_multiline_comment_continuation():
    text = """
Reviewer 1
1. This comment spans
   multiple lines of text
   before the next one starts.
2. Second comment.
"""
    comments = parse_comments(text)
    assert comments[0].text == (
        "This comment spans\n   multiple lines of text\n   before the next one starts."
    )
    assert comments[1].text == "Second comment."


def test_parse_no_reviewer_header_fallback_single_reviewer():
    text = """
1. A single reviewer's first point, no heading given at all.
2. Their second point.
"""
    comments = parse_comments(text)
    assert [c.id for c in comments] == ["R1C1", "R1C2"]


def test_parse_raises_on_no_comments_found():
    with pytest.raises(ParseError):
        parse_comments("Just some prose with no numbered comments at all.")


def test_parse_raises_on_empty_input():
    with pytest.raises(ParseError):
        parse_comments("")


def test_parse_raises_on_duplicate_comment_id():
    text = """
Reviewer 1
1. First point.
1. Accidentally repeated number one.
"""
    with pytest.raises(ParseError):
        parse_comments(text)


def test_parse_ignores_preamble_before_first_comment():
    text = """
Dear authors, thank you for your submission. Below are our comments.

Reviewer 1
1. The actual first comment.
"""
    comments = parse_comments(text)
    assert len(comments) == 1
    assert comments[0].text == "The actual first comment."


def test_parse_responses_basic():
    text = """
[R1C1]
First response text.

[R1C2]
Second response,
spanning two lines.
"""
    responses = parse_responses(text)
    assert responses["R1C1"] == "First response text."
    assert responses["R1C2"] == "Second response,\nspanning two lines."


def test_parse_responses_key_normalization():
    text = """
[r1c1]
Lowercase key should still normalize.
"""
    responses = parse_responses(text)
    assert responses == {"R1C1": "Lowercase key should still normalize."}


def test_parse_responses_raises_on_no_keys_found():
    with pytest.raises(ParseError):
        parse_responses("No block markers here at all.")


def test_parse_responses_raises_on_duplicate_key():
    text = """
[R1C1]
First.

[R1C1]
Duplicate key for the same comment.
"""
    with pytest.raises(ParseError):
        parse_responses(text)
