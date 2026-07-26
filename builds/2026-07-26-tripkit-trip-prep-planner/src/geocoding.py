"""Resolve a typed destination name to coordinates via the Open-Meteo Geocoding API."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
REQUEST_TIMEOUT_SECONDS = 10


class GeocodingError(Exception):
    """Raised when a destination cannot be resolved to coordinates."""


@dataclass(frozen=True)
class ResolvedPlace:
    display_name: str
    country: str
    latitude: float
    longitude: float


def fetch_json(url: str) -> dict:
    """Thin wrapper around urlopen so tests can mock a single call point."""
    with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def resolve_destination(query: str) -> ResolvedPlace:
    """Look up a free-text destination and return its first geocoding match.

    Raises GeocodingError if the query is empty or no place is found.
    """
    query = query.strip()
    if not query:
        raise GeocodingError("Destination cannot be empty.")

    params = urllib.parse.urlencode({"name": query, "count": 1, "language": "en", "format": "json"})
    url = f"{GEOCODING_URL}?{params}"

    try:
        data = fetch_json(url)
    except (OSError, ValueError) as exc:
        raise GeocodingError(f"Could not reach the geocoding service: {exc}") from exc

    results = data.get("results") or []
    if not results:
        raise GeocodingError(f"No location found for '{query}'.")

    match = results[0]
    name = match.get("name", query)
    admin1 = match.get("admin1")
    country = match.get("country", "")
    display_parts = [part for part in (name, admin1, country) if part]
    display_name = ", ".join(display_parts)

    try:
        latitude = float(match["latitude"])
        longitude = float(match["longitude"])
    except (KeyError, TypeError, ValueError) as exc:
        raise GeocodingError(f"Malformed geocoding result for '{query}'.") from exc

    return ResolvedPlace(display_name=display_name, country=country, latitude=latitude, longitude=longitude)
