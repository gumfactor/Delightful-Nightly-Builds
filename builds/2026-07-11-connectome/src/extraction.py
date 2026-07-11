"""Concept extraction: deterministic TF-IDF-style scoring plus optional Claude enrichment."""

from __future__ import annotations

import json
import math
import re
import urllib.error
import urllib.request
from collections import Counter
from typing import Optional

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "else", "of", "to", "in",
    "on", "at", "by", "for", "with", "about", "against", "between", "into",
    "through", "during", "before", "after", "above", "below", "from", "up",
    "down", "out", "off", "over", "under", "again", "further", "once", "is",
    "are", "was", "were", "be", "been", "being", "have", "has", "had", "having",
    "do", "does", "did", "doing", "this", "that", "these", "those", "it", "its",
    "as", "so", "than", "too", "very", "can", "will", "just", "should", "now",
    "we", "our", "you", "your", "i", "he", "she", "they", "them", "his", "her",
    "not", "no", "yes", "also", "such", "each", "which", "what", "when", "where",
    "who", "how", "all", "any", "both", "more", "most", "some", "other", "into",
    "there", "here", "while", "because", "her", "his", "their", "my", "me",
}

MIN_TOKEN_LEN = 3
TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z\-']+")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
MAX_BODY_CHARS_FOR_AI = 4000


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens, filtered by stopwords and minimum length."""
    tokens = TOKEN_PATTERN.findall(text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) >= MIN_TOKEN_LEN]


def compute_document_frequencies(note_bodies: dict[str, str]) -> Counter:
    """Given {note_path: body}, return concept -> number of notes containing it."""
    doc_freq: Counter = Counter()
    for body in note_bodies.values():
        unique_terms = set(tokenize(body))
        for term in unique_terms:
            doc_freq[term] += 1
    return doc_freq


def extract_concepts(
    body: str,
    doc_freq: Counter,
    total_notes: int,
    top_n: int = 15,
) -> list[tuple[str, float]]:
    """Return up to top_n (concept, weight) pairs for a note, ranked by TF-IDF.

    Uses smoothed IDF (log((N+1)/(df+1)) + 1) so a term appearing in every
    note (df == total_notes) never divides by zero and still receives a
    positive, non-dominant weight.
    """
    tokens = tokenize(body)
    if not tokens:
        return []
    term_freq = Counter(tokens)
    scored = []
    for term, tf in term_freq.items():
        df = doc_freq.get(term, 1)
        idf = math.log((total_notes + 1) / (df + 1)) + 1
        scored.append((term, tf * idf))
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_n]


def enrich_with_claude(
    body: str,
    fallback_concepts: list[tuple[str, float]],
    api_key: Optional[str],
    top_n: int = 15,
) -> list[tuple[str, float]]:
    """Optionally refine concepts using Claude Haiku. Always falls back cleanly.

    Any failure (no key, network error, bad status, malformed response) returns
    fallback_concepts unchanged rather than raising.
    """
    if not api_key:
        return fallback_concepts

    prompt = (
        "Extract the 5-8 most important distinct concepts, entities, or topics "
        "from this note. Respond with ONLY a JSON array of lowercase strings, "
        "no prose, no markdown fences.\n\nNote:\n" + body[:MAX_BODY_CHARS_FOR_AI]
    )
    payload = json.dumps({
        "model": ANTHROPIC_MODEL,
        "max_tokens": 256,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            ANTHROPIC_API_URL,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status != 200:
                return fallback_concepts
            raw = json.loads(response.read().decode("utf-8"))
            text = raw["content"][0]["text"].strip()
            concepts = json.loads(text)
            if not isinstance(concepts, list):
                return fallback_concepts
            cleaned = [str(c).strip().lower() for c in concepts if str(c).strip()]
            if not cleaned:
                return fallback_concepts
            # Assign descending synthetic weights so downstream ranking still works.
            return [(term, float(len(cleaned) - i)) for i, term in enumerate(cleaned[:top_n])]
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            KeyError, IndexError, ValueError, json.JSONDecodeError):
        return fallback_concepts
