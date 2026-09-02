import json

import pytest

from src.crossref import CrossrefError, fetch_doi_metadata, message_to_reference, resolve_doi
from urllib.error import HTTPError


FIXTURE_MESSAGE = {
    "type": "journal-article",
    "title": ["The effects of sleep on memory: a randomized trial"],
    "author": [
        {"family": "Smith", "given": "Jane Marie"},
        {"family": "Jones", "given": "Alice B"},
    ],
    "container-title": ["Journal of Cognitive Science"],
    "volume": "12",
    "issue": "3",
    "page": "45-60",
    "DOI": "10.1000/xyz123",
    "URL": "https://doi.org/10.1000/xyz123",
    "issued": {"date-parts": [[2020, 6, 1]]},
}


def _transport_returning(payload: dict):
    calls = []

    def transport(url: str) -> bytes:
        calls.append(url)
        return json.dumps({"message": payload}).encode("utf-8")

    transport.calls = calls
    return transport


def test_fetch_doi_metadata_maps_crossref_message():
    transport = _transport_returning(FIXTURE_MESSAGE)
    message = fetch_doi_metadata("10.1000/xyz123", transport=transport)
    assert message["DOI"] == "10.1000/xyz123"
    assert len(transport.calls) == 1
    assert transport.calls[0] == "https://api.crossref.org/works/10.1000/xyz123"


def test_fetch_doi_metadata_strips_doi_url_prefix_before_request():
    transport = _transport_returning(FIXTURE_MESSAGE)
    fetch_doi_metadata("https://doi.org/10.1000/xyz123", transport=transport)
    assert transport.calls[0] == "https://api.crossref.org/works/10.1000/xyz123"


def test_fetch_doi_metadata_404_raises_crossref_error():
    def transport(url: str) -> bytes:
        raise HTTPError(url, 404, "Not Found", {}, None)

    with pytest.raises(CrossrefError, match="not found"):
        fetch_doi_metadata("10.9999/missing", transport=transport)


def test_fetch_doi_metadata_malformed_json_raises_crossref_error():
    def transport(url: str) -> bytes:
        return b"not json"

    with pytest.raises(CrossrefError, match="malformed JSON"):
        fetch_doi_metadata("10.1000/xyz123", transport=transport)


def test_fetch_doi_metadata_empty_doi_raises_without_network_call():
    def transport(url: str) -> bytes:
        raise AssertionError("transport should never be called for an empty DOI")

    with pytest.raises(CrossrefError):
        fetch_doi_metadata("", transport=transport)


def test_message_to_reference_maps_all_fields():
    ref = message_to_reference(FIXTURE_MESSAGE)
    assert ref.ref_type == "journal-article"
    assert ref.title == "The effects of sleep on memory: a randomized trial"
    assert len(ref.authors) == 2
    assert ref.authors[0].family == "Smith"
    assert ref.container_title == "Journal of Cognitive Science"
    assert ref.year == "2020"
    assert ref.source == "crossref"


def test_message_to_reference_unknown_type_maps_to_other():
    message = dict(FIXTURE_MESSAGE, type="dataset")
    ref = message_to_reference(message)
    assert ref.ref_type == "other"


def test_resolve_doi_end_to_end():
    transport = _transport_returning(FIXTURE_MESSAGE)
    ref = resolve_doi("10.1000/xyz123", transport=transport)
    assert ref.doi == "10.1000/xyz123"
    assert ref.year == "2020"
