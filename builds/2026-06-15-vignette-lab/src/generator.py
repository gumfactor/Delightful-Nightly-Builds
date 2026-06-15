"""Combinatorial vignette assembly from scenario element banks."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .banks import CHARACTERS, THEMES


@dataclass
class Vignette:
    """One generated scenario vignette."""
    theme: str
    index: int                  # 1-based position in the batch
    character: dict
    setting: str
    event: str
    narrative: str
    checks: list[str]
    prompt: str
    researcher_note: str


def _fill(template: str, char: dict) -> str:
    """Substitute character tokens in a template string."""
    return (
        template
        .replace("{name}",        char["name"])
        .replace("{pronoun_sub}", char["pronoun_sub"])
        .replace("{pronoun_obj}", char["pronoun_obj"])
        .replace("{pronoun_pos}", char["pronoun_pos"])
    )


def _to_be(pronoun_sub: str) -> str:
    """Return the correct form of 'to be' for the subject pronoun."""
    return "are" if pronoun_sub.lower() == "they" else "is"


def _build_narrative(char: dict, setting: str, event: str) -> str:
    """Assemble the participant-facing vignette paragraph."""
    name   = char["name"]
    role   = char["role"]
    age    = char["age"]
    sub    = char["pronoun_sub"].capitalize()
    to_be  = _to_be(char["pronoun_sub"])

    setting_filled = _fill(setting, char)
    event_filled   = _fill(event, char)

    return (
        f"{name} is a {age}-year-old {role}. "
        f"{sub} {to_be} {setting_filled} when {event_filled}."
    )


def list_themes() -> dict[str, dict]:
    """Return a summary of all available themes with element counts."""
    summary: dict[str, dict] = {}
    for key, data in THEMES.items():
        summary[key] = {
            "label":       data["label"],
            "description": data["description"],
            "settings":    len(data["settings"]),
            "events":      len(data["events"]),
            "checks":      len(data["checks"]),
            "prompts":     len(data["prompts"]),
            "combinations": len(CHARACTERS) * len(data["settings"]) * len(data["events"]),
        }
    return summary


def generate_vignettes(
    theme: str,
    count: int,
    seed: int | None = None,
) -> list[Vignette]:
    """
    Generate `count` unique vignettes for the requested theme.

    Characters are cycled without repetition until the pool is exhausted,
    then reshuffled for additional rounds. Settings and events are sampled
    without replacement within each round, cycling when the pool is exhausted.
    Same seed always produces the same sequence.
    """
    if theme not in THEMES:
        raise ValueError(f"Unknown theme '{theme}'. Valid themes: {', '.join(THEMES)}")
    if count < 0:
        raise ValueError(f"count must be ≥ 0, got {count}")

    rng = random.Random(seed)
    data = THEMES[theme]

    # Shuffle separate pools so draws are independent
    char_pool    = list(CHARACTERS)
    setting_pool = list(data["settings"])
    event_pool   = list(data["events"])
    check_pool   = list(data["checks"])
    prompt_pool  = list(data["prompts"])

    rng.shuffle(char_pool)
    rng.shuffle(setting_pool)
    rng.shuffle(event_pool)

    def _cycle_pick(pool: list, rng: random.Random, index: int) -> str:
        # Re-shuffle pool at start of each cycle to avoid obvious repetition
        if index % len(pool) == 0 and index > 0:
            rng.shuffle(pool)
        return pool[index % len(pool)]

    vignettes: list[Vignette] = []
    for i in range(count):
        if i % len(char_pool) == 0 and i > 0:
            rng.shuffle(char_pool)

        char    = char_pool[i % len(char_pool)]
        setting = _cycle_pick(setting_pool, rng, i)
        event   = _cycle_pick(event_pool,   rng, i)

        narrative = _build_narrative(char, setting, event)

        # Pick 2 distinct check questions
        rng.shuffle(check_pool)
        checks = [_fill(check_pool[0], char), _fill(check_pool[1], char)]

        # Pick 1 response prompt
        rng.shuffle(prompt_pool)
        prompt = _fill(prompt_pool[0], char)

        vignettes.append(Vignette(
            theme           = theme,
            index           = i + 1,
            character       = char,
            setting         = setting,
            event           = event,
            narrative       = narrative,
            checks          = checks,
            prompt          = prompt,
            researcher_note = data["note"],
        ))

    return vignettes
