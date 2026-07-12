import json
import math
import urllib.error
from unittest.mock import MagicMock, patch

import extraction


def test_tokenize_lowercases_and_strips_stopwords():
    tokens = extraction.tokenize("The Quick Fox and the Lazy Dog")
    assert "the" not in tokens
    assert "and" not in tokens
    assert "quick" in tokens
    assert "lazy" in tokens


def test_tokenize_filters_short_tokens():
    tokens = extraction.tokenize("a an it is ok fine")
    # "ok" is length 2, below MIN_TOKEN_LEN=3; "fine" should survive.
    assert "ok" not in tokens
    assert "fine" in tokens


def test_tokenize_empty_string_returns_empty_list():
    assert extraction.tokenize("") == []


def test_extract_bigrams_joins_adjacent_content_words():
    bigrams = extraction.extract_bigrams("the stress response system")
    assert "stress response" in bigrams
    assert "response system" in bigrams


def test_extract_bigrams_excludes_pairs_spanning_a_stopword():
    # "and" sits between "quick" and "lazy" in the raw text, so they must not
    # be joined even though both individually pass the content-word filter.
    bigrams = extraction.extract_bigrams("quick and lazy fox")
    assert "quick lazy" not in bigrams
    assert "quick and" not in bigrams


def test_extract_bigrams_excludes_pair_with_short_word():
    # "ok" is below MIN_TOKEN_LEN (3), so it can't anchor a bigram either side.
    bigrams = extraction.extract_bigrams("ok fine plan")
    assert "ok fine" not in bigrams
    assert "fine plan" in bigrams


def test_extract_bigrams_empty_and_single_word_produce_no_bigrams():
    assert extraction.extract_bigrams("") == []
    assert extraction.extract_bigrams("workflow") == []


def test_compute_document_frequencies_counts_bigram_phrases_across_notes():
    bodies = {
        "a": "stress response system overview",
        "b": "the stress response varies by person",
        "c": "completely unrelated golf content",
    }
    doc_freq = extraction.compute_document_frequencies(bodies)
    assert doc_freq["stress response"] == 2


def test_compute_document_frequencies_counts_notes_not_occurrences():
    bodies = {
        "a": "workflow workflow workflow context",
        "b": "workflow context",
        "c": "golf swing",
    }
    doc_freq = extraction.compute_document_frequencies(bodies)
    assert doc_freq["workflow"] == 2
    assert doc_freq["context"] == 2
    assert doc_freq["golf"] == 1


def test_extract_concepts_ranks_rare_terms_above_ubiquitous_terms():
    bodies = {
        "a": "workflow context automation",
        "b": "workflow context golf",
        "c": "workflow context sourdough",
    }
    doc_freq = extraction.compute_document_frequencies(bodies)
    total = len(bodies)
    concepts = extraction.extract_concepts(bodies["a"], doc_freq, total, top_n=5)
    terms = [term for term, _ in concepts]
    # "automation" appears in only 1 of 3 notes; "workflow"/"context" appear in all 3.
    assert terms.index("automation") < terms.index("workflow")


def test_extract_concepts_handles_term_in_every_note_without_zero_division():
    # Regression test: a term with doc_freq == total_notes must not raise
    # ZeroDivisionError or ValueError under the smoothed IDF formula.
    bodies = {"a": "shared term here", "b": "shared term again"}
    doc_freq = extraction.compute_document_frequencies(bodies)
    total = len(bodies)
    concepts = extraction.extract_concepts(bodies["a"], doc_freq, total)
    weights = dict(concepts)
    assert "shared" in weights
    assert weights["shared"] > 0
    assert math.isfinite(weights["shared"])


def test_extract_concepts_empty_body_returns_empty_list():
    doc_freq = extraction.compute_document_frequencies({"a": "something"})
    assert extraction.extract_concepts("", doc_freq, 1) == []


def test_extract_concepts_includes_bigram_phrases_alongside_single_words():
    bodies = {
        "a": "stress response research design covers stress response mechanisms",
        "b": "an unrelated note about golf swing mechanics entirely",
    }
    doc_freq = extraction.compute_document_frequencies(bodies)
    total = len(bodies)
    concepts = extraction.extract_concepts(bodies["a"], doc_freq, total, top_n=10)
    terms = [term for term, _ in concepts]
    assert "stress response" in terms
    # The phrase repeats twice in note "a" (tf=2), so it should outrank a
    # same-rarity single word that only appears once.
    assert terms.index("stress response") < terms.index("design")


def test_extract_concepts_respects_top_n():
    # Distinct letter-only words (the tokenizer strips digits, so "term0".."term19"
    # would all collapse to the same token "term" — use distinct letters instead).
    words = [chr(ord("a") + i) * 5 for i in range(20)]
    body = " ".join(words)
    doc_freq = extraction.compute_document_frequencies({"a": body})
    concepts = extraction.extract_concepts(body, doc_freq, 1, top_n=5)
    assert len(concepts) == 5


def test_enrich_with_claude_returns_fallback_when_no_api_key():
    fallback = [("workflow", 1.0)]
    result = extraction.enrich_with_claude("some note body", fallback, api_key=None)
    assert result == fallback


def test_enrich_with_claude_uses_ai_response_on_success():
    fallback = [("workflow", 1.0)]
    fake_response_body = json.dumps({
        "content": [{"text": json.dumps(["automation", "handoffs", "context"])}]
    }).encode("utf-8")

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = fake_response_body
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    with patch("extraction.urllib.request.urlopen", return_value=mock_response):
        result = extraction.enrich_with_claude("note body", fallback, api_key="fake-key")

    terms = [term for term, _ in result]
    assert terms == ["automation", "handoffs", "context"]


def test_enrich_with_claude_falls_back_on_network_error():
    fallback = [("workflow", 1.0)]
    with patch("extraction.urllib.request.urlopen", side_effect=urllib.error.URLError("blocked")):
        result = extraction.enrich_with_claude("note body", fallback, api_key="fake-key")
    assert result == fallback


def test_enrich_with_claude_falls_back_on_malformed_json():
    fallback = [("workflow", 1.0)]
    fake_response_body = json.dumps({
        "content": [{"text": "not valid json ["}]
    }).encode("utf-8")

    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = fake_response_body
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    with patch("extraction.urllib.request.urlopen", return_value=mock_response):
        result = extraction.enrich_with_claude("note body", fallback, api_key="fake-key")

    assert result == fallback


def test_enrich_with_claude_falls_back_on_non_200_status():
    fallback = [("workflow", 1.0)]
    mock_response = MagicMock()
    mock_response.status = 500
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    with patch("extraction.urllib.request.urlopen", return_value=mock_response):
        result = extraction.enrich_with_claude("note body", fallback, api_key="fake-key")

    assert result == fallback
