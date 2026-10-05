"""Model pricing lookup (USD per million tokens), user-editable."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

CACHE_WRITE_MULTIPLIER = 1.25
CACHE_READ_MULTIPLIER = 0.1
DEFAULT_PRICING_FILE = Path(__file__).resolve().parents[2] / "pricing.json"


@dataclass(frozen=True)
class Rate:
    input: float
    output: float
    cache_write: float
    cache_read: float


class PricingError(ValueError):
    pass


class PriceTable:
    def __init__(self, models: dict[str, dict[str, float]]):
        self._rates: dict[str, Rate] = {}
        for name, spec in models.items():
            try:
                base_in, base_out = float(spec["input"]), float(spec["output"])
            except (KeyError, TypeError, ValueError) as exc:
                raise PricingError(f"pricing entry {name!r} needs numeric input and output") from exc
            self._rates[name.lower()] = Rate(
                base_in,
                base_out,
                float(spec.get("cache_write", base_in * CACHE_WRITE_MULTIPLIER)),
                float(spec.get("cache_read", base_in * CACHE_READ_MULTIPLIER)),
            )

    @classmethod
    def load(cls, path: Path | None = None) -> "PriceTable":
        target = path or DEFAULT_PRICING_FILE
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PricingError(f"cannot read pricing file {target}: {exc}") from exc
        models = data.get("models") if isinstance(data, dict) else None
        if not isinstance(models, dict) or not models:
            raise PricingError(f"pricing file {target} has no 'models' table")
        return cls(models)

    def rate_for(self, model: str) -> Rate | None:
        lowered = model.lower()
        matches = [name for name in self._rates if name in lowered]
        return self._rates[max(matches, key=len)] if matches else None

    def cost(self, model: str, input: int, output: int, cache_write: int, cache_read: int) -> float | None:
        rate = self.rate_for(model)
        if rate is None:
            return None
        return (
            input * rate.input + output * rate.output + cache_write * rate.cache_write + cache_read * rate.cache_read
        ) / 1_000_000

    def cache_savings(self, model: str, cache_read: int) -> float:
        """Dollars saved by reading from cache instead of paying the fresh-input rate."""
        rate = self.rate_for(model)
        return 0.0 if rate is None else cache_read * (rate.input - rate.cache_read) / 1_000_000
