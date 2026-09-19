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
