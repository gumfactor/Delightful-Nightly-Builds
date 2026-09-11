import math

import pytest

from src.similarity import (
    build_tfidf_vectors,
    cosine_similarity,
    find_similar_pairs,
    tokenize,
)


def test_tokenize_lowercases_and_strips_punctuation():
    tokens = tokenize("Hello, World! It's Fine.")
    assert tokens == ["hello", "world", "it's", "fine"]


def test_identical_documents_have_similarity_one():
    docs = ["the cat sat on the mat", "the cat sat on the mat"]
    vectors = build_tfidf_vectors(docs)
    score = cosine_similarity(vectors[0], vectors[1])
    assert score == pytest.approx(1.0, abs=1e-9)


def test_disjoint_vocabularies_have_similarity_zero():
    docs = ["apples oranges bananas", "quantum entropy lattice"]
    vectors = build_tfidf_vectors(docs)
    score = cosine_similarity(vectors[0], vectors[1])
    assert score == 0.0


def test_partial_overlap_matches_independent_reference_implementation():
    doc_a = "cat dog bird"
    doc_b = "cat fish bird"

    # Independent reference implementation, computed directly with plain
    # loops (not calling into src.similarity at all), to cross-check the
    # shipped TF-IDF + cosine implementation rather than just testing it
    # against itself.
    docs = [doc_a, doc_b]
    tokenized = [d.split() for d in docs]
    n = len(tokenized)
    df: dict[str, int] = {}
    for toks in tokenized:
        for term in set(toks):
            df[term] = df.get(term, 0) + 1

    def ref_vector(toks):
        tf = {t: toks.count(t) / len(toks) for t in set(toks)}
        return {t: tf[t] * (math.log((1 + n) / (1 + df[t])) + 1) for t in tf}

    vec_a = ref_vector(tokenized[0])
    vec_b = ref_vector(tokenized[1])
    shared = set(vec_a) & set(vec_b)
    dot = sum(vec_a[t] * vec_b[t] for t in shared)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    expected = dot / (norm_a * norm_b)

    vectors = build_tfidf_vectors(docs)
    actual = cosine_similarity(vectors[0], vectors[1])

    assert actual == pytest.approx(expected, abs=1e-9)
    # Sanity bound: shares 2 of 3 tokens, so similarity should be
    # meaningfully between 0 and 1, not at either extreme.
    assert 0.3 < actual < 0.8


def test_find_similar_pairs_threshold_filtering():
    docs = [
        "the quick brown fox jumps over the lazy dog",
        "the quick brown fox jumps over the lazy dog",  # identical -> flagged
        "completely unrelated content about neuroscience research methods",
    ]
    pairs = find_similar_pairs(docs, threshold=0.75)
    assert len(pairs) == 1
    assert pairs[0].index_a == 0
    assert pairs[0].index_b == 1
    assert pairs[0].score >= 0.75


def test_find_similar_pairs_empty_batch_returns_empty():
    assert find_similar_pairs([], threshold=0.75) == []


def test_find_similar_pairs_single_document_returns_empty():
    assert find_similar_pairs(["only one document here"], threshold=0.75) == []


def test_cosine_similarity_empty_vector_returns_zero():
    assert cosine_similarity({}, {"a": 1.0}) == 0.0
    assert cosine_similarity({"a": 1.0}, {}) == 0.0


def test_find_similar_pairs_sorted_highest_first():
    docs = [
        "alpha beta gamma delta epsilon",
        "alpha beta gamma delta zeta",
        "alpha beta gamma delta epsilon",
    ]
    pairs = find_similar_pairs(docs, threshold=0.5)
    scores = [p.score for p in pairs]
    assert scores == sorted(scores, reverse=True)
