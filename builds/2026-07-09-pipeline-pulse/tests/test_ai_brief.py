import json

import ai_brief


def make_summary(backlog_count=3, total=10, oldest_days=15, oldest_title="Old One",
                  rating_coverage_pct=30.0, rated_count=3, average_rating=6.0):
    return {
        "total": total,
        "merged_count": total - backlog_count,
        "backlog_count": backlog_count,
        "merged_pct": (total - backlog_count) / total * 100 if total else 0,
        "backlog_pct": backlog_count / total * 100 if total else 0,
        "oldest_unmerged": (
            {"title": oldest_title, "date": "2026-06-24", "backlog_days": oldest_days}
            if backlog_count
            else None
        ),
        "rated_count": rated_count,
        "rating_coverage_pct": rating_coverage_pct,
        "average_rating": average_rating,
        "category_distribution": {"A": 2},
        "complexity_distribution": {"ambitious": 3},
        "status_distribution": {"complete": 3},
        "rating_trend": [],
        "needs_attention": [],
    }


def test_deterministic_brief_mentions_backlog_count_and_oldest():
    summary = make_summary(backlog_count=3, oldest_title="Schema Sentinel", oldest_days=21)
    text = ai_brief.deterministic_brief(summary)
    assert "3" in text
    assert "Schema Sentinel" in text
    assert "21" in text


def test_deterministic_brief_all_merged_case():
    summary = make_summary(backlog_count=0)
    text = ai_brief.deterministic_brief(summary)
    assert "All 10" in text or "merged" in text.lower()


def test_deterministic_brief_low_rating_coverage_mentioned():
    summary = make_summary(rating_coverage_pct=20.0)
    text = ai_brief.deterministic_brief(summary)
    assert "rated" in text.lower()


def test_generate_brief_without_api_key_uses_deterministic(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    summary = make_summary()

    def fetch_should_not_be_called(url, payload, headers):
        raise AssertionError("fetch should not be called without an API key")

    result = ai_brief.generate_brief(summary, fetch=fetch_should_not_be_called)
    assert result == ai_brief.deterministic_brief(summary)


def test_generate_brief_uses_successful_api_response(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    summary = make_summary()

    def fake_fetch(url, payload, headers):
        return json.dumps({"content": [{"text": "Custom AI briefing text."}]}).encode("utf-8")

    result = ai_brief.generate_brief(summary, fetch=fake_fetch)
    assert result == "Custom AI briefing text."


def test_generate_brief_falls_back_on_fetch_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    summary = make_summary()

    def failing_fetch(url, payload, headers):
        raise OSError("network unreachable")

    result = ai_brief.generate_brief(summary, fetch=failing_fetch)
    assert result == ai_brief.deterministic_brief(summary)


def test_generate_brief_falls_back_on_malformed_response(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    summary = make_summary()

    def malformed_fetch(url, payload, headers):
        return b"not json"

    result = ai_brief.generate_brief(summary, fetch=malformed_fetch)
    assert result == ai_brief.deterministic_brief(summary)
