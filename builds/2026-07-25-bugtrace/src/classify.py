"""Deterministic keyword-based root-cause classifier.

This is the taxonomy shared by both the deterministic classifier and the
optional AI classifier (src/ai_classify.py), so results from either source
are directly comparable in the aggregated report.
"""

import re

TAXONOMY = [
    "test_only_fix",
    "config_env_credentials",
    "dependency_version",
    "async_race_condition",
    "off_by_one_index",
    "null_none_handling",
    "type_mismatch",
    "logic_operator_error",
    "error_handling_missing",
    "api_integration_misuse",
    "typo_naming",
    "other",
]

CATEGORY_LABELS = {
    "test_only_fix": "Test-only fix",
    "config_env_credentials": "Config / env / credentials",
    "dependency_version": "Dependency / version",
    "async_race_condition": "Async / race condition",
    "off_by_one_index": "Off-by-one / index error",
    "null_none_handling": "Null / None handling",
    "type_mismatch": "Type mismatch",
    "logic_operator_error": "Logic / operator error",
    "error_handling_missing": "Missing error handling",
    "api_integration_misuse": "API / integration misuse",
    "typo_naming": "Typo / naming",
    "other": "Other",
}

# Ordered (category, [regex patterns]); first match wins. Keep more specific
# categories earlier so generic words in later buckets don't steal the match.
_RULES = [
    (
        "config_env_credentials",
        [r"\benv(?:ironment)? ?var", r"\.env\b", r"\bcredential", r"\bapi[_-]?key\b", r"\bsecret key\b", r"\bconfig(?:uration)?\b"],
    ),
    (
        "dependency_version",
        [r"requirements\.txt", r"package\.json", r"\bupgrade\b", r"\bdowngrade\b", r"\bbump\b.*version", r"\bdependenc"],
    ),
    (
        "async_race_condition",
        [r"race condition", r"\bdeadlock\b", r"\basync\b", r"\bawait\b", r"\bconcurren", r"\bthread.?safe\b"],
    ),
    (
        "off_by_one_index",
        [r"off.by.one", r"index ?error", r"out of range", r"out-of-range", r"\bboundary\b", r"fencepost"],
    ),
    (
        "null_none_handling",
        [r"nonetype", r"null ?pointer", r"null ?reference", r"\bnull check", r"\bnone check", r"undefined is not"],
    ),
    (
        "type_mismatch",
        [r"type ?error", r"type mismatch", r"\bcast(?:ing)?\b", r"wrong type"],
    ),
    (
        "logic_operator_error",
        [r"\binverted\b", r"wrong operator", r"logic error", r"\bnegat(?:e|ed|ion)\b"],
    ),
    (
        "error_handling_missing",
        [r"unhandled exception", r"missing (?:try|except)", r"add(?:ed)? error handling", r"\btraceback\b", r"\buncaught\b"],
    ),
    (
        "api_integration_misuse",
        [r"\bapi\b", r"\bendpoint\b", r"\b40[134]\b", r"\b500 error\b", r"\btimeout\b", r"\brate limit"],
    ),
    (
        "typo_naming",
        [r"\btypo\b", r"\bmisspell", r"\brename\b"],
    ),
]

_COMPILED_RULES = [(category, [re.compile(p, re.IGNORECASE) for p in patterns]) for category, patterns in _RULES]


def _is_test_only(changed_files):
    if not changed_files:
        return False
    return all(_looks_like_test_file(f) for f in changed_files)


def _looks_like_test_file(filename: str) -> bool:
    lower = filename.lower()
    return (
        "/tests/" in lower
        or lower.startswith("tests/")
        or "/test_" in lower
        or lower.startswith("test_")
        or lower.endswith(".spec.js")
        or lower.endswith("_test.py")
    )


def keyword_classify(message: str, diff_excerpt: str, changed_files=None):
    """Return (category, explanation) using deterministic keyword rules.

    Always returns a valid category from TAXONOMY, never raises.
    """
    changed_files = changed_files or []
    if _is_test_only(changed_files):
        return "test_only_fix", "Every changed file lives under a test path."

    text = f"{message or ''}\n{diff_excerpt or ''}".lower()
    for category, patterns in _COMPILED_RULES:
        for pattern in patterns:
            if pattern.search(text):
                return category, f"Matched keyword rule for '{CATEGORY_LABELS[category]}'."

    return "other", "No keyword rule matched; classified as other."
