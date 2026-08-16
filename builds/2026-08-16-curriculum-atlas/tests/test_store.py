import pytest

from src import parser, store


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test.db")
    return store.connect(db_path)


def _parsed(concepts, objectives):
    return store.ParsedDocument(
        concepts=[
            store.Concept(id=0, document_id=0, display_name=c[0],
                          normalized_name=parser.normalize_name(c[0]), source=c[1])
            for c in concepts
        ],
        objectives=[store.Objective(id=0, document_id=0, text=t) for t in objectives],
    )


def test_add_course_is_idempotent(conn):
    c1 = store.add_course(conn, "Stress and Coping")
    c2 = store.add_course(conn, "Stress and Coping")
    assert c1.id == c2.id
    assert len(store.list_courses(conn)) == 1


def test_add_course_rejects_empty_name(conn):
    with pytest.raises(ValueError):
        store.add_course(conn, "   ")


def test_get_course_returns_none_for_unknown_course(conn):
    assert store.get_course(conn, "Nonexistent") is None


def test_list_courses_empty_when_none_registered(conn):
    assert store.list_courses(conn) == []


def test_ingest_document_stores_concepts_and_objectives(conn):
    course = store.add_course(conn, "Stress and Coping")
    parsed = _parsed([("HPA Axis", "marker")], ["explain the HPA axis"])
    doc = store.ingest_document(
        conn, course.id, "Fall 2026", "w3.md", "2026-08-16T00:00:00Z", 100, parsed
    )
    concepts = store.list_concepts(conn, course_id=course.id)
    objectives = store.list_objectives(conn, course_id=course.id)
    assert doc.course_name == "Stress and Coping"
    assert len(concepts) == 1
    assert concepts[0]["display_name"] == "HPA Axis"
    assert len(objectives) == 1


def test_reingesting_same_document_replaces_not_duplicates(conn):
    course = store.add_course(conn, "Stress and Coping")
    parsed1 = _parsed([("HPA Axis", "marker")], ["objective one"])
    store.ingest_document(conn, course.id, "Fall 2026", "w3.md", "2026-08-16T00:00:00Z", 100, parsed1)
    assert len(store.list_concepts(conn, course_id=course.id)) == 1

    parsed2 = _parsed([("HPA Axis", "marker"), ("Allostatic Load", "marker")], ["objective one"])
    store.ingest_document(conn, course.id, "Fall 2026", "w3.md", "2026-08-16T01:00:00Z", 120, parsed2)
    concepts = store.list_concepts(conn, course_id=course.id)
    objectives = store.list_objectives(conn, course_id=course.id)
    assert len(concepts) == 2
    assert len(objectives) == 1
    assert len(store.list_documents(conn, course_id=course.id)) == 1


def test_ingest_document_different_term_creates_separate_document(conn):
    course = store.add_course(conn, "Stress and Coping")
    parsed = _parsed([("HPA Axis", "marker")], [])
    store.ingest_document(conn, course.id, "Fall 2026", "w3.md", "t1", 100, parsed)
    store.ingest_document(conn, course.id, "Spring 2027", "w3.md", "t2", 100, parsed)
    assert len(store.list_documents(conn, course_id=course.id)) == 2


def test_list_concepts_filters_by_course_and_term(conn):
    c1 = store.add_course(conn, "Course A")
    c2 = store.add_course(conn, "Course B")
    store.ingest_document(conn, c1.id, "Fall 2026", "a.md", "t", 10, _parsed([("X", "marker")], []))
    store.ingest_document(conn, c2.id, "Fall 2026", "b.md", "t", 10, _parsed([("Y", "marker")], []))
    only_a = store.list_concepts(conn, course_id=c1.id)
    assert len(only_a) == 1
    assert only_a[0]["display_name"] == "X"


def test_concept_notes_cache_round_trip(conn):
    assert store.get_cached_note(conn, "hpa axi") is None
    store.save_note(conn, "hpa axi", "A stress hormone regulation pathway.", "2026-08-16T00:00:00Z")
    assert store.get_cached_note(conn, "hpa axi") == "A stress hormone regulation pathway."


def test_concept_notes_save_overwrites(conn):
    store.save_note(conn, "hpa axi", "First note.", "t1")
    store.save_note(conn, "hpa axi", "Second note.", "t2")
    assert store.get_cached_note(conn, "hpa axi") == "Second note."
