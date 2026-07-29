import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
import store


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test.db")
    c = store.connect(db_path)
    yield c
    c.close()


def test_add_paper_with_doi(conn):
    paper_id = store.add_paper(conn, title="Test Paper", authors=["A. Author"], year=2020, doi="10.1/x")
    row = store.get_paper(conn, paper_id)
    assert row["title"] == "Test Paper"
    assert row["status"] == "to-read"


def test_add_paper_manual_no_doi(conn):
    paper_id = store.add_paper(conn, title="Manual Entry", authors=["B. Writer"])
    row = store.get_paper(conn, paper_id)
    assert row["doi"] is None


def test_duplicate_doi_rejected(conn):
    store.add_paper(conn, title="First", authors=[], doi="10.1/dup")
    with pytest.raises(store.DuplicateDoiError):
        store.add_paper(conn, title="Second", authors=[], doi="10.1/dup")


def test_get_nonexistent_paper_raises(conn):
    with pytest.raises(store.PaperNotFoundError):
        store.get_paper(conn, 9999)


def test_set_status_updates_timestamp(conn):
    paper_id = store.add_paper(conn, title="P", authors=[])
    before = store.get_paper(conn, paper_id)["status_changed_at"]
    store.set_status(conn, paper_id, "reading")
    after = store.get_paper(conn, paper_id)
    assert after["status"] == "reading"
    assert after["status_changed_at"] >= before


def test_set_status_invalid_raises(conn):
    paper_id = store.add_paper(conn, title="P", authors=[])
    with pytest.raises(store.InvalidStatusError):
        store.set_status(conn, paper_id, "not-a-status")


def test_set_status_nonexistent_paper_raises(conn):
    with pytest.raises(store.PaperNotFoundError):
        store.set_status(conn, 9999, "reading")


def test_set_tags_replaces(conn):
    paper_id = store.add_paper(conn, title="P", authors=[])
    store.set_tags(conn, paper_id, ["stress", "empathy"])
    row = store.paper_to_dict(store.get_paper(conn, paper_id))
    assert row["tags"] == ["stress", "empathy"]
    store.set_tags(conn, paper_id, ["cortisol"])
    row2 = store.paper_to_dict(store.get_paper(conn, paper_id))
    assert row2["tags"] == ["cortisol"]


def test_add_note_and_get_notes_ordered(conn):
    paper_id = store.add_paper(conn, title="P", authors=[])
    store.add_note(conn, paper_id, "first note")
    store.add_note(conn, paper_id, "second note")
    notes = store.get_notes(conn, paper_id)
    assert len(notes) == 2
    assert notes[0]["text"] == "first note"
    assert notes[1]["text"] == "second note"


def test_add_note_nonexistent_paper_raises(conn):
    with pytest.raises(store.PaperNotFoundError):
        store.add_note(conn, 9999, "note")


def test_list_papers_filter_by_status(conn):
    id1 = store.add_paper(conn, title="P1", authors=[])
    id2 = store.add_paper(conn, title="P2", authors=[])
    store.set_status(conn, id2, "read")
    to_read = store.list_papers(conn, status="to-read")
    assert len(to_read) == 1
    assert to_read[0]["id"] == id1


def test_list_papers_filter_by_tag(conn):
    id1 = store.add_paper(conn, title="P1", authors=[])
    id2 = store.add_paper(conn, title="P2", authors=[])
    store.set_tags(conn, id1, ["stress"])
    results = store.list_papers(conn, tag="stress")
    assert len(results) == 1
    assert results[0]["id"] == id1


def test_list_papers_filter_by_search(conn):
    store.add_paper(conn, title="Cortisol and Stress Reactivity", authors=["Jane Doe"])
    store.add_paper(conn, title="Unrelated Topic", authors=["John Smith"])
    results = store.list_papers(conn, search="cortisol")
    assert len(results) == 1


def test_paper_to_dict_shape(conn):
    paper_id = store.add_paper(conn, title="P", authors=["A"], year=2022, tags=["x"])
    d = store.paper_to_dict(store.get_paper(conn, paper_id))
    assert d["id"] == paper_id
    assert d["authors"] == ["A"]
    assert d["tags"] == ["x"]
