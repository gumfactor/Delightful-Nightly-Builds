import json
import os

import pytest

from src import extract

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "sample_companyfacts.json")


@pytest.fixture
def companyfacts():
    with open(FIXTURE_PATH) as f:
        return json.load(f)


@pytest.fixture
def rows(companyfacts):
    return extract.extract_annual_financials(companyfacts)


def test_resolve_tag_picks_first_present_candidate():
    usgaap = {"NetIncomeLoss": {"units": {"USD": [{}]}}}
    assert extract.resolve_tag(usgaap, ["Revenues", "NetIncomeLoss"]) == "NetIncomeLoss"


def test_resolve_tag_returns_none_when_no_candidate_present():
    usgaap = {"SomeUnrelatedTag": {"units": {"USD": [{}]}}}
    assert extract.resolve_tag(usgaap, ["Revenues", "NetIncomeLoss"]) is None


def test_resolve_tag_skips_tag_without_usd_unit():
    usgaap = {"Revenues": {"units": {"EUR": [{}]}}}
    assert extract.resolve_tag(usgaap, ["Revenues"]) is None


def test_falls_back_to_alternate_revenue_tag(rows):
    # Fixture has no "Revenues" tag, only the alternate -- confirms the
    # fallback chain resolved something rather than silently returning None.
    assert all(row["revenue"] is not None for row in rows)


def test_extracts_four_fiscal_years(rows):
    assert [row["fiscal_year"] for row in rows] == [2021, 2022, 2023, 2024]


def test_revenue_values_per_fiscal_year(rows):
    by_fy = {row["fiscal_year"]: row["revenue"] for row in rows}
    assert by_fy[2021] == 1000000000
    assert by_fy[2022] == 850000000
    assert by_fy[2023] == 900000000
    assert by_fy[2024] == 700000000


def test_duration_bounds_reject_stub_period(rows):
    # A 214-day fy=2021 fact exists in the fixture with a later filed date
    # than the genuine full-year fact. If duration filtering were broken,
    # the stub's value (999000000) would win the latest-filed tie-break.
    fy2021 = next(row for row in rows if row["fiscal_year"] == 2021)
    assert fy2021["revenue"] == 1000000000


def test_restated_fact_prefers_latest_filed(rows):
    # FY2023 revenue has two 10-K facts (890M filed 2024-02-05, 900M filed
    # 2024-03-15); the later filing should win.
    fy2023 = next(row for row in rows if row["fiscal_year"] == 2023)
    assert fy2023["revenue"] == 900000000
    assert fy2023["filed_date"] == "2024-03-15"


def test_ten_q_facts_excluded_from_duration_concepts(rows):
    # The Q3 revenue fact (210M) must never surface as a fiscal-year value.
    values = [row["revenue"] for row in rows]
    assert 210000000 not in values


def test_ten_q_facts_excluded_from_instant_concepts(rows):
    # The Q3 assets fact (790M) must never surface as a fiscal-year value.
    values = [row["assets"] for row in rows]
    assert 790000000 not in values


def test_net_income_values_per_fiscal_year(rows):
    by_fy = {row["fiscal_year"]: row["net_income"] for row in rows}
    assert by_fy[2021] == 100000000
    assert by_fy[2022] == 80000000
    assert by_fy[2023] == -50000000
    assert by_fy[2024] == -100000000


def test_balance_sheet_values_per_fiscal_year(rows):
    by_fy = {row["fiscal_year"]: row for row in rows}
    assert by_fy[2023]["assets"] == 750000000
    assert by_fy[2023]["liabilities"] == 700000000
    assert by_fy[2023]["equity"] == 50000000
    assert by_fy[2024]["equity"] == -20000000


def test_non_usd_unit_tag_never_used():
    # EarningsPerShareBasic only has a USD-per-shares unit and is not one
    # of our tracked concepts -- confirm no crash and no stray field.
    usgaap = {"EarningsPerShareBasic": {"units": {"USD-per-shares": [{"val": 1.23}]}}}
    assert extract.resolve_tag(usgaap, ["EarningsPerShareBasic"]) is None


def test_missing_facts_key_returns_empty_list():
    assert extract.extract_annual_financials({}) == []


def test_missing_usgaap_key_returns_empty_list():
    assert extract.extract_annual_financials({"facts": {}}) == []


def test_row_carries_accn_and_filed_date(rows):
    fy2021 = next(row for row in rows if row["fiscal_year"] == 2021)
    assert fy2021["accn"] is not None
    assert fy2021["filed_date"] == "2022-02-10"
