"""Deterministic fact extraction from real PubMed abstract text.

Every function here is a pure regex/keyword transform with no network
access and no AI call — the discussion-question rule engine and the
deterministic vignette assembler both depend on these functions never
guessing: a value that cannot be confidently extracted is returned as
None rather than fabricated.
"""
import re
from typing import Dict, Optional, Union

Facts = Dict[str, Union[int, str, bool, None]]

_SAMPLE_SIZE_PATTERNS = [
    re.compile(r"\bN\s*=\s*(\d{1,6})\b"),
    re.compile(r"\bn\s*=\s*(\d{1,6})\b"),
    re.compile(r"\b(\d{1,6})\s+participants\b", re.IGNORECASE),
    re.compile(r"\b(\d{1,6})\s+subjects\b", re.IGNORECASE),
    re.compile(r"\bsample\s+of\s+(\d{1,6})\b", re.IGNORECASE),
]

_MAX_PLAUSIBLE_SAMPLE_SIZE = 1_000_000


def extract_sample_size(text: str) -> Optional[int]:
    """Return the first plausible explicit sample size mentioned, or None."""
    for pattern in _SAMPLE_SIZE_PATTERNS:
        match = pattern.search(text)
        if match:
            value = int(match.group(1))
            if 1 <= value <= _MAX_PLAUSIBLE_SAMPLE_SIZE:
                return value
    return None


_P_VALUE_PATTERN = re.compile(r"\bp\s*[<>=]\s*\.?\d+(?:\.\d+)?", re.IGNORECASE)


def extract_p_value(text: str) -> Optional[str]:
    """Return the first reported p-value expression verbatim (normalized whitespace), or None."""
    match = _P_VALUE_PATTERN.search(text)
    if match:
        return re.sub(r"\s+", " ", match.group(0)).strip()
    return None


_EFFECT_SIZE_PATTERN = re.compile(
    r"\b(r|d|OR|RR|HR|beta|β|R2|R²)\s*=\s*-?\d+(?:\.\d+)?"
)


def extract_effect_size(text: str) -> Optional[str]:
    """Return the first reported effect-size statistic verbatim, or None."""
    match = _EFFECT_SIZE_PATTERN.search(text)
    if match:
        return re.sub(r"\s+", " ", match.group(0)).strip()
    return None


_METHODOLOGY_KEYWORDS = [
    ("meta-analysis", ("meta-analysis", "meta analytic", "systematic review")),
    ("randomized controlled trial", ("randomized controlled trial", "randomised controlled trial")),
    ("fMRI", ("fmri", "functional magnetic resonance")),
    ("EEG", ("eeg", "electroencephalog")),
    ("longitudinal", ("longitudinal",)),
    ("case study", ("case study", "case report")),
    ("cross-sectional", ("cross-sectional", "cross sectional")),
    ("survey", ("survey", "questionnaire")),
    ("correlational", ("correlat",)),
]


def extract_methodology(text: str) -> Optional[str]:
    """Return a single best-matching methodology tag, checked in a fixed
    priority order (more specific designs like meta-analysis or fMRI are
    checked before the very broad 'correlational' keyword), or None."""
    lowered = text.lower()
    for label, keywords in _METHODOLOGY_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return label
    return None


_POPULATION_KEYWORDS = [
    ("incarcerated/forensic sample", ("incarcerated", "forensic sample", "offender", "inmate")),
    ("clinical sample", ("clinical sample", "patients with", "diagnosed with")),
    ("children", ("children", "child participants", "pediatric")),
    ("adolescents", ("adolescent", "teenage")),
    ("undergraduate sample", ("undergraduate", "college student", "university student")),
    ("community sample", ("community sample", "community-based", "general population")),
]


def extract_population(text: str) -> Optional[str]:
    """Return a single best-matching population descriptor, or None."""
    lowered = text.lower()
    for label, keywords in _POPULATION_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return label
    return None


_CONTROL_LANGUAGE_KEYWORDS = (
    "control group", "control condition", "compared to", "compared with",
    "versus", " vs ", "placebo",
)


def has_control_comparison_language(text: str) -> bool:
    """Whether the abstract mentions an explicit comparison/control condition."""
    lowered = text.lower()
    return any(keyword in lowered for keyword in _CONTROL_LANGUAGE_KEYWORDS)


def indefinite_article(phrase: str) -> str:
    """Return 'an' for a phrase starting with a vowel sound, else 'a'.
    Used when interpolating extracted population descriptors into text."""
    return "an" if phrase[:1].lower() in "aeiou" else "a"


def extract_all(abstract_text: str) -> Facts:
    """Run every extractor once and return the combined fact set."""
    return {
        "sample_size": extract_sample_size(abstract_text),
        "population": extract_population(abstract_text),
        "methodology": extract_methodology(abstract_text),
        "effect_size_text": extract_effect_size(abstract_text),
        "p_value_text": extract_p_value(abstract_text),
        "has_control_comparison": has_control_comparison_language(abstract_text),
    }
