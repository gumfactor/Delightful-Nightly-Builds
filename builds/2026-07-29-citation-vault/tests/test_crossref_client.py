import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
import crossref_client


def _fake_request(response_body: bytes):
    def fn(url):
        return response_body
    return fn


def test_lookup_doi_well_formed():
    body = json.dumps({
        "message": {
            "DOI": "10.1234/abc",
            "title": ["A Study of Something"],
            "author": [{"given": "Jane", "family": "Doe"}, {"given": "John", "family": "Smith"}],
            "published-print": {"date-parts": [[2021, 3]]},
            "container-title": ["Journal of Examples"],
            "abstract": "This is an abstract.",
        }
    }).encode("utf-8")
    paper = crossref_client.lookup_doi("10.1234/abc", request_fn=_fake_request(body))
    assert paper["title"] == "A Study of Something"
    assert paper["authors"] == ["Jane Doe", "John Smith"]
    assert paper["year"] == 2021
    assert paper["journal"] == "Journal of Examples"
    assert paper["abstract"] == "This is an abstract."
    assert paper["doi"] == "10.1234/abc"


def test_lookup_doi_missing_abstract():
    body = json.dumps({
        "message": {
            "DOI": "10.1234/xyz",
            "title": ["No Abstract Here"],
            "author": [{"given": "A", "family": "Author"}],
            "published-online": {"date-parts": [[2019]]},
            "container-title": ["Some Journal"],
        }
    }).encode("utf-8")
    paper = crossref_client.lookup_doi("10.1234/xyz", request_fn=_fake_request(body))
    assert paper["abstract"] is None
    assert paper["year"] == 2019


def test_lookup_doi_missing_author_list():
    body = json.dumps({
        "message": {
            "DOI": "10.1234/noauth",
            "title": ["Orphan Paper"],
        }
    }).encode("utf-8")
    paper = crossref_client.lookup_doi("10.1234/noauth", request_fn=_fake_request(body))
    assert paper["authors"] == []
    assert paper["year"] is None


def test_lookup_doi_organization_author():
    body = json.dumps({
        "message": {
            "DOI": "10.1234/org",
            "title": ["Org Authored Paper"],
            "author": [{"name": "World Health Organization"}],
        }
    }).encode("utf-8")
    paper = crossref_client.lookup_doi("10.1234/org", request_fn=_fake_request(body))
    assert paper["authors"] == ["World Health Organization"]


def test_lookup_doi_http_error():
    def raising_fn(url):
        raise OSError("connection refused")
    with pytest.raises(crossref_client.CrossrefError):
        crossref_client.lookup_doi("10.1234/fail", request_fn=raising_fn)


def test_lookup_doi_malformed_json():
    def fn(url):
        return b"not json{{{"
    with pytest.raises(crossref_client.CrossrefError):
        crossref_client.lookup_doi("10.1234/bad", request_fn=fn)


def test_lookup_doi_no_message_field():
    body = json.dumps({"status": "not-found"}).encode("utf-8")
    with pytest.raises(crossref_client.CrossrefError):
        crossref_client.lookup_doi("10.1234/missing", request_fn=_fake_request(body))


def test_lookup_doi_strips_url_prefix():
    body = json.dumps({
        "message": {"DOI": "10.1234/abc", "title": ["T"], "author": []}
    }).encode("utf-8")
    captured = {}

    def fn(url):
        captured["url"] = url
        return body

    crossref_client.lookup_doi("https://doi.org/10.1234/ABC", request_fn=fn)
    # The slash in a DOI must be percent-encoded since it sits inside a single
    # URL path segment (/works/{doi}), not treated as a path separator.
    assert "10.1234%2Fabc" in captured["url"]


def test_search_multiple_results():
    body = json.dumps({
        "message": {
            "items": [
                {"DOI": "10.1/a", "title": ["Paper A"], "author": [{"given": "X", "family": "Y"}]},
                {"DOI": "10.1/b", "title": ["Paper B"], "author": []},
            ]
        }
    }).encode("utf-8")
    results = crossref_client.search("some query", request_fn=_fake_request(body))
    assert len(results) == 2
    assert results[0]["title"] == "Paper A"
    assert results[1]["title"] == "Paper B"


def test_search_zero_results():
    body = json.dumps({"message": {"items": []}}).encode("utf-8")
    results = crossref_client.search("nothing matches", request_fn=_fake_request(body))
    assert results == []


def test_search_network_error():
    def raising_fn(url):
        raise OSError("timeout")
    with pytest.raises(crossref_client.CrossrefError):
        crossref_client.search("query", request_fn=raising_fn)
