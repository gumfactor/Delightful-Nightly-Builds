"""Minimal stdlib-only client for the Anthropic Messages API.

Uses urllib.request directly rather than the `anthropic` package so this
build has zero third-party dependencies, matching the pattern used across
prior builds in this repo. The API key is read from the environment by the
caller and passed in here explicitly — it is never logged or included in
any exception message.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_TIMEOUT_SECONDS = 20


class MissingAPIKeyError(RuntimeError):
    pass


class AnthropicAPIError(RuntimeError):
    """Raised for any network, HTTP, or malformed-response failure.

    Deliberately generic (never includes the API key) so it is safe to log.
    """


def call_claude(
    prompt: str,
    api_key: str | None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 512,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """Send a single-turn prompt to Claude and return the text of the reply.

    Raises MissingAPIKeyError if api_key is falsy, or AnthropicAPIError on
    any network/HTTP/parsing failure.
    """
    if not api_key:
        raise MissingAPIKeyError("ANTHROPIC_API_KEY is not set")

    payload = json.dumps(
        {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=payload,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise AnthropicAPIError(f"Anthropic API returned HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise AnthropicAPIError(f"Anthropic API request failed: {exc.reason}") from exc
    except (TimeoutError, OSError) as exc:
        raise AnthropicAPIError(f"Anthropic API request failed: {exc}") from exc

    try:
        content_blocks = body["content"]
        text = "".join(block["text"] for block in content_blocks if block.get("type") == "text")
    except (KeyError, TypeError) as exc:
        raise AnthropicAPIError("Anthropic API response had an unexpected shape") from exc

    if not text:
        raise AnthropicAPIError("Anthropic API response contained no text content")
    return text
