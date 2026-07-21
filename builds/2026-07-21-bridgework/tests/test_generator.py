import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import generator, storage, taxonomy

CONCEPT = taxonomy.get_concept("hpa_axis_response")
DOMAIN = taxonomy.get_domain("kitchen")


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test.db")
    connection = storage.connect(db_path)
    yield connection
    connection.close()


def test_build_template_produces_nonempty_fields():
    draft = generator.build_template(CONCEPT, DOMAIN, "public_talk")
    assert draft["hook"].strip()
    assert draft["analogy"].strip()
    assert draft["caveat"].strip()


def test_build_template_contains_concept_and_domain_names():
    for audience in taxonomy.AUDIENCES:
        draft = generator.build_template(CONCEPT, DOMAIN, audience)
        combined = draft["hook"] + draft["analogy"]
        assert CONCEPT.name.lower() in combined.lower() or DOMAIN.name.lower() in combined.lower()


def test_build_template_caveat_includes_concept_caveat():
    draft = generator.build_template(CONCEPT, DOMAIN, "book_chapter")
    assert CONCEPT.caveat in draft["caveat"]


def test_build_template_differs_across_audiences():
    undergrad = generator.build_template(CONCEPT, DOMAIN, "undergrad_lecture")
    public = generator.build_template(CONCEPT, DOMAIN, "public_talk")
    book = generator.build_template(CONCEPT, DOMAIN, "book_chapter")
    analogies = {undergrad["analogy"], public["analogy"], book["analogy"]}
    assert len(analogies) == 3


def test_build_template_rejects_unknown_audience():
    with pytest.raises(ValueError):
        generator.build_template(CONCEPT, DOMAIN, "not_a_real_audience")


def test_generate_entry_uses_template_when_no_api_key(conn):
    record = generator.generate_entry(CONCEPT, DOMAIN, "public_talk", conn, api_key=None, use_ai=True)
    assert record["source"] == "template"
    assert record["id"] is not None


def test_generate_entry_uses_template_when_use_ai_false(conn):
    with patch("src.ai_client.call_claude") as mock_call:
        record = generator.generate_entry(
            CONCEPT, DOMAIN, "public_talk", conn, api_key="fake-key", use_ai=False
        )
    assert record["source"] == "template"
    mock_call.assert_not_called()


def test_generate_entry_uses_ai_when_available(conn):
    ai_result = {"hook": "AI hook", "analogy": "AI analogy", "caveat": "AI caveat"}
    with patch("src.ai_client.call_claude", return_value=ai_result):
        record = generator.generate_entry(
            CONCEPT, DOMAIN, "public_talk", conn, api_key="fake-key", use_ai=True
        )
    assert record["source"] == "ai"
    assert record["hook"] == "AI hook"


def test_generate_entry_falls_back_when_ai_returns_none(conn):
    with patch("src.ai_client.call_claude", return_value=None):
        record = generator.generate_entry(
            CONCEPT, DOMAIN, "public_talk", conn, api_key="fake-key", use_ai=True
        )
    assert record["source"] == "template"


def test_generate_entry_persists_to_storage(conn):
    generator.generate_entry(CONCEPT, DOMAIN, "public_talk", conn, api_key=None, use_ai=False)
    entries = storage.list_analogies(conn)
    assert len(entries) == 1


def test_generate_entry_novelty_score_drops_on_repeat(conn):
    first = generator.generate_entry(CONCEPT, DOMAIN, "public_talk", conn, api_key=None, use_ai=False)
    second = generator.generate_entry(CONCEPT, DOMAIN, "public_talk", conn, api_key=None, use_ai=False)
    assert second["novelty_score"] < first["novelty_score"]
