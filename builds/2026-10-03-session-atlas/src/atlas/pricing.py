"""Token price table and cost estimation. Prices are USD per million tokens."""
from __future__ import annotations

import json
from pathlib import Path

# Estimates only. Override with --prices prices.json: {"opus": {"input": 15, ...}}
DEFAULT_PRICES: dict[str, dict[str, float]] = {
    "opus": {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.5},
    "sonnet": {"input": 3.0, "output": 15.0, "cache_write": 3.75, "cache_read": 0.3},
    "haiku": {"input": 1.0, "output": 5.0, "cache_write": 1.25, "cache_read": 0.1},
}
PRICE_KEYS = ("input", "output", "cache_write", "cache_read")


def load_prices(path: str | Path | None) -> dict[str, dict[str, float]]:
    """Return the default table, merged with overrides from a JSON file if given."""
    prices = {family: dict(row) for family, row in DEFAULT_PRICES.items()}
    if path is None:
        return prices
    try:
        overrides = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read price file {path}: {exc}") from exc
    if not isinstance(overrides, dict):
        raise ValueError("price file must be a JSON object keyed by model family")
    for family, row in overrides.items():
        if not isinstance(row, dict):
            raise ValueError(f"prices for {family!r} must be an object")
        merged = prices.setdefault(family.lower(), {key: 0.0 for key in PRICE_KEYS})
        for key in PRICE_KEYS:
            if key in row:
                merged[key] = float(row[key])
    return prices


def family_for(model: str, prices: dict[str, dict[str, float]]) -> str | None:
    """Match a model id such as 'claude-opus-4-1' to a family key by substring."""
    lowered = (model or "").lower()
    for family in prices:
        if family in lowered:
            return family
    return None


def estimate_cost(
    usage_by_model: dict[str, dict[str, int]], prices: dict[str, dict[str, float]]
) -> tuple[float, bool]:
    """Return (cost_usd, has_unpriced). Unknown models contribute 0 and set the flag."""
    total = 0.0
    unpriced = False
    for model, usage in usage_by_model.items():
        family = family_for(model, prices)
        tokens = sum(usage.get(key, 0) for key in PRICE_KEYS)
        if family is None:
            unpriced = unpriced or tokens > 0
            continue
        row = prices[family]
        for key in PRICE_KEYS:
            total += usage.get(key, 0) * row[key] / 1_000_000
    return round(total, 6), unpriced
