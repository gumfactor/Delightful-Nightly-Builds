"""Shared data model for CanEcon Pulse."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Observation:
    """A single dated value for one economic indicator."""

    series_id: str
    series_label: str
    unit: str
    source: str
    obs_date: date
    value: float
