"""SEC EDGAR client: ticker lookup, companyfacts download, disk cache, throttling."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
MIN_INTERVAL = 0.15  # SEC fair-access limit is 10 requests/second

Fetcher = Callable[[str, dict], bytes]


class SecError(Exception):
    """Raised for any user-presentable SEC access failure."""


def user_agent_from_env() -> str:
    agent = os.environ.get("EDGAR_USER_AGENT", "").strip()
    if not agent:
        raise SecError(
            "EDGAR_USER_AGENT is not set. SEC requires a descriptive User-Agent with a "
            "contact address, e.g. export EDGAR_USER_AGENT='Your Name you@example.com'")
    return agent


def http_fetch(url: str, headers: dict) -> bytes:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


class SecClient:
    def __init__(self, user_agent: str, cache_dir: Path | None = None,
                 fetch: Fetcher = http_fetch, sleep: Callable[[float], None] = time.sleep,
                 retries: int = 3, refresh: bool = False) -> None:
        if not user_agent or "@" not in user_agent:
            raise SecError("User-Agent must include a contact email address (SEC policy).")
        self.user_agent = user_agent
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._fetch = fetch
        self._sleep = sleep
        self.retries = retries
        self.refresh = refresh
        self._last_request = 0.0
        self.network_calls = 0

    def _get_json(self, url: str, cache_name: str) -> dict:
        cache_file = self.cache_dir / cache_name if self.cache_dir else None
        if cache_file and cache_file.exists() and not self.refresh:
            try:
                return json.loads(cache_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass  # corrupt cache: fall through to re-download
        raw = self._request(url)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SecError(f"SEC returned invalid JSON for {url}") from exc
        if cache_file:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(data), encoding="utf-8")
        return data

    def _request(self, url: str) -> bytes:
        headers = {"User-Agent": self.user_agent, "Accept-Encoding": "identity"}
        last_error: Exception | None = None
        for attempt in range(self.retries):
            wait = MIN_INTERVAL - (time.monotonic() - self._last_request)
            if wait > 0:
                self._sleep(wait)
            self._last_request = time.monotonic()
            self.network_calls += 1
            try:
                return self._fetch(url, headers)
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code == 404:
                    raise SecError(f"SEC has no data at {url} (404)") from exc
                if exc.code not in (429, 500, 502, 503, 504):
                    raise SecError(f"SEC request failed with HTTP {exc.code}: {url}") from exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = exc
            self._sleep(2 ** attempt)
        raise SecError(f"SEC request failed after {self.retries} attempts: {url} ({last_error})")

    def ticker_map(self) -> dict[str, dict]:
        raw = self._get_json(TICKERS_URL, "company_tickers.json")
        entries = raw.values() if isinstance(raw, dict) else raw
        return {str(e["ticker"]).upper(): e for e in entries if "ticker" in e and "cik_str" in e}

    def resolve(self, ticker: str) -> tuple[int, str]:
        entry = self.ticker_map().get(ticker.strip().upper().replace(".", "-"))
        if entry is None:
            entry = self.ticker_map().get(ticker.strip().upper())
        if entry is None:
            raise SecError(f"Unknown ticker '{ticker}' (not in SEC company_tickers.json)")
        return int(entry["cik_str"]), str(entry.get("title", ticker))

    def company_facts(self, cik: int) -> dict:
        return self._get_json(FACTS_URL.format(cik=cik), f"CIK{cik:010d}.json")
