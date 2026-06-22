"""Tests for ai_synthesizer.py — prompt building and API integration."""
from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_synthesizer import format_prompt, synthesize


# Empty data stubs
_EMPTY_GITHUB = {"recent_repos": [], "stale_repos": [], "open_prs": []}
_EMPTY_PORTFOLIO = {
    "tickers": [], "total_up": 0, "total_down": 0, "total_flat": 0,
    "top_gainers": [], "top_losers": [],
}
_EMPTY_WEATHER = {"hours": [], "best_run": [], "best_golf": [], "best_boat": []}


# ---------------------------------------------------------------------------
# format_prompt
# ---------------------------------------------------------------------------

class TestFormatPrompt:
    def test_includes_github_section(self):
        prompt = format_prompt(
            {**_EMPTY_GITHUB, "recent_repos": [{"name": "u/repo"}]},
            _EMPTY_PORTFOLIO,
            _EMPTY_WEATHER,
        )
        assert "GitHub" in prompt

    def test_includes_portfolio_section(self):
        prompt = format_prompt(
            _EMPTY_GITHUB,
            {**_EMPTY_PORTFOLIO, "total_up": 3},
            _EMPTY_WEATHER,
        )
        assert "Portfolio" in prompt

    def test_includes_weather_section(self):
        prompt = format_prompt(_EMPTY_GITHUB, _EMPTY_PORTFOLIO, _EMPTY_WEATHER)
        assert "Toronto" in prompt

    def test_includes_repo_counts(self):
        github = {
            "recent_repos": [{"name": "a"}, {"name": "b"}],
            "stale_repos": [{"name": "c"}],
            "open_prs": [],
        }
        prompt = format_prompt(github, _EMPTY_PORTFOLIO, _EMPTY_WEATHER)
        assert "2" in prompt  # 2 recent repos

    def test_includes_portfolio_move_counts(self):
        portfolio = {**_EMPTY_PORTFOLIO, "total_up": 4, "total_down": 2, "total_flat": 0}
        prompt = format_prompt(_EMPTY_GITHUB, portfolio, _EMPTY_WEATHER)
        assert "4" in prompt

    def test_includes_top_gainer_when_present(self):
        portfolio = {
            **_EMPTY_PORTFOLIO,
            "top_gainers": [{"ticker": "NVDA", "formatted_change": "+5.2%"}],
        }
        prompt = format_prompt(_EMPTY_GITHUB, portfolio, _EMPTY_WEATHER)
        assert "NVDA" in prompt

    def test_includes_midday_weather_when_hours_present(self):
        weather = {
            **_EMPTY_WEATHER,
            "hours": [
                {
                    "hour": 12,
                    "time": "2026-06-22T12:00",
                    "temp_c": 23.5,
                    "wind_kph": 12.0,
                    "precip_prob": 10.0,
                    "scores": {"run": 80, "golf": 75, "boat": 70},
                }
            ],
        }
        prompt = format_prompt(_EMPTY_GITHUB, _EMPTY_PORTFOLIO, weather)
        assert "23.5" in prompt


# ---------------------------------------------------------------------------
# synthesize
# ---------------------------------------------------------------------------

class TestSynthesize:
    def test_returns_empty_string_without_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        result = synthesize(_EMPTY_GITHUB, _EMPTY_PORTFOLIO, _EMPTY_WEATHER)
        assert result == ""

    def test_returns_empty_string_on_api_error(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        with patch("ai_synthesizer.urllib.request.urlopen", side_effect=Exception("refused")):
            result = synthesize(_EMPTY_GITHUB, _EMPTY_PORTFOLIO, _EMPTY_WEATHER)
        assert result == ""

    def test_returns_text_on_successful_response(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        import json
        fake_body = json.dumps({
            "content": [{"type": "text", "text": "• Focus on NVDA earnings\n• Run at 7am"}]
        }).encode()
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.read = lambda: fake_body
        with patch("ai_synthesizer.urllib.request.urlopen", return_value=mock_resp):
            result = synthesize(_EMPTY_GITHUB, _EMPTY_PORTFOLIO, _EMPTY_WEATHER)
        assert "NVDA" in result

    def test_returns_empty_when_content_field_missing(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        import json
        fake_body = json.dumps({"id": "msg_123"}).encode()
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.read = lambda: fake_body
        with patch("ai_synthesizer.urllib.request.urlopen", return_value=mock_resp):
            result = synthesize(_EMPTY_GITHUB, _EMPTY_PORTFOLIO, _EMPTY_WEATHER)
        assert result == ""
