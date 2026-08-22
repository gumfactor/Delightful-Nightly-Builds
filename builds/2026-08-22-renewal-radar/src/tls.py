"""Live TLS certificate expiration checks via a direct handshake.

Uses only the Python standard library (`ssl` + `socket`) — no external API
or service is involved. Connecting to a host on port 443 and reading the
peer certificate's `notAfter` field is the same thing a browser does when it
warns about an expiring certificate.
"""

from __future__ import annotations

import socket
import ssl
from datetime import date, datetime
from typing import Callable, Optional

CONNECT_TIMEOUT_SECONDS = 8
CERT_DATE_FORMAT = "%b %d %H:%M:%S %Y %Z"

# Signature: (hostname, port, timeout) -> peer certificate dict, as returned
# by ssl.SSLSocket.getpeercert(). Injectable for testing.
CertFetcher = Callable[[str, int, int], dict]


def _default_fetch_certificate(hostname: str, port: int, timeout: int) -> dict:
    context = ssl.create_default_context()
    with socket.create_connection((hostname, port), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as tls_sock:
            return tls_sock.getpeercert()


def _parse_not_after(not_after: str) -> date:
    return datetime.strptime(not_after, CERT_DATE_FORMAT).date()


def check_certificate(
    hostname: str,
    port: int = 443,
    today: Optional[date] = None,
    fetch_certificate: CertFetcher = _default_fetch_certificate,
) -> dict:
    """Check a hostname's live TLS certificate expiration.

    Returns a dict with keys: status ('ok' | 'unknown'), expiration (ISO
    date or None), days_remaining (int or None), error (str or None). Never
    raises — connection failures, timeouts, and handshake errors all degrade
    to status='unknown'.
    """
    result = {"status": "unknown", "expiration": None, "days_remaining": None, "error": None}
    hostname = hostname.strip().lower()
    check_date = today if today is not None else datetime.utcnow().date()

    try:
        cert = fetch_certificate(hostname, port, CONNECT_TIMEOUT_SECONDS)
    except (socket.timeout, socket.gaierror, ConnectionRefusedError, OSError, ssl.SSLError) as exc:
        result["error"] = f"TLS handshake to {hostname}:{port} failed: {exc}"
        return result

    not_after = cert.get("notAfter") if cert else None
    if not not_after:
        result["error"] = "Certificate response had no notAfter field"
        return result

    try:
        expiration_date = _parse_not_after(not_after)
    except ValueError as exc:
        result["error"] = f"Could not parse certificate expiration '{not_after}': {exc}"
        return result

    result["status"] = "ok"
    result["expiration"] = expiration_date.isoformat()
    result["days_remaining"] = (expiration_date - check_date).days
    return result
