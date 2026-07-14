import json
import urllib.error
from unittest.mock import patch

import pytest

import api_client


class FakeResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_build_request_payload_shape():
    payload = api_client.build_request_payload("psychopathy", [2023, 2024], offset=10, limit=25)
    assert payload["criteria"]["advanced_text_search"]["search_text"] == "psychopathy"
    assert payload["criteria"]["fiscal_years"] == [2023, 2024]
    assert payload["offset"] == 10
    assert payload["limit"] == 25
    assert "ProjectNum" in payload["include_fields"]


def test_parse_project_full_record():
    raw = {
        "ProjectNum": "5R01MH123456-03",
        "ProjectTitle": "Neural correlates of empathy",
        "AbstractText": "This study examines...",
        "ContactPiName": "Jane Smith",
        "OrgName": "Big State University",
        "OrgCity": "Springfield",
        "OrgState": "IL",
        "AgencyIcAdmin": {"Code": "NIMH", "Name": "National Institute of Mental Health"},
        "ActivityCode": "R01",
        "AwardAmount": 450000,
        "FiscalYear": 2024,
        "ProjectStartDate": "2022-05-01",
        "ProjectEndDate": "2027-04-30",
    }
    parsed = api_client.parse_project(raw, "empathy")
    assert parsed["project_num"] == "5R01MH123456-03"
    assert parsed["title"] == "Neural correlates of empathy"
    assert parsed["pi_name"] == "Jane Smith"
    assert parsed["ic_admin"] == "NIMH"
    assert parsed["activity_code"] == "R01"
    assert parsed["award_amount"] == 450000
    assert parsed["fiscal_year"] == 2024
    assert parsed["topic"] == "empathy"


def test_parse_project_missing_project_num_returns_none():
    raw = {"ProjectTitle": "No ID project"}
    assert api_client.parse_project(raw, "empathy") is None


def test_parse_project_handles_missing_optional_fields():
    raw = {"ProjectNum": "1K01AA000000-01"}
    parsed = api_client.parse_project(raw, "stress_coping")
    assert parsed["title"] == "(untitled project)"
    assert parsed["abstract"] == ""
    assert parsed["pi_name"] is None
    assert parsed["ic_admin"] is None


def test_parse_project_extracts_pi_from_principal_investigators_list():
    raw = {
        "ProjectNum": "2R21DA000000-01",
        "PrincipalInvestigators": [{"FirstName": "Alex", "LastName": "Rivera"}],
    }
    parsed = api_client.parse_project(raw, "psychopathy")
    assert parsed["pi_name"] == "Alex Rivera"


def test_fetch_projects_single_page_success():
    fake_results = [
        {"ProjectNum": f"P{i}", "ProjectTitle": f"Title {i}", "AwardAmount": 1000, "FiscalYear": 2024}
        for i in range(3)
    ]
    with patch("api_client.urllib.request.urlopen", return_value=FakeResponse({"results": fake_results})):
        projects = api_client.fetch_projects("empathy", "empathy", [2024], max_results=100)
    assert len(projects) == 3
    assert projects[0]["project_num"] == "P0"


def test_fetch_projects_paginates_until_short_page():
    page_one = [{"ProjectNum": f"A{i}", "ProjectTitle": "t", "FiscalYear": 2024} for i in range(50)]
    page_two = [{"ProjectNum": f"B{i}", "ProjectTitle": "t", "FiscalYear": 2024} for i in range(5)]
    responses = [FakeResponse({"results": page_one}), FakeResponse({"results": page_two})]

    with patch("api_client.urllib.request.urlopen", side_effect=responses):
        projects = api_client.fetch_projects("empathy", "empathy", [2024], max_results=100)
    assert len(projects) == 55


def test_fetch_projects_empty_results_returns_empty_list():
    with patch("api_client.urllib.request.urlopen", return_value=FakeResponse({"results": []})):
        projects = api_client.fetch_projects("empathy", "empathy", [2024], max_results=100)
    assert projects == []


def test_fetch_projects_raises_on_http_error():
    error = urllib.error.HTTPError(url="x", code=500, msg="Server Error", hdrs=None, fp=None)
    with patch("api_client.urllib.request.urlopen", side_effect=error):
        with pytest.raises(api_client.ApiClientError):
            api_client.fetch_projects("empathy", "empathy", [2024])


def test_fetch_projects_raises_on_url_error():
    error = urllib.error.URLError("network unreachable")
    with patch("api_client.urllib.request.urlopen", side_effect=error):
        with pytest.raises(api_client.ApiClientError):
            api_client.fetch_projects("empathy", "empathy", [2024])


def test_fetch_projects_raises_on_malformed_json():
    class BadResponse:
        def read(self):
            return b"not json"

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    with patch("api_client.urllib.request.urlopen", return_value=BadResponse()):
        with pytest.raises(api_client.ApiClientError):
            api_client.fetch_projects("empathy", "empathy", [2024])


def test_fetch_projects_raises_when_results_key_missing():
    with patch("api_client.urllib.request.urlopen", return_value=FakeResponse({"meta": {}})):
        with pytest.raises(api_client.ApiClientError):
            api_client.fetch_projects("empathy", "empathy", [2024])
