import json
import urllib.request

import pytest

from src import ai
from src.analytics import SectorPoint, SectorResult
from src.storage import QuadrantTransition


def _result(ticker, ratio, momentum, quadrant):
    point = SectorPoint(date="2026-01-01", rs_ratio=ratio, rs_momentum=momentum, quadrant=quadrant)
    return SectorResult(ticker=ticker, tail=[point], latest=point, previous=None)


@pytest.fixture
def snapshots():
    return {
        "A": _result("A", 105.0, 102.0, "Leading"),
        "B": _result("B", 95.0, 95.0, "Lagging"),
    }


@pytest.fixture
def transitions():
    return [
        QuadrantTransition(ticker="A", previous_quadrant="Improving", current_quadrant="Leading", changed=True),
        QuadrantTransition(ticker="B", previous_quadrant="Lagging", current_quadrant="Lagging", changed=False),
    ]


def test_no_api_key_returns_deterministic_commentary_without_network_call(monkeypatch, snapshots, transitions):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("urlopen should never be called with no API key")

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(urllib.request, "urlopen", fail_if_called)

    commentary = ai.generate_commentary(snapshots, transitions, api_key=None)
    assert "Leading: A" in commentary
    assert "Lagging: B" in commentary
    assert "A Improving -> Leading" in commentary


def test_explicit_empty_key_forces_deterministic_fallback(snapshots, transitions):
    commentary = ai.generate_commentary(snapshots, transitions, api_key="")
    assert "Leading: A" in commentary


def test_deterministic_commentary_first_run_has_no_prior_history():
    snap = {"A": _result("A", 100.0, 100.0, "Leading")}
    transitions = [QuadrantTransition(ticker="A", previous_quadrant=None, current_quadrant="Leading", changed=False)]
    commentary = ai.generate_commentary(snap, transitions, api_key="")
    assert "first recorded run" in commentary


def test_deterministic_commentary_no_changes_message():
    snap = {"A": _result("A", 100.0, 100.0, "Leading")}
    transitions = [QuadrantTransition(ticker="A", previous_quadrant="Leading", current_quadrant="Leading", changed=False)]
    commentary = ai.generate_commentary(snap, transitions, api_key="")
    assert "No sector changed quadrant" in commentary


def test_successful_anthropic_call_returns_ai_text(monkeypatch, snapshots, transitions):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"content": [{"type": "text", "text": "AI-written summary."}]}).encode("utf-8")

    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["headers"] = {k.lower(): v for k, v in request.headers.items()}
        return FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    commentary = ai.generate_commentary(snapshots, transitions, api_key="sk-test-key")
    assert commentary == "AI-written summary."
    assert captured["url"] == ai.ANTHROPIC_API_URL
    assert captured["headers"]["x-api-key"] == "sk-test-key"


def test_malformed_anthropic_response_falls_back(monkeypatch, snapshots, transitions):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b"not valid json"

    monkeypatch.setattr(urllib.request, "urlopen", lambda request, timeout=None: FakeResponse())

    commentary = ai.generate_commentary(snapshots, transitions, api_key="sk-test-key")
    assert "Leading: A" in commentary  # fell back to deterministic template


def test_network_error_falls_back(monkeypatch, snapshots, transitions):
    def raise_error(request, timeout=None):
        raise OSError("network unreachable")

    monkeypatch.setattr(urllib.request, "urlopen", raise_error)

    commentary = ai.generate_commentary(snapshots, transitions, api_key="sk-test-key")
    assert "Leading: A" in commentary


def test_summary_payload_never_includes_extra_sectors(snapshots, transitions):
    payload = json.loads(ai._build_summary_payload(snapshots, transitions))
    tickers = {row["ticker"] for row in payload["sectors"]}
    assert tickers == {"A", "B"}
