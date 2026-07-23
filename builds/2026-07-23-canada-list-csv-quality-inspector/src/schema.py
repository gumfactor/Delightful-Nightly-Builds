"""Default schema and canonical reference data for Canada List CSV QC."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

PROVINCE_ALIASES: dict[str, str] = {
    "ab": "AB", "alberta": "AB",
    "bc": "BC", "british columbia": "BC",
    "mb": "MB", "manitoba": "MB",
    "nb": "NB", "new brunswick": "NB",
    "nl": "NL", "newfoundland and labrador": "NL", "newfoundland": "NL",
    "ns": "NS", "nova scotia": "NS",
    "nt": "NT", "northwest territories": "NT",
    "nu": "NU", "nunavut": "NU",
    "on": "ON", "ontario": "ON",
    "pe": "PE", "prince edward island": "PE", "pei": "PE",
    "qc": "QC", "quebec": "QC", "québec": "QC",
    "sk": "SK", "saskatchewan": "SK",
    "yt": "YT", "yukon": "YT",
}

CANONICAL_PROVINCE_CODES: set[str] = set(PROVINCE_ALIASES.values())

DEFAULT_OWNERSHIP_STATUS_VALUES: list[str] = [
    "canadian-owned",
    "foreign-owned",
    "unknown",
]

LEGAL_SUFFIXES: list[str] = [
    "incorporated", "corporation", "limited", "company",
    "inc", "ltd", "llc", "corp", "co", "lp", "llp", "ulc",
]

DEFAULT_REQUIRED_COLUMNS: list[str] = [
    "business_name",
    "category",
    "province",
    "website",
]


@dataclass
class Schema:
    """QC schema. Column names are matched case-insensitively at load time."""

    required_columns: list[str] = field(
        default_factory=lambda: list(DEFAULT_REQUIRED_COLUMNS)
    )
    ownership_status_values: list[str] = field(
        default_factory=lambda: list(DEFAULT_OWNERSHIP_STATUS_VALUES)
    )

    @classmethod
    def default(cls) -> "Schema":
        return cls()

    @classmethod
    def from_dict(cls, data: dict) -> "Schema":
        required = data.get("required_columns")
        ownership = data.get("ownership_status_values")
        return cls(
            required_columns=list(required) if required else list(DEFAULT_REQUIRED_COLUMNS),
            ownership_status_values=(
                list(ownership) if ownership else list(DEFAULT_OWNERSHIP_STATUS_VALUES)
            ),
        )


def normalize_province(value: str) -> Optional[str]:
    """Return the canonical 2-letter province/territory code, or None if unrecognized."""
    if value is None:
        return None
    key = value.strip().lower()
    return PROVINCE_ALIASES.get(key)


def normalize_business_name(name: str) -> str:
    """Lowercase, strip punctuation and common legal suffixes, collapse whitespace."""
    import re

    lowered = name.lower()
    lowered = re.sub(r"[^\w\s]", " ", lowered)
    tokens = lowered.split()
    while tokens and tokens[-1] in LEGAL_SUFFIXES:
        tokens.pop()
    return " ".join(tokens)
