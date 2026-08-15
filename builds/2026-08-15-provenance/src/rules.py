"""Deterministic Canadian-ownership rule engine.

Takes already-resolved country QIDs (never touches the network itself — see
``batch.py`` for the Wikidata lookups that produce these inputs) and returns
a ``(verdict, confidence, evidence)`` triple. Every branch is reachable and
independently testable with a plain dict, with zero API key or network
access required — this is the layer that stays honest even when the
optional AI enrichment in ``ai_enrich.py`` is unavailable.
"""

from __future__ import annotations

CANADA_QID = "Q16"

VERDICT_CANADIAN = "canadian"
VERDICT_FOREIGN = "foreign"
VERDICT_UNCERTAIN = "uncertain"


def empty_resolution() -> dict:
    """Return a resolution dict with every field unresolved."""
    return {
        "own_country": None,
        "headquarters_country": None,
        "parent_country": None,
        "owner_country": None,
    }


def classify(resolved: dict) -> tuple[str, float, str]:
    """Classify a business's Canadian-ownership status from resolved claims.

    ``resolved`` must have keys: own_country, headquarters_country,
    parent_country, owner_country — each a Wikidata country QID or None.
    """
    own = resolved.get("own_country")
    hq = resolved.get("headquarters_country")
    parent = resolved.get("parent_country")
    owner = resolved.get("owner_country")

    if own is not None:
        return _classify_with_own_country(own, hq, parent, owner)

    if hq is not None:
        return _classify_with_headquarters_only(hq, parent, owner)

    if parent is not None:
        if parent == CANADA_QID:
            return (
                VERDICT_CANADIAN,
                0.6,
                "No direct country or headquarters claim; parent organization is Canadian.",
            )
        return (
            VERDICT_FOREIGN,
            0.55,
            f"No direct country claim; parent organization resolves to a foreign country ({parent}).",
        )

    if owner is not None:
        if owner == CANADA_QID:
            return (
                VERDICT_CANADIAN,
                0.55,
                "No direct country, headquarters, or parent claim; owning entity is Canadian.",
            )
        return (
            VERDICT_FOREIGN,
            0.5,
            f"No direct country claim; owning entity resolves to a foreign country ({owner}).",
        )

    return (
        VERDICT_UNCERTAIN,
        0.0,
        "No country, headquarters, parent-organization, or ownership claims could be resolved.",
    )


def _classify_with_own_country(own: str, hq, parent, owner) -> tuple[str, float, str]:
    if own == CANADA_QID:
        if hq is not None and hq != CANADA_QID:
            return (
                VERDICT_UNCERTAIN,
                0.5,
                f"Registered country is Canada but headquarters resolves to a different country ({hq}) — conflicting claims.",
            )
        if parent is not None and parent != CANADA_QID:
            return (
                VERDICT_UNCERTAIN,
                0.55,
                "Registered country is Canada, but the company has a foreign parent organization — ownership is not purely Canadian.",
            )
        if owner is not None and owner != CANADA_QID:
            return (
                VERDICT_UNCERTAIN,
                0.55,
                "Registered country is Canada, but the company is owned by a foreign entity — ownership is not purely Canadian.",
            )
        return (VERDICT_CANADIAN, 0.95, "Company's registered country (P17) is Canada.")

    if hq == CANADA_QID:
        return (
            VERDICT_UNCERTAIN,
            0.5,
            f"Registered country ({own}) is foreign but headquarters resolves to Canada — conflicting claims.",
        )
    return (
        VERDICT_FOREIGN,
        0.9,
        f"Company's registered country (P17) is {own}, not Canada.",
    )


def _classify_with_headquarters_only(hq: str, parent, owner) -> tuple[str, float, str]:
    if hq == CANADA_QID:
        if parent is not None and parent != CANADA_QID:
            return (
                VERDICT_UNCERTAIN,
                0.5,
                "Headquarters resolves to Canada, but the parent organization is foreign — ownership is uncertain.",
            )
        if owner is not None and owner != CANADA_QID:
            return (
                VERDICT_UNCERTAIN,
                0.5,
                "Headquarters resolves to Canada, but the owning entity is foreign — ownership is uncertain.",
            )
        return (
            VERDICT_CANADIAN,
            0.75,
            "No direct country claim; headquarters resolves to Canada.",
        )
    return (
        VERDICT_FOREIGN,
        0.7,
        f"No direct country claim; headquarters resolves outside Canada ({hq}).",
    )
