"""Deterministic template generation and the orchestration that ties
taxonomy + novelty + storage + the optional AI client together into a
single generated, stored library entry.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from . import ai_client, novelty, storage


def _hook(concept, domain) -> str:
    return f"{domain.name}: {domain.trigger_word}, and {domain.outcome_word}. It's a close cousin of {concept.name.lower()}."


def _analogy_undergrad(concept, domain) -> str:
    return (
        f"{concept.name} is a useful case for {domain.name.lower()} thinking. Structurally: "
        f"{concept.trigger}, then {concept.mechanism}, producing the outcome that {concept.consequence}. "
        f"Compare {domain.name.lower()}: {domain.trigger_word}, then {domain.process_word}, and "
        f"{domain.outcome_word}. The mapping is not perfect, but the structural parallel — trigger, "
        f"mechanism, consequence — makes {concept.name.lower()} easier to hold onto than the biology alone."
    )


def _analogy_public(concept, domain) -> str:
    return (
        f"Here's a way to feel {concept.name.lower()} instead of just hearing the definition. Picture "
        f"{domain.name.lower()}: {domain.trigger_word}, {domain.process_word}, and {domain.outcome_word}. "
        f"That's what's happening, in miniature, when {concept.trigger} and {concept.mechanism} — until "
        f"{concept.consequence}."
    )


def _analogy_book(concept, domain) -> str:
    trigger = domain.trigger_word[0].upper() + domain.trigger_word[1:]
    return (
        f"Consider {domain.name.lower()}. {trigger}; {domain.process_word}; {domain.outcome_word}. "
        f"It is, in its way, a small and familiar rehearsal of something larger: {concept.trigger}, "
        f"{concept.mechanism}, until {concept.consequence}. The parallel is {concept.name.lower()}, "
        f"and once you have seen it in {domain.name.lower()}, it is hard to unsee in the body."
    )


_ANALOGY_BUILDERS = {
    "undergrad_lecture": _analogy_undergrad,
    "public_talk": _analogy_public,
    "book_chapter": _analogy_book,
}


def build_template(concept, domain, audience: str) -> dict:
    """Deterministic hook/analogy/caveat for a (concept, domain, audience) triple.
    Always produces complete, non-empty text with no external dependency."""
    if audience not in _ANALOGY_BUILDERS:
        raise ValueError(f"Unknown audience '{audience}'")
    return {
        "hook": _hook(concept, domain),
        "analogy": _ANALOGY_BUILDERS[audience](concept, domain),
        "caveat": f"Where this breaks down: {concept.caveat}",
    }


def generate_entry(
    concept,
    domain,
    audience: str,
    conn,
    api_key: Optional[str] = None,
    use_ai: bool = True,
    model: str = ai_client.DEFAULT_MODEL,
) -> dict:
    """Builds one analogy (AI-polished if available and requested, template
    otherwise), scores its novelty against the existing library, inserts it,
    and returns the stored record."""
    draft = build_template(concept, domain, audience)

    source = "template"
    text = draft
    if use_ai and api_key:
        ai_result = ai_client.call_claude(concept, domain, audience, draft, api_key=api_key, model=model)
        if ai_result is not None:
            text = ai_result
            source = "ai"

    prior_usage = storage.count_triple(conn, concept.id, domain.id, audience)
    existing_texts = storage.all_analogy_texts(conn)
    overlap = novelty.max_overlap(text["analogy"], existing_texts)
    score = novelty.novelty_score(prior_usage, overlap)

    record = {
        "concept_id": concept.id,
        "concept_name": concept.name,
        "subdomain": concept.subdomain,
        "domain_id": domain.id,
        "domain_name": domain.name,
        "audience": audience,
        "hook": text["hook"],
        "analogy": text["analogy"],
        "caveat": text["caveat"],
        "source": source,
        "novelty_score": score,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    entry_id = storage.insert_analogy(conn, record)
    record["id"] = entry_id
    return record
