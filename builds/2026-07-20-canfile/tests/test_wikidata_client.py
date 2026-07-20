from unittest.mock import patch

import wikidata_client as wd


def test_search_entity_single_match():
    fake_response = {
        "search": [{"id": "Q1524829", "label": "Tim Hortons", "description": "Canadian restaurant chain"}]
    }
    with patch.object(wd, "_api_get", return_value=fake_response) as mock_get:
        results = wd.search_entity("Tim Hortons")
    assert results == [
        {"id": "Q1524829", "label": "Tim Hortons", "description": "Canadian restaurant chain"}
    ]
    mock_get.assert_called_once()


def test_search_entity_multiple_matches():
    fake_response = {
        "search": [
            {"id": "Q1", "label": "Acme Corp", "description": "US company"},
            {"id": "Q2", "label": "Acme Corp Canada", "description": "Canadian subsidiary"},
        ]
    }
    with patch.object(wd, "_api_get", return_value=fake_response):
        results = wd.search_entity("Acme")
    assert len(results) == 2
    assert results[0]["id"] == "Q1"


def test_search_entity_no_matches():
    with patch.object(wd, "_api_get", return_value={"search": []}):
        results = wd.search_entity("Totally Fictional Company Xyz")
    assert results == []


def test_get_claims_extracts_relevant_properties():
    fake_response = {
        "entities": {
            "Q1524829": {
                "claims": {
                    "P17": [
                        {"mainsnak": {"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q16"}}}}
                    ],
                    "P159": [
                        {"mainsnak": {"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q172"}}}}
                    ],
                    "P31": [
                        {"mainsnak": {"snaktype": "value", "datavalue": {"type": "wikibase-entityid", "value": {"id": "Q6881511"}}}}
                    ],
                }
            }
        }
    }
    with patch.object(wd, "_api_get", return_value=fake_response):
        claims = wd.get_claims("Q1524829")
    assert claims["P17"] == ["Q16"]
    assert claims["P159"] == ["Q172"]
    assert claims["P749"] == []
    assert claims["P127"] == []
    assert claims["P31"] == ["Q6881511"]


def test_get_claims_skips_novalue_snaks():
    fake_response = {
        "entities": {
            "Q999": {
                "claims": {
                    "P17": [{"mainsnak": {"snaktype": "novalue"}}],
                }
            }
        }
    }
    with patch.object(wd, "_api_get", return_value=fake_response):
        claims = wd.get_claims("Q999")
    assert claims["P17"] == []


def test_get_claims_missing_entity_returns_empty_lists():
    with patch.object(wd, "_api_get", return_value={"entities": {}}):
        claims = wd.get_claims("Q0")
    assert all(value == [] for value in claims.values())


def test_resolve_labels_batch():
    fake_response = {
        "entities": {
            "Q16": {"labels": {"en": {"value": "Canada"}}},
            "Q172": {"labels": {"en": {"value": "Oakville"}}},
        }
    }
    with patch.object(wd, "_api_get", return_value=fake_response):
        labels = wd.resolve_labels(["Q16", "Q172"])
    assert labels == {"Q16": "Canada", "Q172": "Oakville"}


def test_resolve_labels_empty_input_makes_no_call():
    with patch.object(wd, "_api_get") as mock_get:
        labels = wd.resolve_labels([])
    assert labels == {}
    mock_get.assert_not_called()


def test_api_get_raises_wikidata_error_on_network_failure():
    with patch("urllib.request.urlopen", side_effect=OSError("network unreachable")):
        try:
            wd._api_get({"action": "wbsearchentities"})
            assert False, "expected WikidataError"
        except wd.WikidataError:
            pass


def test_entity_url_format():
    assert wd.entity_url("Q1524829") == "https://www.wikidata.org/wiki/Q1524829"
