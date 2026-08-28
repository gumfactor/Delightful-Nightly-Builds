"""SEC EDGAR HTTP layer: ticker->CIK resolution and companyfacts fetch.

SEC's fair-access policy asks API clients to self-identify via a
descriptive User-Agent header. STANDARDS.md forbids hardcoding real
personal data (including a real email), so the default here is a
generic, non-personal placeholder -- override it with --user-agent or
the EDGAR_USER_AGENT environment variable for your own runtime use.

Every network call goes through fetch_json(), which accepts an injectable
urlopen_func so tests never make a real HTTP request.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Callable

COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
COMPANY_FACTS_URL_TEMPLATE = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

DEFAULT_USER_AGENT = "EDGARLens/1.0 (contact: set-your-email@example.com)"

# SEC asks clients to stay under ~10 requests/second.
RATE_LIMIT_DELAY_SECONDS = 0.15


class EdgarClientError(Exception):
    """Raised on any network, HTTP-status, or JSON-parsing failure."""


def fetch_json(
    url: str,
    user_agent: str,
    urlopen_func: Callable[..., Any] = urllib.request.urlopen,
    timeout: float = 15.0,
) -> Any:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent, "Accept": "application/json"},
    )
    try:
        with urlopen_func(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            if status != 200:
                raise EdgarClientError(f"Unexpected HTTP status {status} for {url}")
            raw = response.read()
    except EdgarClientError:
        raise
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise EdgarClientError(f"Request failed for {url}: {exc}") from exc

    try:
        return json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise EdgarClientError(f"Malformed JSON from {url}: {exc}") from exc


def fetch_company_tickers(
    user_agent: str,
    urlopen_func: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, dict[str, str]]:
    """Fetch and normalize SEC's ticker->CIK index into TICKER -> {cik, title}."""
    raw = fetch_json(COMPANY_TICKERS_URL, user_agent, urlopen_func)
    mapping: dict[str, dict[str, str]] = {}
    for entry in raw.values():
        ticker = str(entry.get("ticker", "")).upper().strip()
        cik_raw = entry.get("cik_str")
        title = entry.get("title", "")
        if not ticker or cik_raw is None:
            continue
        mapping[ticker] = {"cik": str(cik_raw).zfill(10), "title": title}
    return mapping


def resolve_ticker(ticker: str, ticker_map: dict[str, dict[str, str]]) -> dict[str, str] | None:
    return ticker_map.get(ticker.upper().strip())


def fetch_companyfacts(
    cik: str,
    user_agent: str,
    urlopen_func: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any]:
    url = COMPANY_FACTS_URL_TEMPLATE.format(cik=cik)
    return fetch_json(url, user_agent, urlopen_func)


def rate_limit_sleep(
    sleep_func: Callable[[float], None] = time.sleep,
    delay: float = RATE_LIMIT_DELAY_SECONDS,
) -> None:
    sleep_func(delay)
