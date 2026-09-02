"""Sentence-case and title-case converters used by the citation style engines.

Both converters preserve "protected" words untouched: acronyms (all letters
upper-case, e.g. "HIV") and words with an internal capital after the first
letter (e.g. "McDonald", "mRNA"), since a naive case converter would corrupt
those. This is a deterministic approximation of true proper-noun detection
(no dictionary lookups), documented as a known simplification in Manual.md.
"""

from __future__ import annotations

MINOR_WORDS = {
    "a", "an", "the",
    "and", "but", "or", "nor", "so", "yet",
    "as", "at", "by", "for", "from", "in", "into", "nor", "of", "off",
    "on", "onto", "per", "to", "up", "via", "with",
}


def _is_protected(letters: list[str]) -> bool:
    if not letters:
        return False
    if len(letters) > 1 and all(c.isupper() for c in letters):
        return True  # acronym, e.g. "HIV"
    if any(c.isupper() for c in letters[1:]):
        return True  # internal capital, e.g. "McDonald", "mRNA"
    return False


def _transform_word(word: str, capitalize: bool) -> str:
    letters = [c for c in word if c.isalpha()]
    if not letters:
        return word
    if _is_protected(letters):
        return word
    chars = list(word)
    first_alpha_idx = next(i for i, c in enumerate(chars) if c.isalpha())
    for i, c in enumerate(chars):
        if not c.isalpha():
            continue
        chars[i] = c.upper() if (i == first_alpha_idx and capitalize) else c.lower()
    return "".join(chars)


def _is_segment_boundary(words: list[str], idx: int) -> bool:
    if idx == 0:
        return True
    prev = words[idx - 1].rstrip()
    return prev.endswith(":") or prev.endswith("?")


def to_sentence_case(text: str) -> str:
    """Capitalize only the first word and the first word after ':' or '?'."""
    if not text:
        return text
    words = text.split(" ")
    result = []
    for idx, word in enumerate(words):
        capitalize = _is_segment_boundary(words, idx)
        result.append(_transform_word(word, capitalize))
    return " ".join(result)


def to_title_case(text: str) -> str:
    """Capitalize principal words; lowercase minor words unless first/last/after ':'."""
    if not text:
        return text
    words = text.split(" ")
    n = len(words)
    result = []
    for idx, word in enumerate(words):
        is_boundary = _is_segment_boundary(words, idx)
        is_last = idx == n - 1
        core = "".join(c for c in word if c.isalpha()).lower()
        capitalize = is_boundary or is_last or core not in MINOR_WORDS
        result.append(_transform_word(word, capitalize))
    return " ".join(result)
