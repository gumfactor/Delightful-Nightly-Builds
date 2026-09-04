import pytest

from src import db


def _make_case(pmid="123", course="Stress and Coping", title="A Study") -> db.Case:
    return db.Case(
        pmid=pmid,
        course=course,
        topic_query="cortisol stress",
        title=title,
        journal="Journal of Testing",
        pub_year=2023,
        citation=f"{title}. Journal of Testing. (2023) PMID:{pmid}",
        abstract_text="A sample abstract with N=40 and r = 0.3, p < .05.",
        sample_size=40,
        population="undergraduate sample",
        methodology="survey",
        effect_size_text="r = 0.3",
        p_value_text="p < .05",
        vignette_text="A deterministic vignette.",
        vignette_source="deterministic",
        discussion_questions=["Question one?", "Question two?", "Question three?"],
        created_at="2026-09-04T08:00:00Z",
    )


@pytest.fixture
def conn(tmp_path):
    connection = db.connect(str(tmp_path / "test.db"))
    yield connection
    connection.close()


def test_pmid_exists_false_for_empty_db(conn):
    assert db.pmid_exists(conn, "123") is False


def test_insert_and_pmid_exists(conn):
    db.insert_case(conn, _make_case(pmid="123"))
    assert db.pmid_exists(conn, "123") is True


def test_get_case_round_trips_all_fields(conn):
    original = _make_case(pmid="555")
    db.insert_case(conn, original)
    fetched = db.get_case(conn, "555")
    assert fetched is not None
    assert fetched.title == original.title
    assert fetched.sample_size == 40
    assert fetched.discussion_questions == ["Question one?", "Question two?", "Question three?"]


def test_get_case_returns_none_for_missing_pmid(conn):
    assert db.get_case(conn, "does-not-exist") is None


def test_list_cases_returns_all_by_default(conn):
    db.insert_case(conn, _make_case(pmid="1"))
    db.insert_case(conn, _make_case(pmid="2"))
    assert len(db.list_cases(conn)) == 2


def test_list_cases_filters_by_course(conn):
    db.insert_case(conn, _make_case(pmid="1", course="Stress and Coping"))
    db.insert_case(conn, _make_case(pmid="2", course="Social Affective Neuroscience"))
    filtered = db.list_cases(conn, course="Stress and Coping")
    assert len(filtered) == 1
    assert filtered[0].pmid == "1"


def test_insert_without_overwrite_raises_on_duplicate_pmid(conn):
    db.insert_case(conn, _make_case(pmid="1"))
    with pytest.raises(Exception):
        db.insert_case(conn, _make_case(pmid="1"), overwrite=False)


def test_insert_with_overwrite_replaces_existing_row(conn):
    db.insert_case(conn, _make_case(pmid="1", title="Old Title"))
    db.insert_case(conn, _make_case(pmid="1", title="New Title"), overwrite=True)
    cases = db.list_cases(conn)
    assert len(cases) == 1
    assert cases[0].title == "New Title"


def test_search_cases_matches_title(conn):
    db.insert_case(conn, _make_case(pmid="1", title="Empathy and Cortisol Reactivity"))
    db.insert_case(conn, _make_case(pmid="2", title="An Unrelated Study"))
    results = db.search_cases(conn, "Cortisol")
    assert len(results) == 1
    assert results[0].pmid == "1"


def test_search_cases_matches_course(conn):
    db.insert_case(conn, _make_case(pmid="1", course="AI Applications for Psychologists"))
    results = db.search_cases(conn, "AI Applications")
    assert len(results) == 1


def test_search_cases_no_match_returns_empty_list(conn):
    db.insert_case(conn, _make_case(pmid="1"))
    assert db.search_cases(conn, "nonexistent keyword xyz") == []


def test_now_iso_format():
    timestamp = db.now_iso()
    assert timestamp.endswith("Z")
    assert "T" in timestamp
