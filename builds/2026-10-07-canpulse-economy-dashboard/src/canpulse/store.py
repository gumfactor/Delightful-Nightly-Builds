"""Disk cache of the last good fetch."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CACHE_PATH = DATA_DIR / "cache.json"
SAMPLE_PATH = DATA_DIR / "sample_data.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def save_cache(series: dict[str, dict], errors: dict[str, str], path: Path = CACHE_PATH) -> dict:
    doc = {"fetched_at": now_iso(), "sample": False, "series": series, "errors": errors}
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc), encoding="utf-8")
    tmp.replace(path)
    return doc


def load_cache(path: Path = CACHE_PATH) -> dict | None:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc.get("series"), dict) else None


def merge_with_cache(series: dict[str, dict], errors: dict[str, str],
                     cached: dict | None) -> tuple[dict[str, dict], dict[str, str]]:
    """Fall back to cached series for any indicator that failed this run."""
    merged = dict(series)
    if cached and not cached.get("sample"):
        for sid in errors:
            if sid in cached["series"] and sid not in merged:
                old = dict(cached["series"][sid])
                old["from_cache"] = True
                merged[sid] = old
    return merged, errors


def load_any(offline_ok: bool = True) -> dict[str, Any] | None:
    return load_cache() or (_load(SAMPLE_PATH) if offline_ok else None)


def _load(path: Path) -> dict | None:
    return load_cache(path)
