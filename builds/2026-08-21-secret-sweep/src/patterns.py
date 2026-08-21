"""Secret detection patterns: named credential formats plus a generic
high-entropy-assignment fallback.

Every regex here matches the *shape* of a credential (a documented public
prefix/format) — none of them contain real key material.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class NamedPattern:
    name: str
    regex: re.Pattern
    severity_base: str  # 'critical' or 'high' — refined further by scan scope (tree vs history)


# Each regex captures the credential value in group 1.
NAMED_PATTERNS: list[NamedPattern] = [
    NamedPattern("AWS Access Key ID", re.compile(r"\b((?:AKIA|ASIA)[0-9A-Z]{16})\b"), "critical"),
    NamedPattern("AWS Secret Access Key", re.compile(
        r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?"), "critical"),
    NamedPattern("GitHub Personal Access Token (classic)", re.compile(r"\b(ghp_[A-Za-z0-9]{36})\b"), "critical"),
    NamedPattern("GitHub Fine-Grained PAT", re.compile(r"\b(github_pat_[A-Za-z0-9_]{22,255})\b"), "critical"),
    NamedPattern("GitHub OAuth Token", re.compile(r"\b(gho_[A-Za-z0-9]{36})\b"), "critical"),
    NamedPattern("Slack Token", re.compile(r"\b(xox[baprs]-[A-Za-z0-9-]{10,72})\b"), "critical"),
    NamedPattern("Stripe Live Secret Key", re.compile(r"\b(sk_live_[A-Za-z0-9]{24,99})\b"), "critical"),
    NamedPattern("Stripe Live Publishable Key", re.compile(r"\b(pk_live_[A-Za-z0-9]{24,99})\b"), "high"),
    NamedPattern("Google API Key", re.compile(r"\b(AIza[A-Za-z0-9_-]{35})\b"), "critical"),
    NamedPattern("Anthropic API Key", re.compile(r"\b(sk-ant-[A-Za-z0-9_-]{20,120})\b"), "critical"),
    NamedPattern("OpenAI API Key", re.compile(r"\b(sk-[A-Za-z0-9]{20,64}T3BlbkFJ[A-Za-z0-9]{20,64})\b"), "critical"),
    NamedPattern("SendGrid API Key", re.compile(r"\b(SG\.[A-Za-z0-9_-]{20,24}\.[A-Za-z0-9_-]{20,64})\b"), "critical"),
    NamedPattern("Twilio Account SID", re.compile(r"\b(AC[a-f0-9]{32})\b"), "high"),
    NamedPattern("Twilio Auth Token", re.compile(
        r"(?i)twilio.{0,20}(?:auth[_-]?token)\s*[:=]\s*['\"]?([a-f0-9]{32})['\"]?"), "critical"),
    NamedPattern("PEM Private Key Block", re.compile(
        r"(-----BEGIN(?: (?:RSA|EC|DSA|OPENSSH))? PRIVATE KEY-----)"), "critical"),
    NamedPattern("Firebase Service Account Private Key", re.compile(
        r'"private_key"\s*:\s*"(-----BEGIN PRIVATE KEY-----[^"]+)"'), "critical"),
]

# Values the generic entropy detector should never flag, even if they look high-entropy.
ALLOWLIST_VALUES = {
    "changeme", "change_me", "your_api_key_here", "your-api-key-here",
    "example", "example_key", "dummy", "placeholder", "redacted", "test",
    "test_key", "testkey", "insert_key_here", "todo", "fixme", "none", "null",
    "xxxxxxxxxxxxxxxxxxxxxxxx", "0000000000000000",
}

GENERIC_VAR_NAME_RE = re.compile(r"(?i)(api[_-]?key|secret|token|passwd|password|credential)")
GENERIC_ASSIGNMENT_RE = re.compile(
    r"""(?i)([A-Za-z_][A-Za-z0-9_]*(?:key|secret|token|passwd|password|credential)[A-Za-z0-9_]*)\s*[:=]\s*['"]([^'"\s]{16,128})['"]"""
)

MIN_ENTROPY_BITS_PER_CHAR = 3.5


def shannon_entropy(value: str) -> float:
    """Shannon entropy in bits per character. Empty string has zero entropy."""
    if not value:
        return 0.0
    freq: dict[str, int] = {}
    for ch in value:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(value)
    entropy = 0.0
    for count in freq.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy


def is_allowlisted(value: str) -> bool:
    lowered = value.lower()
    if lowered in ALLOWLIST_VALUES:
        return True
    # Repeated single character (e.g. "aaaaaaaaaaaaaaaa") is never a real secret.
    if len(set(lowered)) <= 1:
        return True
    return False


def find_named_matches(text: str) -> list[tuple[NamedPattern, str, int]]:
    """Return (pattern, raw_value, char_offset) for every named-pattern match in text."""
    results: list[tuple[NamedPattern, str, int]] = []
    for pattern in NAMED_PATTERNS:
        for m in pattern.regex.finditer(text):
            value = m.group(1)
            results.append((pattern, value, m.start(1)))
    return results


def find_generic_matches(text: str) -> list[tuple[str, str, int]]:
    """Return (variable_name, raw_value, char_offset) for high-entropy generic assignments."""
    results: list[tuple[str, str, int]] = []
    for m in GENERIC_ASSIGNMENT_RE.finditer(text):
        var_name, value = m.group(1), m.group(2)
        if is_allowlisted(value):
            continue
        if shannon_entropy(value) < MIN_ENTROPY_BITS_PER_CHAR:
            continue
        results.append((var_name, value, m.start(2)))
    return results
