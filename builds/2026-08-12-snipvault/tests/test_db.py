import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db import add_snippet, connect, get_snippet, list_snippets, remove_snippet, search_snippets


@pytest.fixture
def conn(tmp_path):
    c = connect(tmp_path / "test.db")
    yield c
    c.close()


def test_add_and_get_snippet(conn):
    s = add_snippet(conn, title="Foo", language="python", code="print('hi')", tags=["util"])
    fetched = get_snippet(conn, s.id)
    assert fetched.title == "Foo"
    assert fetched.language == "python"
    assert fetched.tags == ["util"]


def test_add_rejects_empty_title(conn):
    with pytest.raises(ValueError):
        add_snippet(conn, title="  ", language="python", code="x = 1")


def test_add_rejects_empty_code(conn):
    with pytest.raises(ValueError):
        add_snippet(conn, title="Foo", language="python", code="   ")


def test_get_missing_snippet_returns_none(conn):
    assert get_snippet(conn, 9999) is None


def test_get_bumps_usage_count(conn):
    s = add_snippet(conn, title="Foo", language="python", code="x = 1")
    assert s.usage_count == 0
    fetched_once = get_snippet(conn, s.id)
    fetched_twice = get_snippet(conn, s.id)
    assert fetched_once.usage_count == 1
    assert fetched_twice.usage_count == 2


def test_duplicate_titles_get_distinct_ids(conn):
    a = add_snippet(conn, title="Same", language="python", code="a = 1")
    b = add_snippet(conn, title="Same", language="python", code="b = 2")
    assert a.id != b.id


def test_list_filters_by_language(conn):
    add_snippet(conn, title="Py", language="python", code="x = 1")
    add_snippet(conn, title="JS", language="javascript", code="let x = 1;")
    results = list_snippets(conn, language="python")
    assert len(results) == 1
    assert results[0].title == "Py"


def test_list_filters_by_tag(conn):
    add_snippet(conn, title="A", language="python", code="x = 1", tags=["regex", "util"])
    add_snippet(conn, title="B", language="python", code="y = 2", tags=["sql"])
    results = list_snippets(conn, tag="regex")
    assert len(results) == 1
    assert results[0].title == "A"


def test_remove_snippet(conn):
    s = add_snippet(conn, title="Gone", language="python", code="x = 1")
    assert remove_snippet(conn, s.id) is True
    assert get_snippet(conn, s.id) is None


def test_remove_missing_snippet_returns_false(conn):
    assert remove_snippet(conn, 12345) is False


def test_search_empty_db_returns_empty(conn):
    assert search_snippets(conn, ["anything"]) == []


def test_search_title_match_outranks_code_only_match(conn):
    add_snippet(conn, title="Retry wrapper", language="python", code="def f(): pass")
    add_snippet(conn, title="Unrelated", language="python", code="# retry logic buried here\ndef g(): pass")
    results = search_snippets(conn, ["retry"])
    assert len(results) == 2
    assert results[0].title == "Retry wrapper"


def test_search_returns_empty_for_no_match(conn):
    add_snippet(conn, title="Foo", language="python", code="x = 1")
    assert search_snippets(conn, ["zzz_nomatch"]) == []


def test_search_ignores_blank_keywords(conn):
    add_snippet(conn, title="Foo", language="python", code="x = 1")
    assert search_snippets(conn, ["  ", ""]) == []
