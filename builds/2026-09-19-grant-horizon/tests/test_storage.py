from pathlib import Path

import pytest

import storage
from reporter_client import Project


def make_project(**overrides):
    defaults = dict(
        topic="psychopathy",
        project_num="1R01MH123456-01",
        core_project_num="R01MH123456",
        title="A study of psychopathy",
        fiscal_year=2023,
        award_amount=100000.0,
        org_name="University of Example",
        org_city="Example City",
        org_state="MA",
        org_country="United States",
        pi_names=["Jane Researcher"],
        agency_ic="NIMH",
        start_date="2023-01-01",
        end_date="2028-01-01",
    )
    defaults.update(overrides)
    return Project(**defaults)


@pytest.fixture
def conn(tmp_path: Path):
    db_path = tmp_path / "test.db"
    connection = storage.connect(db_path)
    yield connection
    connection.close()


def test_upsert_and_read_back(conn):
    written = storage.upsert_projects(conn, [make_project()])
    assert written == 1
    rows = storage.all_projects(conn)
    assert len(rows) == 1
    assert rows[0].title == "A study of psychopathy"
    assert rows[0].pi_names == ["Jane Researcher"]


def test_upsert_dedupes_on_topic_and_project_num(conn):
    storage.upsert_projects(conn, [make_project(award_amount=100000.0)])
    storage.upsert_projects(conn, [make_project(award_amount=250000.0)])
    rows = storage.all_projects(conn)
    assert len(rows) == 1
    assert rows[0].award_amount == 250000.0


def test_different_topics_with_same_project_num_are_distinct_rows(conn):
    storage.upsert_projects(conn, [make_project(topic="psychopathy")])
    storage.upsert_projects(conn, [make_project(topic="empathy neuroscience")])
    rows = storage.all_projects(conn)
    assert len(rows) == 2


def test_all_projects_filters_by_topic(conn):
    storage.upsert_projects(conn, [
        make_project(topic="psychopathy", project_num="P1"),
        make_project(topic="stress cortisol", project_num="P2"),
    ])
    rows = storage.all_projects(conn, topic="stress cortisol")
    assert len(rows) == 1
    assert rows[0].project_num == "P2"


def test_project_count(conn):
    storage.upsert_projects(conn, [
        make_project(project_num="P1"),
        make_project(project_num="P2"),
    ])
    assert storage.project_count(conn) == 2


def test_filtered_projects_restricts_by_topic_and_fiscal_year(conn):
    storage.upsert_projects(conn, [
        make_project(topic="psychopathy", project_num="P1", fiscal_year=2021),
        make_project(topic="psychopathy", project_num="P2", fiscal_year=2025),  # out of range
        make_project(topic="stress cortisol", project_num="P3", fiscal_year=2021),  # out of topic scope
    ])
    rows = storage.filtered_projects(conn, ["psychopathy"], fy_start=2020, fy_end=2022)
    assert [r.project_num for r in rows] == ["P1"]


def test_filtered_projects_empty_topics_returns_empty(conn):
    storage.upsert_projects(conn, [make_project(project_num="P1")])
    assert storage.filtered_projects(conn, [], fy_start=2020, fy_end=2026) == []


def test_filtered_projects_narrower_scope_than_a_prior_broader_sync(conn):
    # Simulates: an earlier sync covered 3 topics / FY2018-2026, then the user
    # runs `report --topics psychopathy --fy-start 2020 --fy-end 2022`.
    storage.upsert_projects(conn, [
        make_project(topic="psychopathy", project_num="P1", fiscal_year=2019),
        make_project(topic="psychopathy", project_num="P2", fiscal_year=2021),
        make_project(topic="affective neuroscience", project_num="P3", fiscal_year=2021),
    ])
    rows = storage.filtered_projects(conn, ["psychopathy"], fy_start=2020, fy_end=2022)
    assert [r.project_num for r in rows] == ["P2"]


def test_reconcile_topic_deletes_rows_no_longer_returned(conn):
    storage.upsert_projects(conn, [
        make_project(topic="psychopathy", project_num="P1", fiscal_year=2023),
        make_project(topic="psychopathy", project_num="P2", fiscal_year=2023),
    ])
    # Latest sync for FY2023 only returned P1 -- P2 must have been withdrawn/corrected.
    deleted = storage.reconcile_topic(conn, "psychopathy", [2023], {"P1"})
    assert deleted == 1
    remaining = storage.all_projects(conn, topic="psychopathy")
    assert [r.project_num for r in remaining] == ["P1"]


def test_reconcile_topic_never_touches_fiscal_years_outside_the_sync(conn):
    storage.upsert_projects(conn, [
        make_project(topic="psychopathy", project_num="P1", fiscal_year=2022),  # not resynced
        make_project(topic="psychopathy", project_num="P2", fiscal_year=2023),
    ])
    # This sync only covered FY2023, and returned nothing for it.
    deleted = storage.reconcile_topic(conn, "psychopathy", [2023], set())
    assert deleted == 1
    remaining = storage.all_projects(conn, topic="psychopathy")
    assert [r.project_num for r in remaining] == ["P1"]


def test_reconcile_topic_never_touches_other_topics(conn):
    storage.upsert_projects(conn, [
        make_project(topic="psychopathy", project_num="P1", fiscal_year=2023),
        make_project(topic="stress cortisol", project_num="P1", fiscal_year=2023),
    ])
    storage.reconcile_topic(conn, "psychopathy", [2023], set())
    remaining = storage.all_projects(conn)
    assert [(r.topic, r.project_num) for r in remaining] == [("stress cortisol", "P1")]


def test_reconcile_topic_empty_fiscal_years_is_a_noop(conn):
    storage.upsert_projects(conn, [make_project(project_num="P1", fiscal_year=2023)])
    deleted = storage.reconcile_topic(conn, "psychopathy", [], set())
    assert deleted == 0
    assert storage.project_count(conn) == 1
