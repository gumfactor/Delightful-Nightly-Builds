"""Tests for the OpenAlex client — all HTTP calls are mocked, never live."""

import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import openalex  # noqa: E402


def _mock_response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


def test_reconstruct_abstract_normal_case():
    inverted = {"Hello": [0], "world": [1], "of": [3], "science": [2]}
    assert openalex.reconstruct_abstract(inverted) == "Hello world science of"


def test_reconstruct_abstract_empty_case():
    assert openalex.reconstruct_abstract(None) == ""
    assert openalex.reconstruct_abstract({}) == ""


def test_reconstruct_abstract_repeated_words_out_of_order():
    inverted = {"a": [2, 0], "b": [1]}
    assert openalex.reconstruct_abstract(inverted) == "a b a"


def test_search_authors_returns_candidates():
    payload = {
        "results": [
            {
                "id": "https://openalex.org/A5023888391",
                "display_name": "Jane Doe",
                "works_count": 42,
                "cited_by_count": 1000,
                "last_known_institutions": [{"display_name": "Example University"}],
            }
        ]
    }
    with patch("openalex.urllib.request.urlopen", return_value=_mock_response(payload)):
        candidates = openalex.search_authors("Jane Doe")

    assert len(candidates) == 1
    assert candidates[0]["author_id"] == "A5023888391"
    assert candidates[0]["institution"] == "Example University"


def test_search_authors_rejects_empty_query():
    try:
        openalex.search_authors("   ")
        assert False, "expected OpenAlexError"
    except openalex.OpenAlexError:
        pass


def test_get_author_maps_summary_stats():
    payload = {
        "id": "https://openalex.org/A5023888391",
        "display_name": "Jane Doe",
        "works_count": 42,
        "cited_by_count": 1000,
        "summary_stats": {"h_index": 12, "i10_index": 20},
    }
    with patch("openalex.urllib.request.urlopen", return_value=_mock_response(payload)):
        author = openalex.get_author("A5023888391")

    assert author == {
        "author_id": "A5023888391",
        "display_name": "Jane Doe",
        "works_count": 42,
        "cited_by_count": 1000,
        "h_index": 12,
        "i10_index": 20,
    }


def test_iter_author_works_paginates_via_cursor():
    page_one = {
        "results": [{"id": "https://openalex.org/W1", "title": "Paper One", "cited_by_count": 5, "concepts": []}],
        "meta": {"next_cursor": "cursor-2"},
    }
    page_two = {
        "results": [{"id": "https://openalex.org/W2", "title": "Paper Two", "cited_by_count": 9, "concepts": []}],
        "meta": {"next_cursor": None},
    }
    responses = [_mock_response(page_one), _mock_response(page_two)]

    with patch("openalex.urllib.request.urlopen", side_effect=responses):
        works = list(openalex.iter_author_works("A5023888391"))

    assert [w["work_id"] for w in works] == ["W1", "W2"]
    assert works[0]["title"] == "Paper One"


def test_iter_author_works_stops_on_empty_results():
    empty_page = {"results": [], "meta": {"next_cursor": "cursor-x"}}
    with patch("openalex.urllib.request.urlopen", return_value=_mock_response(empty_page)):
        works = list(openalex.iter_author_works("A5023888391"))
    assert works == []


def test_normalize_work_extracts_host_venue_and_concepts():
    raw_work = {
        "id": "https://openalex.org/W3",
        "title": "A Study",
        "publication_year": 2020,
        "doi": "10.1234/x",
        "cited_by_count": 3,
        "primary_location": {"source": {"display_name": "Journal of Examples"}},
        "concepts": [{"display_name": "Neuroscience"}, {"display_name": "Statistics"}],
        "abstract_inverted_index": {"Real": [0], "abstract": [1]},
    }
    normalized = openalex._normalize_work(raw_work)
    assert normalized["host_venue"] == "Journal of Examples"
    assert normalized["concepts"] == ["Neuroscience", "Statistics"]
    assert normalized["abstract"] == "Real abstract"


def test_get_json_raises_openalex_error_on_http_error():
    http_error = urllib.error.HTTPError("url", 404, "Not Found", hdrs=None, fp=None)
    with patch("openalex.urllib.request.urlopen", side_effect=http_error):
        try:
            openalex.get_author("A_DOES_NOT_EXIST")
            assert False, "expected OpenAlexError"
        except openalex.OpenAlexError as exc:
            assert "404" in str(exc)


def test_get_json_raises_openalex_error_on_url_error():
    url_error = urllib.error.URLError("network unreachable")
    with patch("openalex.urllib.request.urlopen", side_effect=url_error):
        try:
            openalex.get_author("A5023888391")
            assert False, "expected OpenAlexError"
        except openalex.OpenAlexError as exc:
            assert "Could not reach OpenAlex" in str(exc)


def test_get_json_includes_mailto_when_provided():
    payload = {"id": "https://openalex.org/A1", "display_name": "X", "works_count": 0, "cited_by_count": 0}
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        return _mock_response(payload)

    with patch("openalex.urllib.request.urlopen", side_effect=fake_urlopen):
        openalex.get_author("A1", mailto="researcher@example.com")

    assert "mailto=researcher%40example.com" in captured["url"]
