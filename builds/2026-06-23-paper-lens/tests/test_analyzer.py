"""Tests for analyzer.py — AI analysis prompt building and response parsing."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analyzer import build_analysis_prompt, _parse_analysis_response, _default_analysis, analyze_papers, ABSTRACT_TRUNCATE

_SAMPLE_PAPERS = [
    {
        "arxiv_id": "2410.00001",
        "title": "Neural Correlates of Empathy",
        "abstract": "A" * 800,
        "authors": "Smith, Jones",
        "published_date": "2024-10-01",
    },
    {
        "arxiv_id": "2410.00002",
        "title": "Autonomous LLM Agents",
        "abstract": "Short abstract.",
        "authors": "Brown",
        "published_date": "2024-10-02",
    },
]

_VALID_RESPONSE = (
    '[{"arxiv_id":"2410.00001","relevance":8,"summary":"Examines empathy in neural terms.",'
    '"methodology":"fMRI","topic":"empathy neural correlates"},'
    '{"arxiv_id":"2410.00002","relevance":6,"summary":"Explores AI agents.","methodology":"ML","topic":"AI agents"}]'
)


def test_build_prompt_contains_all_titles():
    prompt = build_analysis_prompt(_SAMPLE_PAPERS)
    assert "Neural Correlates of Empathy" in prompt
    assert "Autonomous LLM Agents" in prompt


def test_build_prompt_truncates_long_abstract():
    prompt = build_analysis_prompt(_SAMPLE_PAPERS)
    # Full abstract is 800 chars, should be truncated to ABSTRACT_TRUNCATE + "..."
    assert "..." in prompt
    # Should not contain more than ABSTRACT_TRUNCATE + a bit of overhead
    truncated_abstract = "A" * ABSTRACT_TRUNCATE + "..."
    assert truncated_abstract in prompt


def test_build_prompt_includes_short_abstract_verbatim():
    prompt = build_analysis_prompt(_SAMPLE_PAPERS)
    assert "Short abstract." in prompt


def test_parse_valid_json_response():
    results = _parse_analysis_response(_VALID_RESPONSE, _SAMPLE_PAPERS)
    assert "2410.00001" in results
    assert results["2410.00001"]["relevance_score"] == 8
    assert results["2410.00001"]["methodology"] == "fMRI"
    assert "2410.00002" in results
    assert results["2410.00002"]["relevance_score"] == 6


def test_parse_malformed_json_returns_defaults():
    bad_response = "This is not JSON at all."
    results = _parse_analysis_response(bad_response, _SAMPLE_PAPERS)
    # Should fall back to defaults
    assert "2410.00001" in results
    assert results["2410.00001"]["relevance_score"] == 5


def test_no_api_key_returns_defaults():
    results = analyze_papers(_SAMPLE_PAPERS, api_key="")
    assert "2410.00001" in results
    assert results["2410.00001"]["relevance_score"] == 5


def test_default_analysis_has_all_fields():
    paper = {
        "arxiv_id": "2410.99999",
        "title": "Test Paper",
        "abstract": "Test abstract.",
        "authors": "Author",
        "published_date": "2024-10-01",
    }
    result = _default_analysis(paper)
    assert "relevance_score" in result
    assert "summary" in result
    assert "methodology" in result
    assert "topic_label" in result


def test_analyze_papers_empty_list_returns_empty():
    results = analyze_papers([], api_key="fake-key")
    assert results == {}


def test_parse_response_clamps_relevance_to_valid_range():
    # Relevance out of range should be clamped
    response = '[{"arxiv_id":"2410.00001","relevance":15,"summary":"Test.","methodology":"fMRI","topic":"test"}]'
    results = _parse_analysis_response(response, _SAMPLE_PAPERS[:1])
    assert results["2410.00001"]["relevance_score"] <= 10


def test_parse_response_ignores_unknown_arxiv_ids():
    response = '[{"arxiv_id":"9999.99999","relevance":9,"summary":"Unknown.","methodology":"other","topic":"x"}]'
    results = _parse_analysis_response(response, _SAMPLE_PAPERS)
    # Should not crash; known papers still get defaults
    assert "2410.00001" in results
