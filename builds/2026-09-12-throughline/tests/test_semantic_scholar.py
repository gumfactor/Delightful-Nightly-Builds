import json
import urllib.error

import pytest

from src import semantic_scholar as ss


def fixture_transport(response_bytes):
    def transport(url, headers):
        return response_bytes
    return transport


def erroring_transport(exc):
    def transport(url, headers):
        raise exc
    return transport


AUTHOR_SEARCH_FIXTURE = {
    "total": 2,
    "data": [
        {
            "authorId": "12345",
            "name": "Jane Doe",
            "affiliations": ["State University"],
            "paperCount": 42,
            "citationCount": 900,
            "papers": [{"title": "Stress and Cortisol Reactivity"}, {"title": "Empathy Networks"}],
        },
        {
            "authorId": "67890",
            "name": "Jane Doe",
            "affiliations": ["Other College"],
            "paperCount": 3,
            "citationCount": 5,
            "papers": [],
        },
    ],
}

AUTHOR_PAPERS_FIXTURE = {
    "authorId": "12345",
    "name": "Jane Doe",
    "papers": [
        {
            "paperId": "abc1",
            "title": "Stress and Cortisol Reactivity",
            "abstract": "We examine cortisol reactivity under acute stress.",
            "year": 2019,
            "venue": "Journal of Affective Neuroscience",
            "citationCount": 40,
            "externalIds": {"DOI": "10.1000/abc1"},
        },
        {
            "paperId": "abc2",
            "title": "Empathy Networks",
            "abstract": None,
            "year": 2021,
            "venue": "Neuroscience Letters",
            "citationCount": 5,
            "externalIds": {},
        },
        {"paperId": None, "title": "Malformed entry with no id"},
    ],
}


def test_search_authors_parses_candidates():
    transport = fixture_transport(json.dumps(AUTHOR_SEARCH_FIXTURE).encode())
    candidates = ss.search_authors("Jane Doe", transport=transport)
    assert len(candidates) == 2
    assert candidates[0].author_id == "12345"
    assert candidates[0].paper_count == 42
    assert candidates[0].sample_titles == ["Stress and Cortisol Reactivity", "Empathy Networks"]
    assert candidates[1].affiliations == ["Other College"]


def test_search_authors_empty_results():
    transport = fixture_transport(json.dumps({"total": 0, "data": []}).encode())
    candidates = ss.search_authors("Nobody At All", transport=transport)
    assert candidates == []


def test_search_authors_rejects_empty_name():
    with pytest.raises(ValueError):
        ss.search_authors("   ")


def test_search_authors_handles_rate_limit():
    http_error = urllib.error.HTTPError("url", 429, "Too Many Requests", {}, None)
    transport = erroring_transport(http_error)
    with pytest.raises(ss.SemanticScholarError, match="rate limit"):
        ss.search_authors("Jane Doe", transport=transport)


def test_search_authors_handles_generic_http_error():
    http_error = urllib.error.HTTPError("url", 500, "Server Error", {}, None)
    transport = erroring_transport(http_error)
    with pytest.raises(ss.SemanticScholarError, match="500"):
        ss.search_authors("Jane Doe", transport=transport)


def test_search_authors_handles_network_error():
    transport = erroring_transport(urllib.error.URLError("no route to host"))
    with pytest.raises(ss.SemanticScholarError, match="Could not reach"):
        ss.search_authors("Jane Doe", transport=transport)


def test_search_authors_handles_malformed_json():
    transport = fixture_transport(b"not json at all {{{")
    with pytest.raises(ss.SemanticScholarError, match="malformed"):
        ss.search_authors("Jane Doe", transport=transport)


def test_fetch_author_papers_parses_papers_and_doi_url():
    transport = fixture_transport(json.dumps(AUTHOR_PAPERS_FIXTURE).encode())
    papers = ss.fetch_author_papers("12345", transport=transport)
    assert len(papers) == 2  # the malformed entry with no paperId is skipped
    assert papers[0].paper_id == "abc1"
    assert papers[0].external_url == "https://doi.org/10.1000/abc1"
    assert papers[1].abstract is None
    assert papers[1].external_url is None


def test_fetch_author_papers_rejects_empty_id():
    with pytest.raises(ValueError):
        ss.fetch_author_papers("")
