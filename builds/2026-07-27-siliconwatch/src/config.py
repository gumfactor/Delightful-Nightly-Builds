"""Ticker/subsector configuration for SiliconWatch."""
import json
from pathlib import Path
from typing import List, Dict, Optional

DEFAULT_TICKERS: List[Dict[str, str]] = [
    {"ticker": "NVDA", "name": "NVIDIA Corporation", "subsector": "GPU / AI Accelerators"},
    {"ticker": "AMD", "name": "Advanced Micro Devices", "subsector": "GPU / AI Accelerators"},
    {"ticker": "AVGO", "name": "Broadcom Inc.", "subsector": "Custom Silicon / Networking"},
    {"ticker": "MRVL", "name": "Marvell Technology", "subsector": "Custom Silicon / Networking"},
    {"ticker": "TSM", "name": "Taiwan Semiconductor Manufacturing", "subsector": "Foundry / IDM"},
    {"ticker": "INTC", "name": "Intel Corporation", "subsector": "Foundry / IDM"},
    {"ticker": "ASML", "name": "ASML Holding", "subsector": "Equipment / EDA"},
    {"ticker": "AMAT", "name": "Applied Materials", "subsector": "Equipment / EDA"},
    {"ticker": "LRCX", "name": "Lam Research", "subsector": "Equipment / EDA"},
    {"ticker": "MU", "name": "Micron Technology", "subsector": "Memory"},
    {"ticker": "ARM", "name": "Arm Holdings", "subsector": "IP / Architecture & Analog"},
    {"ticker": "TXN", "name": "Texas Instruments", "subsector": "IP / Architecture & Analog"},
]

REQUIRED_FIELDS = {"ticker", "name", "subsector"}


class ConfigError(ValueError):
    """Raised when a ticker config file is missing or malformed."""


def load_tickers(config_path: Optional[str] = None) -> List[Dict[str, str]]:
    """Load the ticker/subsector list, falling back to the curated default.

    Raises ConfigError if config_path is given but missing or malformed.
    """
    if config_path is None:
        return list(DEFAULT_TICKERS)

    path = Path(config_path)
    if not path.is_file():
        raise ConfigError(f"Config file not found: {config_path}")

    try:
        raw = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Config file is not valid JSON: {exc}") from exc

    if not isinstance(raw, list) or not raw:
        raise ConfigError("Config file must contain a non-empty JSON array of ticker entries")

    tickers = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict) or not REQUIRED_FIELDS.issubset(entry.keys()):
            raise ConfigError(
                f"Config entry {i} must be an object with 'ticker', 'name', and 'subsector'"
            )
        tickers.append(
            {
                "ticker": str(entry["ticker"]).upper(),
                "name": str(entry["name"]),
                "subsector": str(entry["subsector"]),
            }
        )
    return tickers
