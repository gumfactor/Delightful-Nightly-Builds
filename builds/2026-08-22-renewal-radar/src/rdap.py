"""RDAP domain-expiration lookups via the official IANA RDAP bootstrap registry.

RDAP (RFC 9082/9083) is the modern, structured, standardized replacement for
WHOIS text scraping. Rather than depending on a single third-party proxy, this
module fetches IANA's own bootstrap file to find the authoritative RDAP
server(s) for a domain's TLD, then queries that server directly.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import date, datetime
from typing import Any, Callable, Optional

BOOTSTRAP_URL = "https://data.iana.org/rdap/dns.json"
REQUEST_TIMEOUT_SECONDS = 8
USER_AGENT = "RenewalRadar/1.0 (personal admin tool; no-auth RDAP client)"

UrlOpener = Callable[[urllib.request.Request, int], Any]


def _default_urlopen(request: urllib.request.Request, timeout: int) -> Any:
    return urllib.request.urlopen(request, timeout=timeout)


def _fetch_json(url: str, urlopen: UrlOpener) -> dict:
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    with urlopen(request, REQUEST_TIMEOUT_SECONDS) as response:
        raw = response.read()
    return json.loads(raw.decode("utf-8"))


def fetch_bootstrap(urlopen: UrlOpener = _default_urlopen) -> dict[str, list[str]]:
    """Fetch and flatten the IANA RDAP bootstrap registry into {tld: [server_urls]}."""
    data = _fetch_json(BOOTSTRAP_URL, urlopen)
    tld_map: dict[str, list[str]] = {}
    for entry in data.get("services", []):
        if len(entry) != 2:
            continue
        tlds, servers = entry
        for tld in tlds:
            tld_map[tld.lower()] = list(servers)
    return tld_map


def _extract_tld(domain: str) -> str:
    parts = domain.strip().lower().rstrip(".").split(".")
    if len(parts) < 2:
        raise ValueError(f"'{domain}' does not look like a registrable domain (no TLD)")
    return parts[-1]


def _parse_expiration(rdap_response: dict) -> Optional[str]:
    for event in rdap_response.get("events", []):
        if event.get("eventAction") in ("expiration", "registration expiration"):
            raw_date = event.get("eventDate")
            if not raw_date:
                continue
            try:
                parsed = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            except ValueError:
                continue
            return parsed.date().isoformat()
    return None


def _parse_registrar(rdap_response: dict) -> Optional[str]:
    for entity in rdap_response.get("entities", []):
        if "registrar" not in entity.get("roles", []):
            continue
        vcard = entity.get("vcardArray")
        if not vcard or len(vcard) < 2:
            continue
        for field in vcard[1]:
            if len(field) >= 4 and field[0] == "fn":
                return str(field[3])
    return None


def lookup_domain(
    domain: str,
    urlopen: UrlOpener = _default_urlopen,
    bootstrap: Optional[dict[str, list[str]]] = None,
) -> dict:
    """Look up a domain's registration expiration via RDAP.

    Returns a dict with keys: status ('ok' | 'unknown'), expiration (ISO date
    or None), registrar (str or None), error (str or None). Never raises —
    any failure (unsupported TLD, network error, malformed response) degrades
    to status='unknown' with an explanatory error message.
    """
    result = {"status": "unknown", "expiration": None, "registrar": None, "error": None}
    try:
        tld = _extract_tld(domain)
    except ValueError as exc:
        result["error"] = str(exc)
        return result

    try:
        tld_servers = bootstrap if bootstrap is not None else fetch_bootstrap(urlopen)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        result["error"] = f"RDAP bootstrap fetch failed: {exc}"
        return result

    servers = tld_servers.get(tld)
    if not servers:
        result["error"] = f"No RDAP server registered for TLD '.{tld}'"
        return result

    last_error: Optional[str] = None
    for server in servers:
        base = server.rstrip("/")
        query_url = f"{base}/domain/{domain.strip().lower().rstrip('.')}"
        try:
            response = _fetch_json(query_url, urlopen)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            last_error = f"RDAP query to {base} failed: {exc}"
            continue
        result["status"] = "ok"
        result["expiration"] = _parse_expiration(response)
        result["registrar"] = _parse_registrar(response)
        return result

    result["error"] = last_error or "All RDAP servers for this TLD failed"
    return result
