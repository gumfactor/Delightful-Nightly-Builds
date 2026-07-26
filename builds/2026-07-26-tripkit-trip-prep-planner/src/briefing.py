"""Trip briefing text: an optional Claude Haiku call, with a deterministic fallback.

ANTHROPIC_API_KEY is never present in the build/test environment — it is a
runtime-only credential the user supplies when they actually run TripKit.
Every code path that touches the network is exercised only via mocks in
tests; when no API key is set, no network call is attempted at all.
"""

from __future__ import annotations

import json
import urllib.request

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
ANTHROPIC_VERSION = "2023-06-01"
REQUEST_TIMEOUT_SECONDS = 20
MAX_TOKENS = 300


def _call_anthropic_api(api_key: str, prompt: str) -> str:
    """Single network call point so tests can mock it. Raises on any failure."""
    body = json.dumps(
        {
            "model": ANTHROPIC_MODEL,
            "max_tokens": MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=body,
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode("utf-8"))

    content_blocks = payload.get("content") or []
    text_parts = [block.get("text", "") for block in content_blocks if block.get("type") == "text"]
    text = "".join(text_parts).strip()
    if not text:
        raise ValueError("Anthropic response contained no text content.")
    return text


def _build_prompt(
    trip_name: str,
    destination_name: str,
    start_date: str,
    end_date: str,
    activity_tags: list[str],
    mode: str,
    avg_high_c: float,
    avg_low_c: float,
    any_rain: bool,
    any_wind: bool,
    packing_list: dict[str, list[str]],
) -> str:
    weather_label = "forecast" if mode == "forecast" else "historical climate-normal estimate"
    tags = ", ".join(activity_tags) if activity_tags else "general travel"
    item_count = sum(len(items) for items in packing_list.values())
    return (
        f"Write a short (under 120 words), friendly trip-prep briefing for a trip called "
        f"'{trip_name}' to {destination_name}, from {start_date} to {end_date}. "
        f"Activity type: {tags}. Weather ({weather_label}): average high {avg_high_c}C, "
        f"average low {avg_low_c}C, rain expected: {any_rain}, high wind expected: {any_wind}. "
        f"A packing list with {item_count} items has already been generated. "
        f"Point out any weather- or activity-specific nuance the packer should keep in mind. "
        f"Do not repeat the full packing list — just the briefing paragraph."
    )


def _deterministic_briefing(
    trip_name: str,
    destination_name: str,
    start_date: str,
    end_date: str,
    activity_tags: list[str],
    mode: str,
    avg_high_c: float,
    avg_low_c: float,
    any_rain: bool,
    any_wind: bool,
) -> str:
    weather_label = "the forecast" if mode == "forecast" else "typical conditions for this time of year"
    tags = ", ".join(activity_tags) if activity_tags else "your trip"
    conditions = []
    if any_rain:
        conditions.append("some rain")
    if any_wind:
        conditions.append("breezy/windy stretches")
    conditions_text = " and ".join(conditions) if conditions else "no significant rain or wind"

    return (
        f"{trip_name}: {start_date} to {end_date} in {destination_name} ({tags}). "
        f"Based on {weather_label}, expect highs around {avg_high_c}C and lows around {avg_low_c}C, "
        f"with {conditions_text}. Your packing list below is tailored to these conditions and the "
        f"activities you selected — check it against the actual forecast again closer to departure "
        f"if this trip is more than a couple of weeks out."
    )


def generate_briefing(
    trip_name: str,
    destination_name: str,
    start_date: str,
    end_date: str,
    activity_tags: list[str],
    mode: str,
    avg_high_c: float,
    avg_low_c: float,
    any_rain: bool,
    any_wind: bool,
    packing_list: dict[str, list[str]],
    api_key: str | None,
) -> str:
    """Return AI-generated briefing text if api_key is set and the call succeeds,
    otherwise a deterministic template — never raises.
    """
    if api_key:
        prompt = _build_prompt(
            trip_name,
            destination_name,
            start_date,
            end_date,
            activity_tags,
            mode,
            avg_high_c,
            avg_low_c,
            any_rain,
            any_wind,
            packing_list,
        )
        try:
            return _call_anthropic_api(api_key, prompt)
        except Exception:
            pass  # fall through to deterministic template on any failure

    return _deterministic_briefing(
        trip_name, destination_name, start_date, end_date, activity_tags, mode, avg_high_c, avg_low_c, any_rain, any_wind
    )
