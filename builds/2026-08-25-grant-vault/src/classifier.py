"""Deterministic section-type classification for grant text chunks."""

import re

SECTION_TYPES = [
    "Specific Aims",
    "Significance",
    "Innovation",
    "Approach",
    "Broader Impacts",
    "Data Management Plan",
    "Budget Justification",
    "Other",
]

# Heading lines that immediately identify a chunk's section, regardless of
# body content. Matched case-insensitively against the chunk's first line.
_HEADING_PATTERNS = {
    "Specific Aims": [r"^specific\s+aims?\b"],
    "Significance": [r"^significance\b"],
    "Innovation": [r"^innovation\b"],
    "Approach": [r"^(research\s+)?(strategy|approach)\b"],
    "Broader Impacts": [r"^broader\s+impacts?\b"],
    "Data Management Plan": [r"^data\s+management\s+plan\b"],
    "Budget Justification": [r"^budget\s+justification\b"],
}

# Keyword signatures used when no heading line is present. Each match of a
# phrase (case-insensitive, whole-word-bounded) adds one point to that
# section's score; the highest-scoring section wins ties broken by the
# order below (earlier = higher priority).
_KEYWORD_SIGNATURES = {
    "Specific Aims": [
        "specific aim", "central hypothesis", "aim 1", "aim 2", "aim 3",
        "we hypothesize", "the objective of this proposal",
    ],
    "Significance": [
        "significant because", "public health", "advance the field",
        "critical gap", "addresses a major gap", "significance of",
    ],
    "Innovation": [
        "novel", "innovative", "departs from", "new approach",
        "unlike prior work", "innovation of this proposal",
    ],
    "Approach": [
        "we will", "methodology", "participants will", "procedure",
        "experimental design", "study design", "data will be collected",
    ],
    "Broader Impacts": [
        "broader impact", "outreach", "underrepresented",
        "dissemination", "training the next generation", "public engagement",
    ],
    "Data Management Plan": [
        "data management", "repository", "data sharing", "retention period",
        "de-identified", "deposited in a public",
    ],
    "Budget Justification": [
        "budget justification", "personnel costs", "fringe benefits",
        "requested budget", "cost of", "direct costs",
    ],
}


def classify_section(chunk: str) -> str:
    """Return the most likely section type for a text chunk.

    Heading-line detection takes priority; falls back to keyword-signature
    scoring; returns "Other" when nothing matches.
    """
    if not chunk or not chunk.strip():
        return "Other"

    first_line = chunk.strip().splitlines()[0].strip().lower()
    for section, patterns in _HEADING_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, first_line):
                return section

    lowered = chunk.lower()
    scores = {}
    for section, phrases in _KEYWORD_SIGNATURES.items():
        score = 0
        for phrase in phrases:
            score += len(re.findall(re.escape(phrase), lowered))
        scores[section] = score

    best_section = max(scores, key=lambda s: scores[s])
    if scores[best_section] == 0:
        return "Other"
    return best_section
