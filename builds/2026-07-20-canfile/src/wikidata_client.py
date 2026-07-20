"""Thin client for the public, no-auth Wikidata API (www.wikidata.org/w/api.php).

Every network call goes through `_api_get`, so tests can mock a single
function instead of reaching into urllib internals.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "CanFile/1.0 (personal knowledge tool; contact via GitHub)"

# Wikidata properties of interest for an ownership assessment.
PROP_COUNTRY = "P17"
PROP_HEADQUARTERS = "P159"
PROP_PARENT_ORGANIZATION = "P749"
PROP_OWNED_BY = "P127"
PROP_INSTANCE_OF = "P31"

RELEVANT_PROPS = (
    PROP_COUNTRY,
    PROP_HEADQUARTERS,
    PROP_PARENT_ORGANIZATION,
    PROP_OWNED_BY,
    PROP_INSTANCE_OF,
)


class WikidataError(RuntimeError):
    """Raised when the Wikidata API is unreachable or returns malformed data."""


def _api_get(params: dict[str, str], timeout: float = 10.0) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    url = f"{WIKIDATA_API}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
    except Exception as exc:  # network error, HTTP error, timeout, etc.
        raise WikidataError(f"Wikidata request failed: {exc}") from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise WikidataError(f"Wikidata returned invalid JSON: {exc}") from exc


def search_entity(name: str, limit: int = 5) -> list[dict[str, str]]:
    """Search Wikidata for entities matching `name`. Returns ranked candidates."""
    data = _api_get(
        {
            "action": "wbsearchentities",
            "search": name,
            "language": "en",
            "format": "json",
            "type": "item",
            "limit": str(limit),
        }
    )
    results = []
    for entry in data.get("search", []):
        results.append(
            {
                "id": entry.get("id", ""),
                "label": entry.get("label", ""),
                "description": entry.get("description", ""),
            }
        )
    return results


def _extract_entity_ids(claims: dict[str, Any], prop: str) -> list[str]:
    ids: list[str] = []
    for statement in claims.get(prop, []):
        mainsnak = statement.get("mainsnak", {})
        if mainsnak.get("snaktype") != "value":
            continue  # novalue / somevalue snaks carry no entity id
        datavalue = mainsnak.get("datavalue", {})
        if datavalue.get("type") != "wikibase-entityid":
            continue
        entity_id = datavalue.get("value", {}).get("id")
        if entity_id:
            ids.append(entity_id)
    return ids


def get_claims(qid: str) -> dict[str, list[str]]:
    """Fetch the relevant ownership-related claims for a Wikidata entity."""
    data = _api_get(
        {
            "action": "wbgetentities",
            "ids": qid,
            "format": "json",
            "props": "claims",
        }
    )
    entity = data.get("entities", {}).get(qid, {})
    claims = entity.get("claims", {})
    return {prop: _extract_entity_ids(claims, prop) for prop in RELEVANT_PROPS}


def resolve_labels(qids: list[str]) -> dict[str, str]:
    """Batch-resolve a list of Wikidata QIDs to their English labels."""
    unique_ids = sorted({qid for qid in qids if qid})
    if not unique_ids:
        return {}
    data = _api_get(
        {
            "action": "wbgetentities",
            "ids": "|".join(unique_ids),
            "format": "json",
            "props": "labels",
            "languages": "en",
        }
    )
    labels: dict[str, str] = {}
    for qid, entity in data.get("entities", {}).items():
        label_entry = entity.get("labels", {}).get("en", {})
        labels[qid] = label_entry.get("value", qid)
    return labels


def entity_url(qid: str) -> str:
    return f"https://www.wikidata.org/wiki/{qid}"
