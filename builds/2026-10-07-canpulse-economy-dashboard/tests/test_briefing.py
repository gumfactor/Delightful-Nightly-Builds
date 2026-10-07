from canpulse import briefing

SERIES = {"cpi": {"label": "CPI"}, "policy_rate": {"label": "BoC policy rate"}, "unemployment": {"label": "Unemployment"}}
STATS = {
    "cpi": {"latest": 160.0, "latest_date": "2026-08-01", "yoy": 4.2, "yoy_kind": "pct", "trend": "rising", "pct5y": 90, "signal": "neutral", "reason": "Rising"},
    "policy_rate": {"latest": 2.75, "latest_date": "2026-09-01", "yoy": -1.0, "yoy_kind": "pp", "trend": "falling", "pct5y": 30, "signal": "neutral", "reason": "Falling"},
    "unemployment": {"latest": 7.1, "latest_date": "2026-08-01", "yoy": 0.8, "yoy_kind": "pp", "trend": "rising", "pct5y": 85, "signal": "bad", "reason": "Worsening"},
}


def test_rule_based_mentions_target_band_and_flags():
    text = " ".join(briefing.rule_based(SERIES, STATS))
    assert "above the BoC's 1–3% target band" in text and "Unemployment: Worsening" in text


def test_no_key_uses_rules_without_calling_api():
    def boom(*a):
        raise AssertionError("should not call API")

    out = briefing.ai_briefing(SERIES, STATS, api_key="", post=boom)
    assert out["source"] == "rules" and out["error"] is None


def test_ai_success_returns_lines_and_sends_only_aggregates():
    sent = {}

    def fake(url, headers, payload):
        sent.update(headers=headers, payload=payload)
        return {"content": [{"type": "text", "text": "Line one.\nLine two."}]}

    out = briefing.ai_briefing(SERIES, STATS, api_key="k", post=fake)
    assert out["source"] == "ai" and out["lines"] == ["Line one.", "Line two."]
    assert sent["headers"]["x-api-key"] == "k"
    assert "CPI" in sent["payload"]["messages"][0]["content"]


def test_ai_failure_falls_back_to_rules_with_error():
    def fail(*a):
        raise OSError("403")

    out = briefing.ai_briefing(SERIES, STATS, api_key="k", post=fail)
    assert out["source"] == "rules" and "OSError" in out["error"] and out["lines"]


def test_ai_empty_response_falls_back():
    out = briefing.ai_briefing(SERIES, STATS, api_key="k", post=lambda *a: {"content": []})
    assert out["source"] == "rules"
