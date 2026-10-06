"""User rules: ignore merchants, alias names, declare cancellations."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


class RulesError(ValueError):
    pass


@dataclass
class Rules:
    ignore: list[str] = field(default_factory=list)
    aliases: dict[str, str] = field(default_factory=dict)
    cancelled: dict[str, date] = field(default_factory=dict)

    def is_ignored(self, description: str) -> bool:
        lowered = description.lower()
        return any(token.lower() in lowered for token in self.ignore)

    def alias_for(self, description: str) -> str | None:
        lowered = description.lower()
        for token, name in self.aliases.items():
            if token.lower() in lowered:
                return name
        return None

    def cancelled_on(self, merchant: str) -> date | None:
        for name, when in self.cancelled.items():
            if name.lower() == merchant.lower():
                return when
        return None


def load_rules(path: str | Path | None) -> Rules:
    if path is None:
        return Rules()
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RulesError(f"Rules file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RulesError(f"Rules file is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise RulesError("Rules file must contain a JSON object")
    cancelled: dict[str, date] = {}
    for name, when in (data.get("cancelled") or {}).items():
        try:
            cancelled[name] = date.fromisoformat(when)
        except (TypeError, ValueError) as exc:
            raise RulesError(f"Bad cancellation date for {name!r}: {when!r} (use YYYY-MM-DD)") from exc
    return Rules(
        ignore=list(data.get("ignore") or []),
        aliases=dict(data.get("aliases") or {}),
        cancelled=cancelled,
    )
