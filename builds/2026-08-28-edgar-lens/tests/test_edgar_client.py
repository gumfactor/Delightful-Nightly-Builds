import json

import pytest

from src import edgar_client


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = json.dumps(payload).encode("utf-8")
        self.status = status

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def fake_urlopen_factory(payload, status=200, captured_requests=None):
    def fake_urlopen(request, timeout=None):
        if captured_requests is not None:
            captured_requests.append(request)
        return FakeResponse(payload, status)

    return fake_urlopen


def raising_urlopen(*args, **kwargs):
    raise OSError("connection refused")


def malformed_json_urlopen(request, timeout=None):
    class BadResponse:
        status = 200

        def read(self):
            return b"not json{{{"

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

    return BadResponse()


def test_fetch_json_returns_parsed_payload():
    result = edgar_client.fetch_json(
        "https://example.com/data.json", "TestUA/1.0", fake_urlopen_factory({"hello": "world"})
    )
    assert result == {"hello": "world"}


def test_fetch_json_sets_user_agent_header():
    captured = []
    edgar_client.fetch_json(
        "https://example.com/data.json", "MyApp/1.0 (test@example.com)",
        fake_urlopen_factory({"ok": True}, captured_requests=captured),
    )
    assert captured[0].get_header("User-agent") == "MyApp/1.0 (test@example.com)"


def test_fetch_json_raises_on_non_200_status():
    with pytest.raises(edgar_client.EdgarClientError):
        edgar_client.fetch_json(
            "https://example.com/data.json", "TestUA/1.0",
            fake_urlopen_factory({"ok": True}, status=404),
        )


def test_fetch_json_raises_on_network_error():
    with pytest.raises(edgar_client.EdgarClientError):
        edgar_client.fetch_json("https://example.com/data.json", "TestUA/1.0", raising_urlopen)


def test_fetch_json_raises_on_malformed_json():
    with pytest.raises(edgar_client.EdgarClientError):
        edgar_client.fetch_json("https://example.com/data.json", "TestUA/1.0", malformed_json_urlopen)


def test_fetch_company_tickers_normalizes_mapping():
    raw = {
        "0": {"cik_str": 320193, "ticker": "aapl", "title": "Apple Inc."},
        "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
    }
    mapping = edgar_client.fetch_company_tickers("TestUA/1.0", fake_urlopen_factory(raw))
    assert mapping["AAPL"] == {"cik": "0000320193", "title": "Apple Inc."}
    assert mapping["MSFT"]["cik"] == "0000789019"


def test_resolve_ticker_found_and_missing():
    mapping = {"AAPL": {"cik": "0000320193", "title": "Apple Inc."}}
    assert edgar_client.resolve_ticker("aapl", mapping) == {"cik": "0000320193", "title": "Apple Inc."}
    assert edgar_client.resolve_ticker("ZZZZ", mapping) is None


def test_fetch_companyfacts_builds_correct_url():
    captured = []
    edgar_client.fetch_companyfacts(
        "0000320193", "TestUA/1.0", fake_urlopen_factory({"cik": 320193}, captured_requests=captured)
    )
    assert captured[0].full_url == "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"


def test_rate_limit_sleep_calls_sleep_with_configured_delay():
    calls = []
    edgar_client.rate_limit_sleep(sleep_func=calls.append)
    assert calls == [edgar_client.RATE_LIMIT_DELAY_SECONDS]


def test_default_user_agent_contains_no_real_personal_email():
    # STANDARDS.md forbids hardcoding real personal data; the default must
    # stay a generic placeholder, not the user's real address.
    assert "@example.com" in edgar_client.DEFAULT_USER_AGENT
    assert "mshane" not in edgar_client.DEFAULT_USER_AGENT.lower()
