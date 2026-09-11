"""From-scratch TF-IDF vectorization and cosine similarity for batch
near-duplicate detection. No third-party dependencies — pure stdlib math.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

_TOKEN_RE = re.compile(r"[a-z']+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _term_frequencies(tokens: list[str]) -> dict[str, float]:
    if not tokens:
        return {}
    counts: dict[str, int] = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    total = len(tokens)
    return {term: count / total for term, count in counts.items()}


def build_tfidf_vectors(documents: list[str]) -> list[dict[str, float]]:
    """Returns one TF-IDF weight dict per document, in the same order as
    `documents`. Uses smoothed IDF: ln((1+N)/(1+df)) + 1, so a term present
    in every document still gets a small positive weight rather than zero.
    """
    tokenized = [tokenize(doc) for doc in documents]
    n_docs = len(tokenized)
    if n_docs == 0:
        return []

    doc_freq: dict[str, int] = {}
    for tokens in tokenized:
        for term in set(tokens):
            doc_freq[term] = doc_freq.get(term, 0) + 1

    vectors = []
    for tokens in tokenized:
        tf = _term_frequencies(tokens)
        vector = {}
        for term, freq in tf.items():
            idf = math.log((1 + n_docs) / (1 + doc_freq[term])) + 1
            vector[term] = freq * idf
        vectors.append(vector)
    return vectors


def cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    if not vec_a or not vec_b:
        return 0.0
    shared_terms = set(vec_a) & set(vec_b)
    dot = sum(vec_a[t] * vec_b[t] for t in shared_terms)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


@dataclass
class SimilarityPair:
    index_a: int
    index_b: int
    score: float


def find_similar_pairs(documents: list[str], threshold: float = 0.75) -> list[SimilarityPair]:
    """All (i, j) pairs with i < j whose cosine similarity is >= threshold,
    sorted highest-similarity first. A batch of 0 or 1 documents returns []."""
    vectors = build_tfidf_vectors(documents)
    pairs = []
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            score = cosine_similarity(vectors[i], vectors[j])
            if score >= threshold:
                pairs.append(SimilarityPair(index_a=i, index_b=j, score=round(score, 4)))
    pairs.sort(key=lambda p: p.score, reverse=True)
    return pairs
