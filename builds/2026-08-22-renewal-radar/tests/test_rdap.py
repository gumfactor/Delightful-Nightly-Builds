import json
import urllib.error

import pytest

from src import rdap


class FakeResponse:
    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._body


def make_urlopen(bootstrap_payload=None, domain_payload=None, raise_on_domain=False):
    def _urlopen(request, timeout):
        url = request.full_url
        if "dns.json" in url:
            return FakeResponse(bootstrap_payload)
        if raise_on_domain:
            raise urllib.error.URLError("connection refused")
        return FakeResponse(domain_payload)

    return _urlopen


BOOTSTRAP = {"services": [[["com", "net"], ["https://rdap.example-registry.test/"]]]}

DOMAIN_RESPONSE_WITH_EXPIRATION = {
    "events": [
        {"eventAction": "registration", "eventDate": "2020-01-01T00:00:00Z"},
        {"eventAction": "expiration", "eventDate": "2027-06-15T00:00:00Z"},
    ],
    "entities": [
        {
            "roles": ["registrar"],
            "vcardArray": ["vcard", [["version", {}, "text", "4.0"], ["fn", {}, "text", "Example Registrar Inc."]]],
        }
    ],
}


def test_successful_lookup_returns_expiration_and_registrar():
    urlopen = make_urlopen(bootstrap_payload=BOOTSTRAP, domain_payload=DOMAIN_RESPONSE_WITH_EXPIRATION)
    result = rdap.lookup_domain("example.com", urlopen=urlopen)
    assert result["status"] == "ok"
    assert result["expiration"] == "2027-06-15"
    assert result["registrar"] == "Example Registrar Inc."


def test_bootstrap_fetch_failure_degrades_to_unknown():
    def failing_urlopen(request, timeout):
        raise urllib.error.URLError("no network")

    result = rdap.lookup_domain("example.com", urlopen=failing_urlopen)
    assert result["status"] == "unknown"
    assert "bootstrap fetch failed" in result["error"]


def test_unsupported_tld_degrades_to_unknown():
    urlopen = make_urlopen(bootstrap_payload=BOOTSTRAP)
    result = rdap.lookup_domain("example.zzz", urlopen=urlopen)
    assert result["status"] == "unknown"
    assert "No RDAP server registered" in result["error"]


def test_single_label_domain_degrades_to_unknown_without_network_call():
    call_count = {"n": 0}

    def urlopen(request, timeout):
        call_count["n"] += 1
        return FakeResponse(BOOTSTRAP)

    result = rdap.lookup_domain("localhost", urlopen=urlopen)
    assert result["status"] == "unknown"
    assert call_count["n"] == 0


def test_domain_query_failure_degrades_to_unknown():
    urlopen = make_urlopen(bootstrap_payload=BOOTSTRAP, raise_on_domain=True)
    result = rdap.lookup_domain("example.com", urlopen=urlopen)
    assert result["status"] == "unknown"
    assert "RDAP query" in result["error"]


def test_response_with_no_expiration_event_returns_none_expiration():
    payload = {"events": [{"eventAction": "registration", "eventDate": "2020-01-01T00:00:00Z"}], "entities": []}
    urlopen = make_urlopen(bootstrap_payload=BOOTSTRAP, domain_payload=payload)
    result = rdap.lookup_domain("example.com", urlopen=urlopen)
    assert result["status"] == "ok"
    assert result["expiration"] is None


def test_bootstrap_can_be_injected_directly_skipping_fetch():
    result = rdap.lookup_domain(
        "example.com",
        urlopen=make_urlopen(domain_payload=DOMAIN_RESPONSE_WITH_EXPIRATION),
        bootstrap={"com": ["https://rdap.example-registry.test/"]},
    )
    assert result["status"] == "ok"
    assert result["expiration"] == "2027-06-15"
