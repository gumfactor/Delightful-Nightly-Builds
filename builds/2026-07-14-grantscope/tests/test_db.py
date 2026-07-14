import pytest

import db


@pytest.fixture
def conn():
    connection = db.connect(":memory:")
    yield connection
    connection.close()


def sample_project(project_num="P1", **overrides):
    project = {
        "project_num": project_num,
        "topic": "empathy",
        "title": "Neural correlates of empathy",
        "abstract": "abstract text",
        "pi_name": "Jane Smith",
        "org_name": "Big State University",
        "org_city": "Springfield",
        "org_state": "IL",
        "ic_admin": "NIMH",
        "activity_code": "R01",
        "award_amount": 450000,
        "fiscal_year": 2024,
        "project_start": "2022-05-01",
        "project_end": "2027-04-30",
    }
    project.update(overrides)
    return project


def test_connect_creates_schema(conn):
    tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "projects" in tables
    assert "briefings" in tables


def test_upsert_project_inserts_new_row(conn):
    db.upsert_project(conn, sample_project(), today="2026-07-14")
    rows = db.all_projects(conn)
    assert len(rows) == 1
    assert rows[0]["project_num"] == "P1"
    assert rows[0]["first_seen"] == "2026-07-14"
    assert rows[0]["last_seen"] == "2026-07-14"


def test_upsert_project_dedupes_on_project_num(conn):
    db.upsert_project(conn, sample_project(), today="2026-07-01")
    db.upsert_project(conn, sample_project(award_amount=500000), today="2026-07-14")
    rows = db.all_projects(conn)
    assert len(rows) == 1
    assert rows[0]["first_seen"] == "2026-07-01"
    assert rows[0]["last_seen"] == "2026-07-14"
    assert rows[0]["award_amount"] == 500000


def test_upsert_projects_processes_multiple(conn):
    count = db.upsert_projects(conn, [sample_project("P1"), sample_project("P2")])
    assert count == 2
    assert db.project_count(conn) == 2


def test_all_projects_filters_by_topic(conn):
    db.upsert_project(conn, sample_project("P1", topic="empathy"))
    db.upsert_project(conn, sample_project("P2", topic="stress_coping"))
    rows = db.all_projects(conn, topic="empathy")
    assert len(rows) == 1
    assert rows[0]["project_num"] == "P1"


def test_distinct_topics(conn):
    db.upsert_project(conn, sample_project("P1", topic="empathy"))
    db.upsert_project(conn, sample_project("P2", topic="stress_coping"))
    assert db.distinct_topics(conn) == ["empathy", "stress_coping"]


def test_search_projects_matches_title_and_org(conn):
    db.upsert_project(conn, sample_project("P1", title="Amygdala reactivity study"))
    db.upsert_project(conn, sample_project("P2", title="Unrelated project", org_name="Amygdala Labs"))
    db.upsert_project(conn, sample_project("P3", title="Totally different"))
    results = db.search_projects(conn, "amygdala")
    assert {row["project_num"] for row in results} == {"P1", "P2"}


def test_project_count_empty_db(conn):
    assert db.project_count(conn) == 0


def test_save_and_get_briefing(conn):
    db.save_briefing(conn, "empathy", "This is a briefing.", "template", generated_at="2026-07-14")
    briefing = db.get_briefing(conn, "empathy")
    assert briefing["text"] == "This is a briefing."
    assert briefing["source"] == "template"


def test_save_briefing_overwrites_existing(conn):
    db.save_briefing(conn, "empathy", "First version", "template")
    db.save_briefing(conn, "empathy", "Second version", "ai")
    briefing = db.get_briefing(conn, "empathy")
    assert briefing["text"] == "Second version"
    assert briefing["source"] == "ai"


def test_all_briefings_returns_all_topics(conn):
    db.save_briefing(conn, "empathy", "text a", "template")
    db.save_briefing(conn, "stress_coping", "text b", "template")
    rows = db.all_briefings(conn)
    assert [row["topic"] for row in rows] == ["empathy", "stress_coping"]


def test_get_briefing_returns_none_when_absent(conn):
    assert db.get_briefing(conn, "nonexistent") is None
