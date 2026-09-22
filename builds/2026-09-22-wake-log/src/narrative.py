"""Deterministic, fact-grounded trip-log narrative generation.

A template bank (indexed by Beaufort bucket x precipitation bucket) supplies
several phrasings per condition combination. The template actually used is
chosen by novelty scoring: render every candidate, compute its Jaccard
token-overlap against every narrative previously generated for the same
location, and pick the candidate with the lowest maximum overlap. This is
the same "deterministic draft + novelty check against a persisted corpus"
architecture used by the 2026-08-17 Maple Press build, applied to a new
domain (boating trip logs) and output shape (a written entry, not editorial
copy).

Every template's placeholders are filled exclusively from real computed
facts (never invented) so `verify_facts_present` can confirm the final text
--- deterministic or AI-polished --- always contains every fact verbatim.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Sequence

from .openmeteo import WindowAggregate


def _beaufort_bucket(beaufort_number: int) -> str:
    if beaufort_number <= 1:
        return "calm"
    if beaufort_number <= 3:
        return "light"
    if beaufort_number <= 5:
        return "moderate"
    return "fresh_or_more"


def _precip_bucket(precip_probability: float) -> str:
    return "showery" if precip_probability >= 30.0 else "dry"


# {(beaufort_bucket, precip_bucket): [template, template, template]}
# Placeholders are filled from build_facts()'s keys.
_TEMPLATES: Dict[tuple, List[str]] = {
    ("calm", "dry"): [
        "{date} ({window}) at {location_name}: barely a ripple on the water. "
        "Wind held at {wind_knots} kn ({beaufort_name}), gusting no higher than {gust_knots} kn, "
        "under a {cloud_cover} cloud deck and {temp_c}C air. Glassy conditions, {precip_probability} chance of rain -- "
        "the kind of flat calm that's better for a slow paddle than a proper sail.",
        "Logged {date}, {window} slot at {location_name}. {beaufort_name} ({wind_knots} kn, gusts to {gust_knots} kn) "
        "left the surface nearly still. {temp_c}C, {cloud_cover} cloud, {precip_probability} rain risk -- "
        "an easy, unhurried outing rather than a windy crossing.",
        "{location_name}, {date} {window}: dead calm water under {beaufort_name} conditions "
        "({wind_knots} kn, {gust_knots} kn gusts). {temp_c}C with {cloud_cover} cloud cover and only "
        "{precip_probability} precipitation risk made for a still, mirror-flat session.",
    ],
    ("calm", "showery"): [
        "{date} ({window}) at {location_name}: {beaufort_name} winds ({wind_knots} kn, gusts {gust_knots} kn) "
        "kept the water still, but a {precip_probability} chance of rain under {cloud_cover} cloud meant "
        "keeping an eye on the sky. {temp_c}C on the water.",
        "Logged {date}, {window}, {location_name}. Calm air ({wind_knots} kn, {beaufort_name}) but "
        "{precip_probability} rain odds and {cloud_cover} cloud cover made this a watch-the-radar kind of trip. "
        "{temp_c}C, gusts topping out at {gust_knots} kn.",
        "{location_name}, {date} {window}: flat water under {beaufort_name}, {wind_knots} kn steady "
        "with {gust_knots} kn gusts, but {precip_probability} precipitation risk and {cloud_cover} cloud "
        "kept a jacket within reach. {temp_c}C.",
    ],
    ("light", "dry"): [
        "{date} ({window}) at {location_name}: a proper {beaufort_name}, {wind_knots} kn with gusts to "
        "{gust_knots} kn, just enough to fill a sail without any drama. {temp_c}C, {cloud_cover} cloud, "
        "{precip_probability} rain risk -- close to as good as it gets out here.",
        "Logged {date}, {window}, {location_name}. {beaufort_name} conditions ({wind_knots} kn, "
        "{gust_knots} kn gusts) made for easy, steady progress. {temp_c}C under {cloud_cover} cloud, "
        "{precip_probability} chance of rain.",
        "{location_name}, {date} {window}: {wind_knots} kn of {beaufort_name} (gusting {gust_knots} kn) "
        "kept the boat moving without any fuss. {temp_c}C, {cloud_cover} cloud cover, "
        "{precip_probability} precipitation risk -- a solid window.",
    ],
    ("light", "showery"): [
        "{date} ({window}) at {location_name}: {beaufort_name} ({wind_knots} kn, gusts {gust_knots} kn) made "
        "for pleasant sailing, but {precip_probability} rain odds under {cloud_cover} cloud meant "
        "cutting it shorter than planned. {temp_c}C.",
        "Logged {date}, {window}, {location_name}. Steady {wind_knots} kn ({beaufort_name}), gusts to "
        "{gust_knots} kn -- good wind, undercut by a {precip_probability} chance of rain and "
        "{cloud_cover} cloud cover. {temp_c}C on deck.",
        "{location_name}, {date} {window}: {beaufort_name} at {wind_knots} kn (gusting {gust_knots} kn) "
        "under {cloud_cover} cloud and {precip_probability} rain risk. {temp_c}C -- brought the boat in "
        "a bit early once the sky darkened.",
    ],
    ("moderate", "dry"): [
        "{date} ({window}) at {location_name}: a lively {beaufort_name}, {wind_knots} kn with {gust_knots} kn gusts "
        "kept things brisk. {temp_c}C, {cloud_cover} cloud, only {precip_probability} rain risk -- "
        "a proper sailing day for anyone ready to reef in a puff.",
        "Logged {date}, {window}, {location_name}. {beaufort_name} ({wind_knots} kn, gusts to {gust_knots} kn) "
        "made for a fast, spray-off-the-bow run. {temp_c}C under {cloud_cover} cloud, "
        "{precip_probability} chance of rain.",
        "{location_name}, {date} {window}: {wind_knots} kn of {beaufort_name}, gusting {gust_knots} kn -- "
        "enough to earn its keep. {temp_c}C, {cloud_cover} cloud cover, {precip_probability} precipitation risk.",
    ],
    ("moderate", "showery"): [
        "{date} ({window}) at {location_name}: {beaufort_name} ({wind_knots} kn, gusts {gust_knots} kn) plus a "
        "{precip_probability} chance of rain under {cloud_cover} cloud made this a reef-early, watch-the-horizon trip. "
        "{temp_c}C.",
        "Logged {date}, {window}, {location_name}. Brisk {wind_knots} kn ({beaufort_name}), gusts to "
        "{gust_knots} kn, with {precip_probability} rain odds and {cloud_cover} cloud cover keeping "
        "everyone in foul-weather gear. {temp_c}C.",
        "{location_name}, {date} {window}: {beaufort_name} at {wind_knots} kn (gusting {gust_knots} kn), "
        "{cloud_cover} cloud and {precip_probability} precipitation risk -- a short, wet, exciting run.",
    ],
    ("fresh_or_more", "dry"): [
        "{date} ({window}) at {location_name}: {beaufort_name} conditions, {wind_knots} kn with gusts to "
        "{gust_knots} kn -- experienced-crew territory, though at least the sky stayed dry ({precip_probability} "
        "rain risk, {cloud_cover} cloud). {temp_c}C.",
        "Logged {date}, {window}, {location_name}. {wind_knots} kn of {beaufort_name}, gusting {gust_knots} kn -- "
        "not a day for a light boat. {temp_c}C, {cloud_cover} cloud, {precip_probability} chance of rain.",
        "{location_name}, {date} {window}: {beaufort_name} at {wind_knots} kn (gusts {gust_knots} kn) -- "
        "stayed at the dock and watched the whitecaps. {temp_c}C, {cloud_cover} cloud, "
        "{precip_probability} precipitation risk.",
    ],
    ("fresh_or_more", "showery"): [
        "{date} ({window}) at {location_name}: {beaufort_name} ({wind_knots} kn, gusts {gust_knots} kn) with a "
        "{precip_probability} chance of rain under {cloud_cover} cloud -- a stay-ashore day. {temp_c}C.",
        "Logged {date}, {window}, {location_name}. {wind_knots} kn of {beaufort_name}, gusting {gust_knots} kn, "
        "plus {precip_probability} rain odds and {cloud_cover} cloud cover -- no boat left the slip. {temp_c}C.",
        "{location_name}, {date} {window}: {beaufort_name} at {wind_knots} kn (gusts {gust_knots} kn), "
        "{cloud_cover} cloud and {precip_probability} precipitation risk. Logged as a wash for the record; "
        "{temp_c}C at the dock.",
    ],
}


def build_facts(window: WindowAggregate, location_name: str) -> Dict[str, str]:
    """Return the exact string representations that must appear verbatim in
    any generated narrative, deterministic or AI-polished."""
    return {
        "date": window.date,
        "window": window.window,
        "location_name": location_name,
        "wind_knots": f"{window.wind_knots}",
        "gust_knots": f"{window.gust_knots}",
        "beaufort_name": window.beaufort_name,
        "temp_c": f"{window.temp_c}",
        "precip_probability": f"{window.precip_probability}%",
        "cloud_cover": f"{window.cloud_cover}%",
    }


def _tokenize(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union else 0.0


@dataclass
class GeneratedNarrative:
    text: str
    template_index: int
    novelty_score: float  # max Jaccard overlap against history; 0.0 = fully novel


def generate_narrative(
    window: WindowAggregate,
    location_name: str,
    history: Sequence[str] = (),
) -> GeneratedNarrative:
    """Assemble a trip-log entry for `window`, selecting the template with
    the lowest maximum token-overlap against `history` (prior narratives for
    this location). Facts are always the real computed window values.
    """
    bucket_key = (_beaufort_bucket(window.beaufort_number), _precip_bucket(window.precip_probability))
    templates = _TEMPLATES[bucket_key]
    facts = build_facts(window, location_name)

    history_tokens = [_tokenize(h) for h in history]

    candidates = []
    for idx, template in enumerate(templates):
        rendered = template.format(**facts)
        rendered_tokens = _tokenize(rendered)
        max_overlap = max((_jaccard(rendered_tokens, h) for h in history_tokens), default=0.0)
        candidates.append((max_overlap, idx, rendered))

    # Lowest overlap wins; ties broken by template index for determinism.
    candidates.sort(key=lambda c: (c[0], c[1]))
    best_overlap, best_idx, best_text = candidates[0]

    return GeneratedNarrative(text=best_text, template_index=best_idx, novelty_score=best_overlap)


def verify_facts_present(text: str, facts: Dict[str, str]) -> bool:
    """Return True only if every fact string appears verbatim in `text`."""
    return all(value in text for value in facts.values())
