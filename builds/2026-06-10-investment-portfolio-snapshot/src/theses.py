"""Investment thesis note storage — local JSON persistence, per-ticker CRUD."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class ThesisStore:
    """Read/write investment thesis notes to a local JSON file."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._data: dict[str, list[dict]] = self._load()

    def _load(self) -> dict[str, list[dict]]:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                # Back up the malformed file before starting fresh so no notes are lost silently.
                backup = self.path.with_suffix(".json.bak")
                try:
                    backup.write_bytes(self.path.read_bytes())
                except OSError:
                    pass
                return {}
        return {}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def add(self, ticker: str, note: str, price: Optional[float] = None) -> dict:
        """Add a note for a ticker; returns the created entry."""
        ticker = ticker.upper()
        if ticker not in self._data:
            self._data[ticker] = []
        entries = self._data[ticker]
        entry_id = max((e["id"] for e in entries), default=0) + 1
        entry: dict = {
            "id": entry_id,
            "date": datetime.now(timezone.utc).isoformat(),
            "note": note,
            "price_at_note": price,
        }
        entries.append(entry)
        self._save()
        return entry

    def get(self, ticker: str) -> list[dict]:
        """Return all notes for a ticker, oldest first."""
        return [dict(e) for e in self._data.get(ticker.upper(), [])]

    def get_latest(self, ticker: str) -> Optional[dict]:
        """Return the most recent note for a ticker, or None."""
        entries = self._data.get(ticker.upper(), [])
        return dict(entries[-1]) if entries else None

    def list_tickers(self) -> list[tuple[str, int, str]]:
        """Return (ticker, note_count, last_date_iso) sorted alphabetically."""
        result = []
        for ticker, entries in sorted(self._data.items()):
            if entries:
                last_date = max(e["date"] for e in entries)
                result.append((ticker, len(entries), last_date))
        return result

    def search(self, query: str) -> list[tuple[str, dict]]:
        """Return (ticker, entry) pairs where the note contains query (case-insensitive)."""
        q = query.lower()
        results = []
        for ticker, entries in sorted(self._data.items()):
            for entry in entries:
                if q in entry["note"].lower():
                    results.append((ticker, dict(entry)))
        return results

    def delete(self, ticker: str, entry_id: int) -> bool:
        """Delete a note by ticker + ID. Returns True if a note was removed."""
        ticker = ticker.upper()
        before = len(self._data.get(ticker, []))
        self._data[ticker] = [e for e in self._data.get(ticker, []) if e["id"] != entry_id]
        if not self._data.get(ticker):
            self._data.pop(ticker, None)
        removed = len(self._data.get(ticker, [])) < before
        if removed:
            self._save()
        return removed

    def all_data(self) -> dict[str, list[dict]]:
        """Return a deep copy of the full data dict (ticker → entries)."""
        return {k: [dict(e) for e in v] for k, v in self._data.items()}
