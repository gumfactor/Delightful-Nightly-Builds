"""Shannon entropy scoring and high-entropy token extraction.

Used to flag candidate secrets that don't match a known vendor pattern:
long base64/hex-like runs with entropy above a threshold are the classic
signature of an API key, private token, or randomly-generated password.
"""

from __future__ import annotations

import math
import re
from collections import Counter

BASE64_CHARSET = re.compile(r"^[A-Za-z0-9+/=_\-]+$")
HEX_CHARSET = re.compile(r"^[0-9a-fA-F]+$")

# A token must be at least this long to be worth scoring — short strings
# can't carry enough entropy to be meaningfully distinguished from noise.
MIN_TOKEN_LENGTH = 20

# Entropy thresholds (bits per character) tuned per charset, following the
# same rule of thumb used by common secret-scanning tools: hex has a max
# possible entropy of 4 bits/char (16 symbols), base64 has a max of ~6
# bits/char (64 symbols), so the hex threshold must be lower.
BASE64_ENTROPY_THRESHOLD = 4.5
HEX_ENTROPY_THRESHOLD = 3.0

# Tokens that look high-entropy but are common false positives.
_COMMON_HASH_LOOKALIKES = frozenset(
    {
        "0" * 40,
        "0" * 32,
        "f" * 40,
        "f" * 32,
    }
)

_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9+/=_\-]{%d,}" % MIN_TOKEN_LENGTH)


def shannon_entropy(s: str) -> float:
    """Return the Shannon entropy of a string, in bits per character.

    Empty or single-character-repeated strings score 0.0.
    """
    if not s:
        return 0.0
    counts = Counter(s)
    length = len(s)
    entropy = 0.0
    for count in counts.values():
        probability = count / length
        entropy -= probability * math.log2(probability)
    return entropy


def _looks_like_english_run(token: str) -> bool:
    """Cheap filter for long identifier-like strings that aren't secrets.

    Repeated-character runs and simple word-separator patterns (all
    lowercase with underscores, e.g. a long variable or function name)
    are not what we're after even if they clear the length bar.
    """
    if token == token.lower() and "_" in token and not any(c.isdigit() for c in token):
        return True
    return False


def classify_token_charset(token: str) -> str | None:
    """Return 'hex', 'base64', or None if the token doesn't fit either charset."""
    if HEX_CHARSET.match(token):
        return "hex"
    if BASE64_CHARSET.match(token):
        return "base64"
    return None


def is_high_entropy(token: str) -> bool:
    """Decide whether a candidate token's entropy clears the charset-appropriate bar."""
    if len(token) < MIN_TOKEN_LENGTH:
        return False
    if token in _COMMON_HASH_LOOKALIKES:
        return False
    if _looks_like_english_run(token):
        return False

    charset = classify_token_charset(token)
    if charset is None:
        return False

    entropy = shannon_entropy(token)
    threshold = HEX_ENTROPY_THRESHOLD if charset == "hex" else BASE64_ENTROPY_THRESHOLD
    return entropy >= threshold


def find_high_entropy_tokens(line: str) -> list[str]:
    """Extract every substring of a line that clears the high-entropy bar."""
    candidates = _TOKEN_PATTERN.findall(line)
    return [tok for tok in candidates if is_high_entropy(tok)]
