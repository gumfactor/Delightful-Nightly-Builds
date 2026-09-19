from slug import slugify


def test_slugify_basic_words():
    assert slugify("stress cortisol") == "stress-cortisol"


def test_slugify_collapses_punctuation_and_case():
    assert slugify("Affective  Neuroscience!!") == "affective-neuroscience"


def test_slugify_strips_leading_trailing_hyphens():
    assert slugify("  --forensic neuroscience-- ") == "forensic-neuroscience"


def test_slugify_path_traversal_input_never_contains_slash_or_dotdot():
    result = slugify("../../etc/passwd")
    assert "/" not in result
    assert ".." not in result
    assert result == "etc-passwd"


def test_slugify_empty_or_punctuation_only_falls_back():
    assert slugify("") == "topic"
    assert slugify("!!!???") == "topic"
