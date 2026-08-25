"""Deterministic, corpus-wide rarity-weighted keyword tagging.

Pure-stdlib TF-IDF-style scoring: a token's weight in a chunk is its
frequency in that chunk multiplied by how rare it is across the whole
ingested corpus (fewer chunks containing it -> higher weight). This
surfaces distinctive, searchable terms rather than generic filler words.
"""

import math
import re
from collections import Counter

_STOPWORDS = {
    "the", "and", "for", "are", "but", "not", "you", "all", "can", "her",
    "was", "one", "our", "out", "day", "get", "has", "him", "his", "how",
    "man", "new", "now", "old", "see", "two", "way", "who", "boy", "did",
    "its", "let", "put", "say", "she", "too", "use", "with", "this", "that",
    "from", "have", "will", "your", "which", "their", "about", "would",
    "there", "could", "other", "into", "than", "them", "these", "some",
    "such", "over", "more", "when", "very", "what", "each", "also", "been",
    "were", "then", "they", "shall", "should", "must", "each", "using",
    "based", "study", "project", "proposed", "propose", "proposal",
}

_TOKEN_RE = re.compile(r"[a-z']+")


def _tokenize(text: str) -> list[str]:
    tokens = _TOKEN_RE.findall(text.lower())
    return [t for t in tokens if len(t) >= 4 and t not in _STOPWORDS]


def build_corpus_doc_freq(chunks: list[str]) -> tuple[dict, int]:
    """Return (doc_freq, total_chunks) for a corpus of chunk texts.

    doc_freq maps token -> number of distinct chunks that contain it.
    """
    doc_freq = Counter()
    for chunk in chunks:
        unique_tokens = set(_tokenize(chunk))
        for token in unique_tokens:
            doc_freq[token] += 1
    return dict(doc_freq), len(chunks)


def extract_tags(
    chunk: str,
    doc_freq: dict,
    total_chunks: int,
    top_n: int = 5,
) -> list[str]:
    """Return up to top_n tags for a chunk, ranked by tf-idf-style weight."""
    tokens = _tokenize(chunk)
    if not tokens:
        return []

    term_freq = Counter(tokens)
    scores = {}
    for token, tf in term_freq.items():
        df = doc_freq.get(token, 1)
        idf = math.log((total_chunks + 1) / (df + 1)) + 1
        scores[token] = tf * idf

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return [token for token, _ in ranked[:top_n]]
