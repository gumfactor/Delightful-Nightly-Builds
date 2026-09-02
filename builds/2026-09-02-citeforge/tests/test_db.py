import pytest

from src import db
from src.models import Author, Reference


@pytest.fixture
def conn(tmp_path):
    connection = db.connect(str(tmp_path / "test.db"))
    yield connection
    connection.close()


def _ref(**overrides):
    defaults = dict(
        ref_type="journal-article",
        authors=[Author("Smith", "Jane")],
        year="2020",
        title="A study",
        container_title="Journal X",
        doi="10.1000/abc",
    )
    defaults.update(overrides)
    return Reference(**defaults)


def test_upsert_reference_inserts_new(conn):
    ref_id, was_new = db.upsert_reference(conn, _ref())
    assert was_new is True
    assert ref_id is not None


def test_upsert_reference_dedupes_by_doi(conn):
    first_id, first_new = db.upsert_reference(conn, _ref())
    second_id, second_new = db.upsert_reference(conn, _ref(title="Updated title"))
    assert first_id == second_id
    assert first_new is True
    assert second_new is False
    refs = db.list_references(conn)
    assert len(refs) == 1
    assert refs[0].title == "Updated title"


def test_upsert_reference_dedupes_by_author_year_title_without_doi(conn):
    ref_a = _ref(doi="", title="Same Title Here")
    ref_b = _ref(doi="", title="Same Title Here")
    db.upsert_reference(conn, ref_a)
    db.upsert_reference(conn, ref_b)
    assert len(db.list_references(conn)) == 1


def test_list_references_preserves_insertion_order(conn):
    db.upsert_reference(conn, _ref(doi="10.1/a", title="First"))
    db.upsert_reference(conn, _ref(doi="10.1/b", title="Second"))
    refs = db.list_references(conn)
    assert [r.title for r in refs] == ["First", "Second"]


def test_get_references_filters_by_id(conn):
    id1, _ = db.upsert_reference(conn, _ref(doi="10.1/a", title="First"))
    id2, _ = db.upsert_reference(conn, _ref(doi="10.1/b", title="Second"))
    refs = db.get_references(conn, [id2])
    assert len(refs) == 1
    assert refs[0].title == "Second"


def test_get_references_empty_id_list_returns_all(conn):
    db.upsert_reference(conn, _ref(doi="10.1/a"))
    db.upsert_reference(conn, _ref(doi="10.1/b"))
    assert len(db.get_references(conn, [])) == 2


def test_remove_reference(conn):
    ref_id, _ = db.upsert_reference(conn, _ref())
    assert db.remove_reference(conn, ref_id) is True
    assert db.list_references(conn) == []


def test_remove_reference_nonexistent_id_returns_false(conn):
    assert db.remove_reference(conn, 9999) is False


def test_crossref_cache_roundtrip(conn):
    assert db.get_cached_crossref(conn, "10.1000/xyz") is None
    db.set_cached_crossref(conn, "10.1000/xyz", {"DOI": "10.1000/xyz"})
    cached = db.get_cached_crossref(conn, "10.1000/xyz")
    assert cached == {"DOI": "10.1000/xyz"}


def test_crossref_cache_overwrite(conn):
    db.set_cached_crossref(conn, "10.1000/xyz", {"DOI": "10.1000/xyz", "v": 1})
    db.set_cached_crossref(conn, "10.1000/xyz", {"DOI": "10.1000/xyz", "v": 2})
    assert db.get_cached_crossref(conn, "10.1000/xyz")["v"] == 2


def test_needs_review_flag_persists(conn):
    ref_id, _ = db.upsert_reference(conn, _ref(doi="", title="X", needs_review=True))
    refs = db.list_references(conn)
    assert refs[0].needs_review is True
