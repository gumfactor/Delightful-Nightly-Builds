"""Central config of tracked indicators.

Each indicator's fetch function and identifiers live in exactly one place
here, so a stale Statistics Canada vector ID (or a Bank of Canada series
rename) is a one-line fix rather than a hunt through fetch/storage/render
code. See BUILD_LOG.md for why this build could not verify these against
live traffic during the build session.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List

from src.boc_client import fetch_boc_series
from src.models import Observation
from src.statcan_client import fetch_statcan_vector


@dataclass(frozen=True)
class Indicator:
    series_id: str
    label: str
    unit: str
    source: str
    fetch: Callable[[int], List[Observation]]


INDICATORS: List[Indicator] = [
    Indicator(
        series_id="FXUSDCAD",
        label="USD/CAD Exchange Rate",
        unit="CAD per USD",
        source="Bank of Canada Valet",
        fetch=lambda recent: fetch_boc_series(
            "FXUSDCAD", "USD/CAD Exchange Rate", "CAD per USD", recent
        ),
    ),
    Indicator(
        series_id="FXEURCAD",
        label="EUR/CAD Exchange Rate",
        unit="CAD per EUR",
        source="Bank of Canada Valet",
        fetch=lambda recent: fetch_boc_series(
            "FXEURCAD", "EUR/CAD Exchange Rate", "CAD per EUR", recent
        ),
    ),
    Indicator(
        series_id="V39079",
        label="Bank of Canada Policy Interest Rate",
        unit="%",
        source="Bank of Canada Valet",
        fetch=lambda recent: fetch_boc_series(
            "V39079", "Bank of Canada Policy Interest Rate", "%", recent
        ),
    ),
    Indicator(
        series_id="STATCAN_V41690973",
        label="Canada All-Items CPI",
        unit="index (2002=100)",
        source="Statistics Canada WDS",
        fetch=lambda recent: fetch_statcan_vector(
            41690973, "Canada All-Items CPI", "index (2002=100)", recent
        ),
    ),
    Indicator(
        series_id="STATCAN_V2062815",
        label="Canada Unemployment Rate",
        unit="%",
        source="Statistics Canada WDS",
        fetch=lambda recent: fetch_statcan_vector(
            2062815, "Canada Unemployment Rate", "%", recent
        ),
    ),
]
