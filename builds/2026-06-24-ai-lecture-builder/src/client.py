"""Anthropic API client using urllib.request (no external package needed)."""

import json
import os
import urllib.error
import urllib.request


ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096


class AnthropicError(Exception):
    """Raised when the Anthropic API call fails."""


def call_api(system_prompt: str, user_prompt: str) -> str:
    """
    Call the Anthropic Messages API and return the text content of the first response block.

    Raises AnthropicError on missing key, HTTP error, or malformed response.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise AnthropicError("ANTHROPIC_API_KEY environment variable is not set.")

    payload = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise AnthropicError(f"HTTP {exc.code}: {body[:200]}") from exc
    except urllib.error.URLError as exc:
        raise AnthropicError(f"Network error: {exc.reason}") from exc

    try:
        return result["content"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AnthropicError(f"Unexpected API response shape: {str(result)[:200]}") from exc
