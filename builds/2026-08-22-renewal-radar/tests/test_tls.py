import socket
from datetime import date

import pytest

from src import tls


def test_successful_check_returns_expiration_and_days_remaining():
    def fake_fetch(hostname, port, timeout):
        return {"notAfter": "Jun 15 12:00:00 2027 GMT"}

    result = tls.check_certificate("example.com", today=date(2026, 8, 22), fetch_certificate=fake_fetch)
    assert result["status"] == "ok"
    assert result["expiration"] == "2027-06-15"
    assert result["days_remaining"] == (date(2027, 6, 15) - date(2026, 8, 22)).days


def test_connection_refused_degrades_to_unknown():
    def fake_fetch(hostname, port, timeout):
        raise ConnectionRefusedError("connection refused")

    result = tls.check_certificate("example.com", fetch_certificate=fake_fetch)
    assert result["status"] == "unknown"
    assert "TLS handshake" in result["error"]


def test_timeout_degrades_to_unknown():
    def fake_fetch(hostname, port, timeout):
        raise socket.timeout("timed out")

    result = tls.check_certificate("example.com", fetch_certificate=fake_fetch)
    assert result["status"] == "unknown"


def test_dns_resolution_failure_degrades_to_unknown():
    def fake_fetch(hostname, port, timeout):
        raise socket.gaierror("name resolution failed")

    result = tls.check_certificate("nonexistent.invalid", fetch_certificate=fake_fetch)
    assert result["status"] == "unknown"


def test_missing_not_after_field_degrades_to_unknown():
    def fake_fetch(hostname, port, timeout):
        return {}

    result = tls.check_certificate("example.com", fetch_certificate=fake_fetch)
    assert result["status"] == "unknown"
    assert "no notAfter" in result["error"]


def test_unparseable_not_after_degrades_to_unknown():
    def fake_fetch(hostname, port, timeout):
        return {"notAfter": "not-a-date"}

    result = tls.check_certificate("example.com", fetch_certificate=fake_fetch)
    assert result["status"] == "unknown"
    assert "Could not parse" in result["error"]


def test_expired_certificate_reports_negative_days_remaining():
    def fake_fetch(hostname, port, timeout):
        return {"notAfter": "Jan 1 00:00:00 2026 GMT"}

    result = tls.check_certificate("example.com", today=date(2026, 8, 22), fetch_certificate=fake_fetch)
    assert result["status"] == "ok"
    assert result["days_remaining"] < 0
