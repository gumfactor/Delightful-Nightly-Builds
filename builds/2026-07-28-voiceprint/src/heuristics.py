"""Deterministic pattern detectors for the Voiceprint AI-tell / human-voice audit.

Every function here operates only on the text it is given — no network access,
no file I/O. Each detector is independently unit-tested with both a positive
fixture (pattern present) and a negative fixture (clean prose).
"""

from __future__ import annotations

import re
import statistics
from typing import TypedDict

AI_TELL_PHRASES: list[str] = [
    "delve into",
    "it's important to note",
    "it is important to note",
    "in today's world",
    "in today's fast-paced world",
    "moreover",
    "furthermore",
    "additionally",
    "a testament to",
    "testament to",
    "tapestry",
    "rich tapestry",
    "in the realm of",
    "navigate the complexities",
    "navigating the complexities",
    "that being said",
    "leverage",
    "leveraging",
    "seamless",
    "seamlessly",
    "robust",
    "underscores",
    "underscore the importance",
    "boasts",
    "in conclusion",
    "to summarize",
    "in summary",
    "it's worth noting",
    "it is worth noting",
    "plays a crucial role",
    "plays a vital role",
    "cannot be overstated",
    "unlock the potential",
    "unlocking the potential",
    "dive deep into",
    "shed light on",
    "sheds light on",
    "at the end of the day",
    "a myriad of",
    "myriad of",
    "in the ever-evolving landscape",
    "ever-evolving",
    "game-changer",
    "game changer",
    "paradigm shift",
    "holistic approach",
    "synergy",
    "synergies",
    "foster a",
    "fostering",
    "in essence",
    "it is crucial to",
    "it's crucial to",
    "encompasses",
    "encompass",
    "multifaceted",
    "intricacies",
    "embark on a journey",
    "stands as a",
    "serves as a",
    "elevates",
    "vibrant",
    "bustling",
    "nestled",
]

HEDGE_WORDS: list[str] = [
    "might",
    "could",
    "perhaps",
    "arguably",
    "somewhat",
    "possibly",
    "seemingly",
    "it seems",
    "to some extent",
]

_PASSIVE_PATTERN = re.compile(
    r"\b(?:is|are|was|were|be|been|being)\s+\w+ed\b", re.IGNORECASE
)
_RULE_OF_THREE_PATTERN = re.compile(
    r"\b\w+(?:\s+\w+){0,2}, \w+(?:\s+\w+){0,2},? and \w+(?:\s+\w+){0,2}\b",
    re.IGNORECASE,
)
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
_WORD_PATTERN = re.compile(r"[A-Za-z']+")


class PhraseHit(TypedDict):
    phrase: str
    line: int
    excerpt: str


def word_count(text: str) -> int:
    return len(_WORD_PATTERN.findall(text))


def find_ai_tell_phrases(text: str) -> list[PhraseHit]:
    """Find every AI-tell phrase occurrence, with its line number and excerpt."""
    hits: list[PhraseHit] = []
    lines = text.splitlines()
    for line_num, line in enumerate(lines, start=1):
        lowered = line.lower()
        for phrase in AI_TELL_PHRASES:
            pattern = r"\b" + re.escape(phrase) + r"\b"
            for _ in re.finditer(pattern, lowered):
                hits.append(
                    {"phrase": phrase, "line": line_num, "excerpt": line.strip()}
                )
    return hits


def count_em_dashes(text: str) -> int:
    return text.count("—")


def count_semicolons(text: str) -> int:
    return text.count(";")


def find_hedge_words(text: str) -> list[str]:
    """Return the list of hedge-word matches found (one entry per occurrence)."""
    found: list[str] = []
    lowered = text.lower()
    for word in HEDGE_WORDS:
        pattern = r"\b" + re.escape(word) + r"\b"
        found.extend([word] * len(re.findall(pattern, lowered)))
    return found


def find_passive_voice(text: str) -> list[str]:
    """Return the matched spans of the passive-voice heuristic pattern.

    This is a coarse regex heuristic (auxiliary verb + a word ending in
    '-ed') — it will miss irregular past participles and can over-match a
    handful of adjectival uses. Documented limitation, acceptable for a
    style-nudge tool rather than a linguistic parser.
    """
    return [m.group(0) for m in _PASSIVE_PATTERN.finditer(text)]


def find_rule_of_three(text: str) -> list[str]:
    """Return matches of a comma-separated 'X, Y, and Z' triad pattern."""
    return [m.group(0) for m in _RULE_OF_THREE_PATTERN.finditer(text)]


def sentence_lengths(text: str) -> list[int]:
    """Word count per sentence, for sentences containing at least one word."""
    stripped = text.strip()
    if not stripped:
        return []
    sentences = _SENTENCE_SPLIT_PATTERN.split(stripped)
    lengths = [len(_WORD_PATTERN.findall(s)) for s in sentences]
    return [length for length in lengths if length > 0]


def burstiness(lengths: list[int]) -> dict[str, float]:
    """Coefficient of variation of sentence length: stdev / mean.

    Human prose tends to vary sentence length more (higher burstiness);
    a low coefficient of variation across many sentences is a known
    mechanical-rhythm tell.
    """
    if len(lengths) < 2:
        return {"mean": float(lengths[0]) if lengths else 0.0, "stdev": 0.0, "cv": 0.0}
    mean = statistics.fmean(lengths)
    stdev = statistics.pstdev(lengths)
    cv = stdev / mean if mean > 0 else 0.0
    return {"mean": mean, "stdev": stdev, "cv": cv}


def type_token_ratio(text: str) -> float:
    """Unique words / total words. Lower means more repetitive vocabulary."""
    words = [w.lower() for w in _WORD_PATTERN.findall(text)]
    if not words:
        return 1.0
    return len(set(words)) / len(words)


def split_paragraphs(text: str) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []
    return [p.strip() for p in re.split(r"\n\s*\n", stripped) if p.strip()]


def find_repeated_paragraph_openers(text: str) -> list[dict]:
    """Flag opening words that start 3 or more paragraphs."""
    paragraphs = split_paragraphs(text)
    openers: dict[str, int] = {}
    for para in paragraphs:
        match = _WORD_PATTERN.match(para)
        if not match:
            continue
        word = match.group(0).lower()
        openers[word] = openers.get(word, 0) + 1
    return [
        {"word": word, "count": count}
        for word, count in sorted(openers.items(), key=lambda kv: (-kv[1], kv[0]))
        if count >= 3
    ]


def analyze_text(text: str) -> dict:
    """Run every heuristic once and return the combined analysis dict."""
    lengths = sentence_lengths(text)
    return {
        "word_count": word_count(text),
        "sentence_count": len(lengths),
        "sentence_lengths": lengths,
        "ai_tell_hits": find_ai_tell_phrases(text),
        "em_dash_count": count_em_dashes(text),
        "semicolon_count": count_semicolons(text),
        "hedge_hits": find_hedge_words(text),
        "passive_matches": find_passive_voice(text),
        "rule_of_three_matches": find_rule_of_three(text),
        "burstiness": burstiness(lengths),
        "type_token_ratio": type_token_ratio(text),
        "repeated_openers": find_repeated_paragraph_openers(text),
        "paragraphs": split_paragraphs(text),
    }
