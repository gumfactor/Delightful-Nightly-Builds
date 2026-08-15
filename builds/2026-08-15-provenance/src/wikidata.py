"""Thin client for the free, no-auth Wikidata API.

Only what the rule engine needs: resolve a business name to a QID, pull its
country/headquarters/parent/owner claims, and resolve a QID's plain-English
label. Every network call goes through ``urllib.request`` so tests can mock
a single choke point (``urllib.request.urlopen``) with zero real HTTP.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Optional

API_URL = "https://www.wikidata.org/w/api.php"
USER_AGENT = "Provenance/1.0 (Canada List ownership research tool; contact via GitHub)"
TIMEOUT_SECONDS = 10

# Property IDs used to determine ownership/location.
PROP_COUNTRY = "P17"
PROP_HEADQUARTERS = "P159"
PROP_PARENT_ORG = "P749"
PROP_OWNED_BY = "P127"

CANADA_QID = "Q16"


def _fetch_json(params: dict) -> Optional[dict]:
    """GET the Wikidata API with the given query params, return parsed JSON or None."""
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{API_URL}?{query}",
        headers={"User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read()
    except Exception:
        return None
    try:
        return json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return None


def search_entity(name: str) -> Optional[str]:
    """Resolve a business name to a Wikidata QID, or None if no match found."""
    if not name or not name.strip():
        return None
    data = _fetch_json(
        {
            "action": "wbsearchentities",
            "search": name.strip(),
            "language": "en",
            "type": "item",
            "limit": 1,
            "format": "json",
        }
    )
    if not data:
        return None
    results = data.get("search") or []
    if not results:
        return None
    return results[0].get("id")


def get_claims(qid: str) -> dict:
    """Return a dict of {country, headquarters, parent_org, owned_by} QIDs (or None each)."""
    result = {
        "country": None,
        "headquarters": None,
        "parent_org": None,
        "owned_by": None,
    }
    if not qid:
        return result

    data = _fetch_json(
        {
            "action": "wbgetentities",
            "ids": qid,
            "props": "claims",
            "format": "json",
        }
    )
    if not data:
        return result

    entities = data.get("entities") or {}
    entity = entities.get(qid) or {}
    claims = entity.get("claims") or {}

    result["country"] = _first_claim_value(claims, PROP_COUNTRY)
    result["headquarters"] = _first_claim_value(claims, PROP_HEADQUARTERS)
    result["parent_org"] = _first_claim_value(claims, PROP_PARENT_ORG)
    result["owned_by"] = _first_claim_value(claims, PROP_OWNED_BY)
    return result


def _first_claim_value(claims: dict, property_id: str) -> Optional[str]:
    """Extract the first claim's target QID for a given property, or None."""
    entries = claims.get(property_id)
    if not entries:
        return None
    try:
        mainsnak = entries[0]["mainsnak"]
        if mainsnak.get("snaktype") != "value":
            return None
        return mainsnak["datavalue"]["value"]["id"]
    except (KeyError, IndexError, TypeError):
        return None


def get_label(qid: str) -> Optional[str]:
    """Return the English label for a QID (e.g. a country name), or None."""
    if not qid:
        return None
    data = _fetch_json(
        {
            "action": "wbgetentities",
            "ids": qid,
            "props": "labels",
            "languages": "en",
            "format": "json",
        }
    )
    if not data:
        return None
    try:
        return data["entities"][qid]["labels"]["en"]["value"]
    except (KeyError, TypeError):
        return None
