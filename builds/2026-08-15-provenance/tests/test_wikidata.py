import json
from contextlib import contextmanager
from unittest.mock import patch

from src import wikidata


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def _mock_urlopen(json_body):
    payload = json.dumps(json_body).encode("utf-8")
    return patch("src.wikidata.urllib.request.urlopen", return_value=_FakeResponse(payload))


def test_search_entity_returns_qid_from_first_result():
    body = {"search": [{"id": "Q12345", "label": "Acme"}]}
    with _mock_urlopen(body):
        qid = wikidata.search_entity("Acme")
    assert qid == "Q12345"


def test_search_entity_returns_none_when_no_results():
    body = {"search": []}
    with _mock_urlopen(body):
        qid = wikidata.search_entity("Totally Fictional Business Name XYZ")
    assert qid is None


def test_search_entity_returns_none_for_blank_name_without_network_call():
    with patch("src.wikidata.urllib.request.urlopen") as mock_urlopen:
        qid = wikidata.search_entity("   ")
    assert qid is None
    mock_urlopen.assert_not_called()


def test_get_claims_extracts_country_headquarters_parent_owner():
    body = {
        "entities": {
            "Q1": {
                "claims": {
                    "P17": [{"mainsnak": {"snaktype": "value", "datavalue": {"value": {"id": "Q16"}}}}],
                    "P159": [{"mainsnak": {"snaktype": "value", "datavalue": {"value": {"id": "Q172"}}}}],
                    "P749": [{"mainsnak": {"snaktype": "value", "datavalue": {"value": {"id": "Q999"}}}}],
                    "P127": [{"mainsnak": {"snaktype": "value", "datavalue": {"value": {"id": "Q888"}}}}],
                }
            }
        }
    }
    with _mock_urlopen(body):
        claims = wikidata.get_claims("Q1")
    assert claims == {
        "country": "Q16",
        "headquarters": "Q172",
        "parent_org": "Q999",
        "owned_by": "Q888",
    }


def test_get_claims_missing_properties_returns_none_fields():
    body = {"entities": {"Q1": {"claims": {}}}}
    with _mock_urlopen(body):
        claims = wikidata.get_claims("Q1")
    assert claims == {
        "country": None,
        "headquarters": None,
        "parent_org": None,
        "owned_by": None,
    }


def test_get_claims_handles_malformed_response_without_raising():
    with _mock_urlopen({"unexpected": "shape"}):
        claims = wikidata.get_claims("Q1")
    assert claims == {
        "country": None,
        "headquarters": None,
        "parent_org": None,
        "owned_by": None,
    }


def test_get_claims_with_no_qid_returns_none_fields_without_network_call():
    with patch("src.wikidata.urllib.request.urlopen") as mock_urlopen:
        claims = wikidata.get_claims("")
    assert claims == {
        "country": None,
        "headquarters": None,
        "parent_org": None,
        "owned_by": None,
    }
    mock_urlopen.assert_not_called()


def test_get_label_returns_english_label():
    body = {"entities": {"Q16": {"labels": {"en": {"language": "en", "value": "Canada"}}}}}
    with _mock_urlopen(body):
        label = wikidata.get_label("Q16")
    assert label == "Canada"


def test_get_label_returns_none_on_network_failure():
    with patch("src.wikidata.urllib.request.urlopen", side_effect=OSError("network down")):
        label = wikidata.get_label("Q16")
    assert label is None
