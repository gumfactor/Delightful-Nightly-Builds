from src.chunking import split_into_chunks


def test_splits_on_blank_line():
    text = "First paragraph text.\n\nSecond paragraph text."
    assert split_into_chunks(text) == ["First paragraph text.", "Second paragraph text."]


def test_single_paragraph_no_blank_line():
    text = "Just one paragraph with no separator."
    assert split_into_chunks(text) == ["Just one paragraph with no separator."]


def test_multiple_blank_lines_treated_as_one_separator():
    text = "Alpha paragraph.\n\n\n\nBeta paragraph."
    assert split_into_chunks(text) == ["Alpha paragraph.", "Beta paragraph."]


def test_blank_line_with_whitespace_still_separates():
    text = "Alpha paragraph.\n   \nBeta paragraph."
    assert split_into_chunks(text) == ["Alpha paragraph.", "Beta paragraph."]


def test_trailing_and_leading_whitespace_stripped():
    text = "\n\n   Padded paragraph.   \n\n"
    assert split_into_chunks(text) == ["Padded paragraph."]


def test_empty_string_returns_empty_list():
    assert split_into_chunks("") == []


def test_whitespace_only_string_returns_empty_list():
    assert split_into_chunks("   \n\n   \n  ") == []


def test_preserves_internal_newlines_within_paragraph():
    text = "Line one of paragraph.\nLine two of paragraph."
    chunks = split_into_chunks(text)
    assert chunks == ["Line one of paragraph.\nLine two of paragraph."]


def test_three_paragraphs_all_recovered():
    text = "One.\n\nTwo.\n\nThree."
    assert split_into_chunks(text) == ["One.", "Two.", "Three."]
