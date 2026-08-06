import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import crossref


def _mock_response(items):
    payload = json.dumps({"message": {"items": items}}).encode("utf-8")
    return lambda url: payload


def test_title_similarity_identical_titles_is_one():
    assert crossref.title_similarity("A Study of Things", "A Study of Things") == 1.0


def test_title_similarity_unrelated_titles_is_low():
    assert crossref.title_similarity("A Study of Things", "Zebra Migration Patterns in Africa") < 0.3


def test_authors_overlap_true_when_surname_matches():
    crossref_authors = [{"given": "Jane", "family": "Doe"}]
    assert crossref.authors_overlap("Jane Doe, John Smith", crossref_authors) is True


def test_authors_overlap_false_when_no_surname_matches():
    crossref_authors = [{"given": "Alice", "family": "Nguyen"}]
    assert crossref.authors_overlap("Jane Doe, John Smith", crossref_authors) is False


def test_search_works_uses_injected_http_get_no_live_network():
    calls = []

    def fake_get(url):
        calls.append(url)
        return json.dumps({"message": {"items": [{"title": ["X"]}]}}).encode("utf-8")

    items = crossref.search_works("A Study of Things", "doe", http_get=fake_get)
    assert len(calls) == 1
    assert "query.bibliographic" in calls[0]
    assert "query.author" in calls[0]
    assert items == [{"title": ["X"]}]


def test_search_works_handles_malformed_json_gracefully():
    items = crossref.search_works("X", "doe", http_get=lambda url: b"not json")
    assert items == []


def test_find_publication_match_true_positive():
    items = [{
        "title": ["A Study of Things: Evidence From the Field"],
        "author": [{"given": "Jane", "family": "Doe"}],
        "DOI": "10.1000/abcd",
        "container-title": ["Journal of Examples"],
        "published": {"date-parts": [[2026, 8, 3]]},
    }]
    match = crossref.find_publication_match(
        "A Study of Things: Evidence From the Field",
        "Jane Doe, John Smith",
        http_get=_mock_response(items),
    )
    assert match is not None
    assert match["doi"] == "10.1000/abcd"
    assert match["published_date"] == "2026-08-03"


def test_find_publication_match_true_negative_similar_title_different_authors():
    items = [{
        "title": ["A Study of Things: Evidence From the Field"],
        "author": [{"given": "Alice", "family": "Nguyen"}],
        "DOI": "10.1000/wrongpaper",
        "container-title": ["Unrelated Journal"],
    }]
    match = crossref.find_publication_match(
        "A Study of Things: Evidence From the Field",
        "Jane Doe, John Smith",
        http_get=_mock_response(items),
    )
    assert match is None


def test_find_publication_match_near_miss_title_below_threshold():
    items = [{
        "title": ["Completely Different Research on Zebras"],
        "author": [{"given": "Jane", "family": "Doe"}],
        "DOI": "10.1000/zebra",
    }]
    match = crossref.find_publication_match(
        "A Study of Things: Evidence From the Field",
        "Jane Doe",
        http_get=_mock_response(items),
    )
    assert match is None


def test_find_publication_match_returns_none_on_empty_results():
    match = crossref.find_publication_match("X", "Doe", http_get=_mock_response([]))
    assert match is None


def test_extract_published_date_prefers_published_over_online():
    item = {
        "published-online": {"date-parts": [[2026, 1, 1]]},
        "published": {"date-parts": [[2026, 8, 3]]},
    }
    assert crossref._extract_published_date(item) == "2026-08-03"


def test_extract_published_date_handles_year_only():
    item = {"published": {"date-parts": [[2026]]}}
    assert crossref._extract_published_date(item) == "2026-01-01"


def test_extract_published_date_returns_none_when_missing():
    assert crossref._extract_published_date({}) is None
