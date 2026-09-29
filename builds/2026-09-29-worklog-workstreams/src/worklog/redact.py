"""Secret redaction applied to every string before it is persisted."""
import re
from typing import Any

PLACEHOLDER = "[REDACTED]"

_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)", re.S),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{10,}"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._\-]{12,}"),
    re.compile(r"(?i)\b(?:password|passwd|secret|api[_-]?key|token|private[_-]?key)\b\s*[=:]\s*['\"]?[^\s'\"]{4,}"),
]
_URL_CREDS = re.compile(r"(https?://)[^/\s:@]+(?::[^/\s@]*)?@")


def redact_text(text: str) -> str:
    """Replace likely credentials in a string with a placeholder."""
    text = _URL_CREDS.sub(r"\1", text)
    for pattern in _PATTERNS:
        text = pattern.sub(PLACEHOLDER, text)
    return text


def redact(value: Any) -> Any:
    """Recursively redact strings inside lists, dicts and scalars."""
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    return value


def strip_url_credentials(url: str) -> str:
    """Remove user:password@ from a URL (remotes often embed tokens)."""
    return _URL_CREDS.sub(r"\1", url)
