"""Deterministic body assembly for a generated editorial piece."""

from __future__ import annotations

MAX_PITCH_LENGTH = 160
MAX_EVIDENCE_LENGTH = 160

INTRO_TEMPLATES = {
    ("spotlight", "consumer"): "You're going to want to remember this one.",
    ("spotlight", "editorial"): (
        "{name} is quietly becoming one of the names to know in Canadian {category}."
    ),
    ("spotlight", "social"): "🍁 Business spotlight: {name}",
    ("gift_guide", "consumer"): (
        "Looking for {category} that's actually made here? Start with this list."
    ),
    ("gift_guide", "editorial"): (
        "The Canadian {category} market has quietly gotten deep. Here are "
        "{count} names worth your attention."
    ),
    ("gift_guide", "social"): "🍁 {count} Canadian {category} picks:",
    ("swap_it", "consumer"): (
        "Next time you're about to buy {category} out of habit, try one of "
        "these instead."
    ),
    ("swap_it", "editorial"): (
        "There's a Canadian-made alternative for most of what you already buy. "
        "Here's where to start with {category}."
    ),
    ("local_spotlight", "consumer"): "If you're in {province}, these are worth knowing.",
    ("local_spotlight", "editorial"): (
        "{province}'s Canadian-owned business scene includes these {count} names."
    ),
}

CTA_BY_OCCASION = {
    "general": (
        "Support Canadian. Buy local, buy Canadian-made, buy from businesses "
        "that keep the money here."
    ),
    "holiday": (
        "This holiday season, every Canadian purchase is a vote for a Canadian "
        "business surviving to see next year."
    ),
    "canada-day": "This Canada Day, put your money where the flag is.",
    "back-to-school": (
        "Before the shopping list goes to the big-box store, check this list first."
    ),
}

SOCIAL_HASHTAGS = "#BuyCanadian #ShopCanadian #SupportLocal"


def truncate(text: str, max_len: int) -> str:
    """Word-boundary truncation. Never cuts mid-word, never exceeds max_len."""
    text = text.strip()
    if len(text) <= max_len:
        return text
    limit = max(max_len - 1, 0)
    cut = text[:limit]
    last_space = cut.rfind(" ")
    if last_space > 0:
        cut = cut[:last_space]
    return cut.rstrip() + "…"


def build_card(business: dict, tone: str) -> str:
    name = business["name"]
    category = business["category"]
    description = business.get("description") or f"A Canadian {category} business."
    pitch = truncate(description, MAX_PITCH_LENGTH)

    location_parts = [p for p in (business.get("city"), business.get("province")) if p]
    location = ", ".join(location_parts)

    # Verified status is authoritative and checked first: a business can carry
    # evidence text (e.g. a Provenance/CanFile "uncertain" rationale) without
    # that evidence actually confirming Canadian ownership, so evidence text
    # alone must never suppress the unverified disclaimer.
    evidence = business.get("evidence")
    if not business.get("verified"):
        why_line = "⚠️ Unverified — confirm Canadian ownership before publishing."
    elif evidence:
        why_line = f"Why it's Canadian: {truncate(evidence, MAX_EVIDENCE_LENGTH)}"
    else:
        why_line = "Verified Canadian-owned."

    lines = [f"**{name}** ({category})" + (f" — {location}" if location else "")]
    lines.append(pitch)
    lines.append(why_line)
    return "\n".join(lines)


def build_body(piece_type: str, tone: str, occasion: str, businesses: list[dict], context: dict) -> str:
    intro_template = INTRO_TEMPLATES.get((piece_type, tone))
    if intro_template is None:
        raise ValueError(f"No intro template for ({piece_type!r}, {tone!r})")
    intro = intro_template.format(**context)

    cards = "\n\n".join(build_card(b, tone) for b in businesses)

    cta = CTA_BY_OCCASION.get(occasion)
    if cta is None:
        raise ValueError(f"Unknown occasion: {occasion!r}")
    if tone == "social":
        cta = f"{cta} {SOCIAL_HASHTAGS}"

    return f"{intro}\n\n{cards}\n\n{cta}"
