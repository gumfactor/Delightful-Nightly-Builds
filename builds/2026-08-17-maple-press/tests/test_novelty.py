import novelty


def test_jaccard_overlap_identical_texts_is_one():
    text = "Meet Acme Bakery, a Canadian favourite."
    assert novelty.jaccard_overlap(text, text) == 1.0


def test_jaccard_overlap_disjoint_texts_is_zero():
    assert novelty.jaccard_overlap("apples oranges bananas", "trucks bicycles trains") == 0.0


def test_jaccard_overlap_both_empty_is_zero():
    assert novelty.jaccard_overlap("", "") == 0.0


def test_jaccard_overlap_hand_computed_reference():
    # tokens(a) = {meet, acme, bakery, canadian, bread, lovers}      -> 6
    # tokens(b) = {meet, acme, bakery, for, local, bread}            -> 6
    # intersection = {meet, acme, bakery, bread}                     -> 4
    # union        = {meet, acme, bakery, canadian, bread, lovers, for, local} -> 8
    # jaccard = 4 / 8 = 0.5
    text_a = "Meet Acme Bakery Canadian bread lovers"
    text_b = "Meet Acme Bakery for local bread"
    assert novelty.jaccard_overlap(text_a, text_b) == 0.5


def test_jaccard_overlap_case_and_punctuation_insensitive():
    assert novelty.jaccard_overlap("Meet Acme!", "meet acme.") == 1.0


def test_max_overlap_against_history_empty_history_is_zero():
    assert novelty.max_overlap_against_history("anything at all", []) == 0.0


def test_max_overlap_against_history_picks_highest():
    candidate = "meet acme bakery canadian bread"
    history = [
        "trucks bicycles trains",  # 0 overlap
        "meet acme bakery canadian bread",  # full overlap = 1.0
        "meet acme",  # partial overlap
    ]
    assert novelty.max_overlap_against_history(candidate, history) == 1.0
