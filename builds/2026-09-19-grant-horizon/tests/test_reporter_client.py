import pytest

from reporter_client import (
    ReporterAPIError,
    fetch_all_projects,
    normalize_project,
)

FULL_RECORD = {
    "project_num": "1R01MH123456-01",
    "core_project_num": "R01MH123456",
    "project_title": "Neural correlates of empathy in forensic populations",
    "fiscal_year": 2023,
    "award_amount": 450000.0,
    "organization": {
        "org_name": "University of Example",
        "org_city": "Example City",
        "org_state": "MA",
        "org_country": "United States",
    },
    "principal_investigators": [
        {"first_name": "Jane", "last_name": "Researcher"},
        {"full_name": "Sam Co-PI"},
    ],
    "agency_ic_admin": {"code": "MH", "name": "National Institute of Mental Health"},
    "project_start_date": "2023-04-01",
    "project_end_date": "2028-03-31",
}


def test_normalize_project_full_record():
    project = normalize_project("empathy neuroscience", FULL_RECORD)
    assert project.project_num == "1R01MH123456-01"
    assert project.core_project_num == "R01MH123456"
    assert project.title == "Neural correlates of empathy in forensic populations"
    assert project.fiscal_year == 2023
    assert project.award_amount == 450000.0
    assert project.org_name == "University of Example"
    assert project.org_state == "MA"
    assert project.pi_names == ["Jane Researcher", "Sam Co-PI"]
    assert project.agency_ic == "National Institute of Mental Health"
    assert project.start_date == "2023-04-01"


def test_normalize_project_missing_optional_fields_uses_safe_defaults():
    sparse = {
        "project_num": "1R01MH999999-01",
        "fiscal_year": "2021",
        "project_title": None,
    }
    project = normalize_project("stress cortisol", sparse)
    assert project.title == "(untitled project)"
    assert project.award_amount == 0.0
    assert project.org_name == "Unknown institution"
    assert project.pi_names == []
    assert project.agency_ic == "Unknown agency"
    assert project.fiscal_year == 2021


def test_normalize_project_missing_project_num_raises():
    with pytest.raises(ReporterAPIError):
        normalize_project("psychopathy", {"fiscal_year": 2022, "project_title": "No id"})


def test_normalize_project_missing_fiscal_year_raises():
    with pytest.raises(ReporterAPIError):
        normalize_project("psychopathy", {"project_num": "X", "project_title": "No year"})


def test_normalize_project_malformed_award_amount_defaults_to_zero():
    record = dict(FULL_RECORD, award_amount="not-a-number")
    project = normalize_project("empathy neuroscience", record)
    assert project.award_amount == 0.0


def test_fetch_all_projects_single_page():
    def fake_post(url, body):
        assert body["criteria"]["advanced_text_search"]["search_text"] == "psychopathy"
        assert body["offset"] == 0
        return {"results": [FULL_RECORD]}

    projects = fetch_all_projects("psychopathy", [2023], fake_post, page_size=500)
    assert len(projects) == 1
    assert projects[0].topic == "psychopathy"


def test_fetch_all_projects_paginates_until_short_page():
    call_offsets = []

    def fake_post(url, body):
        call_offsets.append(body["offset"])
        if body["offset"] == 0:
            return {"results": [FULL_RECORD] * 2}
        return {"results": [FULL_RECORD]}

    projects = fetch_all_projects("psychopathy", [2023], fake_post, page_size=2)
    assert call_offsets == [0, 2]
    assert len(projects) == 3


def test_fetch_all_projects_empty_fiscal_years_raises():
    with pytest.raises(ValueError):
        fetch_all_projects("psychopathy", [], lambda url, body: {"results": []})


def test_fetch_all_projects_missing_results_key_raises_reporter_error():
    def fake_post(url, body):
        return {"meta": {"total": 0}}

    with pytest.raises(ReporterAPIError):
        fetch_all_projects("psychopathy", [2023], fake_post)


def test_fetch_all_projects_non_dict_response_raises_reporter_error():
    def fake_post(url, body):
        return ["not", "a", "dict"]

    with pytest.raises(ReporterAPIError):
        fetch_all_projects("psychopathy", [2023], fake_post)
