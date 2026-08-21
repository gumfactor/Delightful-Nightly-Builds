"""Masking and hashing for raw secret values.

Nothing downstream of this module should ever see, store, or transmit a raw
secret value. Every other module calls into here and only keeps the outputs
of these two functions: a masked preview safe to display, and a SHA-256
hash safe to store for re-scan deduplication.
"""

from __future__ import annotations

import hashlib

MASK_CHAR = "•"  # bullet
VISIBLE_PREFIX = 4
VISIBLE_SUFFIX = 4
MIN_MASKED_LENGTH = 8  # ensure short secrets are still fully masked, not fully revealed


def mask_value(raw_value: str) -> str:
    """Return a display-safe preview: first/last VISIBLE_PREFIX/SUFFIX chars, rest masked."""
    if len(raw_value) <= MIN_MASKED_LENGTH:
        return MASK_CHAR * len(raw_value)
    prefix = raw_value[:VISIBLE_PREFIX]
    suffix = raw_value[-VISIBLE_SUFFIX:]
    hidden_count = len(raw_value) - VISIBLE_PREFIX - VISIBLE_SUFFIX
    return f"{prefix}{MASK_CHAR * hidden_count}{suffix}"


def hash_value(raw_value: str) -> str:
    """Return a SHA-256 hex digest of the raw value, used only for dedup — never reversible."""
    return hashlib.sha256(raw_value.encode("utf-8", errors="surrogateescape")).hexdigest()


def masked_context(before: str, raw_value: str, after: str, placeholder: str = "[REDACTED]") -> str:
    """Build a context snippet safe to send to an external API: raw value replaced entirely."""
    return f"{before}{placeholder}{after}"
