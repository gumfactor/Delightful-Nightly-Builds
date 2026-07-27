from ai_narrative import build_template_narrative, generate_narrative

AGGREGATES = {
    "total_market_cap": 5_000_000_000_000,
    "avg_pe_trailing": 42.5,
    "avg_profit_margin": 0.45,
    "growth_positive_count": 9,
    "companies_tracked": 12,
    "top_mover": {"ticker": "NVDA", "name": "NVIDIA Corporation", "pct": 85.2},
    "laggard": {"ticker": "INTC", "name": "Intel Corporation", "pct": -20.1},
}


def test_build_template_narrative_includes_key_numbers():
    text = build_template_narrative(AGGREGATES)
    assert "12" in text
    assert "NVIDIA Corporation" in text
    assert "Intel Corporation" in text
    assert "9" in text


def test_build_template_narrative_handles_missing_movers():
    aggregates = dict(AGGREGATES)
    aggregates["top_mover"] = None
    aggregates["laggard"] = None
    text = build_template_narrative(aggregates)
    assert isinstance(text, str) and len(text) > 0


def test_generate_narrative_no_api_key_uses_template(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    text, source = generate_narrative(AGGREGATES, api_key=None)
    assert source == "template"
    assert text == build_template_narrative(AGGREGATES)


def test_generate_narrative_success_uses_ai_response():
    def fake_post(api_key, aggregates):
        assert api_key == "test-key"
        return "The AI infrastructure buildout continues to accelerate."

    text, source = generate_narrative(AGGREGATES, api_key="test-key", http_post=fake_post)
    assert source == "ai"
    assert text == "The AI infrastructure buildout continues to accelerate."


def test_generate_narrative_network_error_falls_back():
    def failing_post(api_key, aggregates):
        raise ConnectionError("simulated network failure")

    text, source = generate_narrative(AGGREGATES, api_key="test-key", http_post=failing_post)
    assert source == "template"
    assert text == build_template_narrative(AGGREGATES)


def test_generate_narrative_malformed_response_falls_back():
    def bad_post(api_key, aggregates):
        return ""  # empty/blank response counts as malformed

    text, source = generate_narrative(AGGREGATES, api_key="test-key", http_post=bad_post)
    assert source == "template"


def test_generate_narrative_non_string_response_falls_back():
    def bad_post(api_key, aggregates):
        return {"unexpected": "shape"}

    text, source = generate_narrative(AGGREGATES, api_key="test-key", http_post=bad_post)
    assert source == "template"
