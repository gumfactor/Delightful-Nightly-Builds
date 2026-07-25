"""Strip likely credentials/secrets out of diff text before it is stored or
sent to any external API. Defense-in-depth: this runs on every diff excerpt
regardless of whether the AI path is enabled."""

import re

_PATTERNS = [
    # key/value assignment style: API_KEY="...", token: abc123...
    (
        re.compile(
            r"(?i)\b(api[_-]?key|secret|token|password|passwd|access[_-]?key|"
            r"private[_-]?key)(\s*[:=]\s*)([\'\"]?)([^\s'\"]{6,})([\'\"]?)"
        ),
        r"\1\2\3[REDACTED]\5",
    ),
    # AWS-style access key ids
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED_AWS_KEY]"),
    # Anthropic/OpenAI-style secret keys
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"), "[REDACTED_KEY]"),
    # Bearer tokens in headers
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9\-_.]{10,}"), "Bearer [REDACTED]"),
]


def redact_secrets(text: str) -> str:
    if not text:
        return text
    result = text
    for pattern, replacement in _PATTERNS:
        result = pattern.sub(replacement, result)
    return result
