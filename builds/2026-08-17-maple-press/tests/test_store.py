import os

import pytest

import store


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_maple_press.db")


def test_insert_and_get_piece_roundtrip(db_path):
    conn = store.get_connection(db_path)
    businesses = [{"name": "Acme Co", "category": "Bakery"}]
    piece_id = store.insert_piece(
        conn, "spotlight", "consumer", "general", "Meet Acme Co", "Body text here.",
        businesses, 0.0, ai_polished=False,
    )
    piece = store.get_piece(conn, piece_id)
    conn.close()

    assert piece["headline"] == "Meet Acme Co"
    assert piece["body_markdown"] == "Body text here."
    assert piece["piece_type"] == "spotlight"
    assert piece["businesses"] == businesses
    assert piece["ai_polished"] is False
    assert piece["id"] == piece_id


def test_get_piece_missing_id_raises(db_path):
    conn = store.get_connection(db_path)
    with pytest.raises(ValueError, match="No piece found"):
        store.get_piece(conn, 9999)
    conn.close()


def test_list_pieces_filters_by_type_and_tone(db_path):
    conn = store.get_connection(db_path)
    store.insert_piece(conn, "spotlight", "consumer", "general", "H1", "B1", [], 0.0)
    store.insert_piece(conn, "gift_guide", "editorial", "general", "H2", "B2", [], 0.0)
    store.insert_piece(conn, "spotlight", "editorial", "general", "H3", "B3", [], 0.0)

    all_pieces = store.list_pieces(conn)
    spotlight_pieces = store.list_pieces(conn, piece_type="spotlight")
    editorial_pieces = store.list_pieces(conn, tone="editorial")
    conn.close()

    assert len(all_pieces) == 3
    assert len(spotlight_pieces) == 2
    assert {p["headline"] for p in spotlight_pieces} == {"H1", "H3"}
    assert len(editorial_pieces) == 2
    assert {p["headline"] for p in editorial_pieces} == {"H2", "H3"}


def test_history_full_texts_returns_headline_and_body_concatenated(db_path):
    conn = store.get_connection(db_path)
    store.insert_piece(conn, "spotlight", "consumer", "general", "My Headline", "My Body", [], 0.0)
    history = store.history_full_texts(conn, "spotlight")
    conn.close()
    assert history == ["My Headline\n\nMy Body"]


def test_history_full_texts_scoped_to_piece_type(db_path):
    conn = store.get_connection(db_path)
    store.insert_piece(conn, "spotlight", "consumer", "general", "H1", "B1", [], 0.0)
    store.insert_piece(conn, "gift_guide", "consumer", "general", "H2", "B2", [], 0.0)
    history = store.history_full_texts(conn, "gift_guide")
    conn.close()
    assert history == ["H2\n\nB2"]


def test_repeated_insert_never_overwrites(db_path):
    conn = store.get_connection(db_path)
    id_a = store.insert_piece(conn, "spotlight", "consumer", "general", "Same Headline", "Same Body", [], 0.0)
    id_b = store.insert_piece(conn, "spotlight", "consumer", "general", "Same Headline", "Same Body", [], 0.0)
    conn.close()

    assert id_a != id_b

    conn = store.get_connection(db_path)
    all_pieces = store.list_pieces(conn)
    conn.close()
    assert len(all_pieces) == 2


def test_get_connection_creates_table_idempotently(db_path):
    conn_a = store.get_connection(db_path)
    conn_a.close()
    conn_b = store.get_connection(db_path)  # should not raise on an already-existing table
    conn_b.close()
    assert os.path.exists(db_path)
