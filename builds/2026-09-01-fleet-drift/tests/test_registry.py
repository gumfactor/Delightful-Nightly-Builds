import json

from src.registry import fetch_latest, fetch_latest_npm, fetch_latest_pypi


def _transport_for(status, body_dict):
    def transport(url, headers, method="GET", data=None):
        return status, json.dumps(body_dict).encode("utf-8")
    return transport


def test_fetch_latest_pypi_success():
    transport = _transport_for(200, {"info": {"version": "2.31.0"}})
    assert fetch_latest_pypi("requests", transport=transport) == "2.31.0"


def test_fetch_latest_pypi_404_returns_none():
    def transport(url, headers, method="GET", data=None):
        return 404, b"Not Found"
    assert fetch_latest_pypi("does-not-exist", transport=transport) is None


def test_fetch_latest_pypi_malformed_json_returns_none():
    def transport(url, headers, method="GET", data=None):
        return 200, b"not json"
    assert fetch_latest_pypi("requests", transport=transport) is None


def test_fetch_latest_pypi_connection_failure_returns_none():
    def transport(url, headers, method="GET", data=None):
        return None, b""
    assert fetch_latest_pypi("requests", transport=transport) is None


def test_fetch_latest_npm_success():
    transport = _transport_for(200, {"dist-tags": {"latest": "18.3.1"}})
    assert fetch_latest_npm("react", transport=transport) == "18.3.1"


def test_fetch_latest_npm_404_returns_none():
    def transport(url, headers, method="GET", data=None):
        return 404, b"Not Found"
    assert fetch_latest_npm("does-not-exist", transport=transport) is None


def test_fetch_latest_dispatches_by_ecosystem():
    transport = _transport_for(200, {"info": {"version": "1.0.0"}})
    assert fetch_latest("python", "requests", transport=transport) == "1.0.0"


def test_fetch_latest_unknown_ecosystem_raises():
    try:
        fetch_latest("rust", "serde")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_fetch_latest_npm_scoped_package_name_is_url_encoded():
    seen_urls = []

    def transport(url, headers, method="GET", data=None):
        seen_urls.append(url)
        return 200, json.dumps({"dist-tags": {"latest": "1.0.0"}}).encode("utf-8")

    fetch_latest_npm("@scope/pkg", transport=transport)
    assert seen_urls[0] == "https://registry.npmjs.org/@scope/pkg"
