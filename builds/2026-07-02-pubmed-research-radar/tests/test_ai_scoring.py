"""Tests for src/ai_scoring.py — AI path, fallback path, and graceful degradation."""

import json
from unittest.mock import MagicMock, patch

from src.ai_scoring import score_article

ON_TOPIC_ARTICLE = {
    "title": "Empathy and emotion regulation in affective neuroscience",
    "abstract": "This study examines affective neuroscience and emotion processing in empathy tasks.",
}
OFF_TOPIC_ARTICLE = {
    "title": "Crop yield optimization in arid soil",
    "abstract": "This paper examines irrigation schedules for arid farmland.",
}
TOPIC_QUERY = '"affective neuroscience"[tiab] AND (emotion[tiab] OR affect[tiab])'


def _mock_anthropic_response(payload_dict):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "content": [{"type": "text", "text": json.dumps(payload_dict)}]
    }
    return mock_response


class TestFallbackScoring:
    def test_no_api_key_uses_fallback(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        result = score_article("Affective Neuroscience", TOPIC_QUERY, ON_TOPIC_ARTICLE)

        assert result.scoring_method == "fallback"
        assert result.ai_summary is None
        assert 1.0 <= result.relevance_score <= 10.0

    def test_fallback_scores_on_topic_article_higher_than_off_topic(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        on_topic_result = score_article("Affective Neuroscience", TOPIC_QUERY, ON_TOPIC_ARTICLE)
        off_topic_result = score_article("Affective Neuroscience", TOPIC_QUERY, OFF_TOPIC_ARTICLE)

        assert on_topic_result.relevance_score > off_topic_result.relevance_score

    def test_fallback_handles_empty_query_terms_without_crashing(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        result = score_article("Empty", "", ON_TOPIC_ARTICLE)

        assert result.relevance_score == 1.0


class TestAiScoring:
    @patch("src.ai_scoring.requests.post")
    def test_ai_path_used_and_parsed_when_key_present(self, mock_post, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
        mock_post.return_value = _mock_anthropic_response(
            {
                "relevance_score": 9,
                "summary": "This paper links amygdala reactivity to empathic accuracy.",
                "methodology_tag": "fMRI",
            }
        )

        result = score_article("Affective Neuroscience", TOPIC_QUERY, ON_TOPIC_ARTICLE)

        assert result.scoring_method == "ai"
        assert result.relevance_score == 9.0
        assert "amygdala" in result.ai_summary.lower()
        assert result.methodology_tag == "fMRI"

    @patch("src.ai_scoring.requests.post")
    def test_ai_path_sends_api_key_header(self, mock_post, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
        mock_post.return_value = _mock_anthropic_response(
            {"relevance_score": 5, "summary": "Summary.", "methodology_tag": "review"}
        )

        score_article("Affective Neuroscience", TOPIC_QUERY, ON_TOPIC_ARTICLE)

        headers = mock_post.call_args.kwargs["headers"]
        assert headers["x-api-key"] == "test-key-not-real"

    @patch("src.ai_scoring.requests.post")
    def test_malformed_ai_response_falls_back_gracefully(self, mock_post, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
        mock_post.return_value = _mock_anthropic_response({"unexpected": "shape, no score field"})

        result = score_article("Affective Neuroscience", TOPIC_QUERY, ON_TOPIC_ARTICLE)

        assert result.scoring_method == "fallback"

    @patch("src.ai_scoring.requests.post")
    def test_network_error_falls_back_gracefully(self, mock_post, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
        mock_post.side_effect = ConnectionError("simulated network failure")

        result = score_article("Affective Neuroscience", TOPIC_QUERY, ON_TOPIC_ARTICLE)

        assert result.scoring_method == "fallback"

    @patch("src.ai_scoring.requests.post")
    def test_ai_score_is_clamped_to_1_10_range(self, mock_post, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
        mock_post.return_value = _mock_anthropic_response(
            {"relevance_score": 15, "summary": "Summary.", "methodology_tag": "review"}
        )

        result = score_article("Affective Neuroscience", TOPIC_QUERY, ON_TOPIC_ARTICLE)

        assert result.relevance_score == 10.0
