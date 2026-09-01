"""Latest-version lookups against the real PyPI and npm registry APIs.

Both are free, public, no-auth JSON APIs (PyPI's per-project JSON endpoint,
npm's registry document). A lookup failure of any kind — 404, malformed
JSON, connection error — degrades to ``None`` rather than raising, since one
unpublished or renamed package should never abort a fleet-wide sync.
"""
from __future__ import annotations

import json
import urllib.parse
from typing import Optional

from .http import Transport, default_transport

_HEADERS = {"User-Agent": "fleet-drift/1.0 (nightly-build tool)"}


def fetch_latest_pypi(name: str, transport: Transport = default_transport) -> Optional[str]:
    url = f"https://pypi.org/pypi/{urllib.parse.quote(name)}/json"
    try:
        status, body = transport(url, _HEADERS)
    except Exception:
        return None
    if status != 200:
        return None
    try:
        data = json.loads(body.decode("utf-8"))
        version = data.get("info", {}).get("version")
        return version if isinstance(version, str) else None
    except (json.JSONDecodeError, AttributeError, UnicodeDecodeError):
        return None


def fetch_latest_npm(name: str, transport: Transport = default_transport) -> Optional[str]:
    url = f"https://registry.npmjs.org/{urllib.parse.quote(name, safe='@/')}"
    try:
        status, body = transport(url, _HEADERS)
    except Exception:
        return None
    if status != 200:
        return None
    try:
        data = json.loads(body.decode("utf-8"))
        version = data.get("dist-tags", {}).get("latest")
        return version if isinstance(version, str) else None
    except (json.JSONDecodeError, AttributeError, UnicodeDecodeError):
        return None


def fetch_latest(ecosystem: str, name: str, transport: Transport = default_transport) -> Optional[str]:
    if ecosystem == "python":
        return fetch_latest_pypi(name, transport)
    if ecosystem == "npm":
        return fetch_latest_npm(name, transport)
    raise ValueError(f"Unknown ecosystem: {ecosystem}")
