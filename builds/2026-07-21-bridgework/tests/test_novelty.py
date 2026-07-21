import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import novelty


def test_jaccard_identical_texts_is_one():
    assert novelty.jaccard_similarity("the cat sat", "the cat sat") == 1.0


def test_jaccard_disjoint_texts_is_zero():
    assert novelty.jaccard_similarity("apples oranges", "trucks bicycles") == 0.0


def test_jaccard_partial_overlap_is_computed_correctly():
    # {a,b,c} vs {b,c,d} -> intersection 2, union 4 -> 0.5
    assert novelty.jaccard_similarity("a b c", "b c d") == 0.5


def test_jaccard_empty_text_is_zero():
    assert novelty.jaccard_similarity("", "something") == 0.0
    assert novelty.jaccard_similarity("something", "") == 0.0
    assert novelty.jaccard_similarity("", "") == 0.0


def test_jaccard_case_insensitive():
    assert novelty.jaccard_similarity("Hello World", "hello world") == 1.0


def test_max_overlap_empty_corpus_is_zero():
    assert novelty.max_overlap("some text here", []) == 0.0


def test_max_overlap_picks_highest_similarity():
    text = "the storm builds and discharges"
    existing = ["completely unrelated sentence", "the storm builds and discharges exactly"]
    result = novelty.max_overlap(text, existing)
    assert result > 0.5


def test_novelty_score_decreases_with_higher_usage_count():
    low_usage = novelty.novelty_score(usage_count=0, overlap=0.0)
    high_usage = novelty.novelty_score(usage_count=5, overlap=0.0)
    assert low_usage > high_usage


def test_novelty_score_decreases_with_higher_overlap():
    low_overlap = novelty.novelty_score(usage_count=0, overlap=0.1)
    high_overlap = novelty.novelty_score(usage_count=0, overlap=0.9)
    assert low_overlap > high_overlap


def test_novelty_score_is_one_for_first_use_and_no_overlap():
    assert novelty.novelty_score(usage_count=0, overlap=0.0) == 1.0


def test_novelty_score_rejects_negative_usage_count():
    with pytest.raises(ValueError):
        novelty.novelty_score(usage_count=-1, overlap=0.0)


def test_novelty_score_rejects_out_of_range_overlap():
    with pytest.raises(ValueError):
        novelty.novelty_score(usage_count=0, overlap=1.5)
    with pytest.raises(ValueError):
        novelty.novelty_score(usage_count=0, overlap=-0.1)


def test_rank_triples_by_usage_sorts_ascending():
    class FakeItem:
        def __init__(self, id_):
            self.id = id_

    c1, c2 = FakeItem("c1"), FakeItem("c2")
    d1 = FakeItem("d1")
    triples = [(c1, d1, "public_talk"), (c2, d1, "public_talk")]
    usage_counts = {("c1", "d1", "public_talk"): 3, ("c2", "d1", "public_talk"): 0}
    ranked = novelty.rank_triples_by_usage(triples, usage_counts)
    assert ranked[0][0].id == "c2"
    assert ranked[1][0].id == "c1"


def test_rank_triples_by_usage_defaults_missing_to_zero():
    class FakeItem:
        def __init__(self, id_):
            self.id = id_

    c1 = FakeItem("c1")
    d1 = FakeItem("d1")
    triples = [(c1, d1, "book_chapter")]
    ranked = novelty.rank_triples_by_usage(triples, {})
    assert ranked == triples
