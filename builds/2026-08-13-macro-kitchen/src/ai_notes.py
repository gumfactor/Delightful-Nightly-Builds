"""Optional Claude Haiku 'chef's note' per day, with an unconditional deterministic fallback.

Only aggregate macro numbers for the day are ever sent to the API — never the
user's body stats, weight, age, or any personally identifying information.
Makes zero network calls when ANTHROPIC_API_KEY is unset.
"""
from __future__ import annotations

import json
import os
import urllib.request

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"
TIMEOUT_SECONDS = 20


def _deterministic_note(day_totals: dict, recipe_names: list) -> str:
    protein_share = 0.0
    if day_totals["calories"] > 0:
        protein_share = (day_totals["protein_g"] * 4) / day_totals["calories"]

    if protein_share >= 0.30:
        protein_note = "a protein-forward day"
    elif protein_share >= 0.20:
        protein_note = "a balanced protein day"
    else:
        protein_note = "a lighter-protein day"

    dishes = ", ".join(recipe_names)
    return (
        f"{protein_note.capitalize()} — {int(day_totals['calories'])} kcal across "
        f"{dishes}. Prep the highest-protein dish first if you're batching."
    )


def generate_day_note(day_totals: dict, recipe_names: list) -> tuple[str, bool]:
    """Return (note_text, used_ai). Falls back to a deterministic note on any failure."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _deterministic_note(day_totals, recipe_names), False

    prompt = (
        "You are writing a single short (<=2 sentence) chef's note for a daily meal plan. "
        f"Today's totals: {int(day_totals['calories'])} kcal, "
        f"{int(day_totals['protein_g'])}g protein, {int(day_totals['carbs_g'])}g carbs, "
        f"{int(day_totals['fat_g'])}g fat. Dishes: {', '.join(recipe_names)}. "
        "Give one practical prep or variety tip. No greeting, no sign-off."
    )

    payload = json.dumps(
        {
            "model": MODEL,
            "max_tokens": 150,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=payload,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
        text = body["content"][0]["text"].strip()
        if text:
            return text, True
        return _deterministic_note(day_totals, recipe_names), False
    except Exception:
        return _deterministic_note(day_totals, recipe_names), False
