"""Known vendor secret patterns.

Each pattern is a high-confidence, unambiguous signature — if one of these
matches, the finding is tiered 'high' and skips AI triage entirely, since
there's nothing ambiguous about a string shaped exactly like an AWS access
key ID to disambiguate.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class VendorPattern:
    name: str
    regex: re.Pattern[str]


VENDOR_PATTERNS: list[VendorPattern] = [
    VendorPattern("AWS Access Key ID", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    VendorPattern("GitHub Personal Access Token", re.compile(r"\bghp_[A-Za-z0-9]{36}\b")),
    VendorPattern("GitHub OAuth Token", re.compile(r"\bgho_[A-Za-z0-9]{36}\b")),
    VendorPattern("GitHub Fine-Grained PAT", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}\b")),
    VendorPattern("Slack Token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    VendorPattern("Stripe Live Secret Key", re.compile(r"\bsk_live_[A-Za-z0-9]{24,}\b")),
    VendorPattern("Google/Firebase API Key", re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")),
    VendorPattern("Twilio API Key", re.compile(r"\bSK[0-9a-fA-F]{32}\b")),
    VendorPattern(
        "PEM Private Key Block",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |)PRIVATE KEY-----"),
    ),
    VendorPattern(
        "JSON Web Token",
        re.compile(r"\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
    ),
]

# Variable-name signals used by the tier-assignment step in classifier.py
# to promote an unmatched high-entropy token from 'low' to 'medium'.
SUSPICIOUS_VARIABLE_NAMES = re.compile(
    r"(api[_-]?key|secret|token|password|passwd|credential|private[_-]?key|auth)",
    re.IGNORECASE,
)


def match_vendor_patterns(line: str) -> list[VendorPattern]:
    """Return every vendor pattern that matches somewhere in the line."""
    return [pattern for pattern in VENDOR_PATTERNS if pattern.regex.search(line)]
