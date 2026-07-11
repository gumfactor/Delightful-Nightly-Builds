"""Shared helpers: time, deterministic hashing, slugs, and secret redaction."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone

ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return to_iso(utc_now())


def to_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime(ISO_FORMAT)


def parse_iso(value: str) -> datetime:
    """Parse an ISO-8601 UTC timestamp, tolerant of a trailing 'Z' or a +00:00 offset."""
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def event_id(project_id: str, source_provider: str, source_ref: str, event_type: str) -> str:
    """Deterministic event ID so re-sync/re-ingest never creates duplicate rows."""
    payload = "|".join([project_id, source_provider, source_ref, event_type])
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def path_hash(path: str) -> str:
    return hashlib.sha1(path.encode("utf-8")).hexdigest()[:16]


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str, max_len: int = 60) -> str:
    slug = _SLUG_RE.sub("-", text.strip().lower()).strip("-")
    if not slug:
        slug = "item"
    return slug[:max_len].rstrip("-")


# Patterns for common secret/token shapes. Deliberately conservative (favors catching a real
# secret over avoiding a false positive) since this only redacts free text before persistence.
_SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),               # OpenAI/Anthropic-style keys
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),               # GitHub personal access tokens
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{12,}\b"),                  # AWS access key IDs
    re.compile(r"\b[A-Za-z0-9_\-]{32,}\b"),                # generic long opaque tokens
]

_REDACTED = "[REDACTED]"


def redact_secrets(text: str) -> str:
    """Replace substrings that look like API keys/tokens with a redaction marker."""
    if not text:
        return text
    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(_REDACTED, redacted)
    return redacted


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


ISSUE_REF_RE = re.compile(r"#(\d+)\b")


def extract_issue_refs(text: str) -> list[int]:
    if not text:
        return []
    seen = []
    for match in ISSUE_REF_RE.finditer(text):
        num = int(match.group(1))
        if num not in seen:
            seen.append(num)
    return seen


_DURATION_RE = re.compile(r"^(\d+)([dhm])$")


def parse_since(text: str) -> datetime:
    """Parse a relative duration ('7d', '24h', '30m'), 'yesterday'/'today', or an ISO timestamp."""
    text = text.strip().lower()
    now = utc_now()
    if text == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if text == "yesterday":
        return now - timedelta(days=1)
    match = _DURATION_RE.match(text)
    if match:
        amount, unit = int(match.group(1)), match.group(2)
        delta = {"d": timedelta(days=amount), "h": timedelta(hours=amount), "m": timedelta(minutes=amount)}[unit]
        return now - delta
    return parse_iso(text)
