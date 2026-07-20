import os
from unittest.mock import patch

import pytest

import main as canfile_main
import storage
import wikidata_client
import wikipedia_client


SEARCH_RESULT = [{"id": "Q1524829", "label": "Tim Hortons", "description": "Canadian restaurant chain"}]

CLAIMS_CANADIAN = {"P17": ["Q16"], "P159": ["Q172"], "P749": [], "P127": [], "P31": ["Q6881511"]}
LABELS_CANADIAN = {"Q16": "Canada", "Q172": "Oakville", "Q6881511": "restaurant chain"}

WIKI_SUMMARY = {"title": "Tim Hortons", "extract": "A Canadian restaurant chain.", "url": "https://en.wikipedia.org/wiki/Tim_Hortons"}


@pytest.fixture
def db_path(tmp_path):
    return os.path.join(tmp_path, "cli_test.db")


def test_add_company_end_to_end(db_path):
    with patch.object(wikidata_client, "search_entity", return_value=SEARCH_RESULT), \
         patch.object(wikidata_client, "get_claims", return_value=CLAIMS_CANADIAN), \
         patch.object(wikidata_client, "resolve_labels", return_value=LABELS_CANADIAN), \
         patch.object(wikipedia_client, "get_summary", return_value=WIKI_SUMMARY), \
         patch.dict(os.environ, {}, clear=True):
        card = canfile_main.add_company("Tim Hortons", db_path=db_path)

    assert card["verdict"] == "canadian"
    assert card["confidence"] == "high"
    assert card["version"] == 1
    assert card["wikipedia_summary"] == "A Canadian restaurant chain."


def test_add_company_not_found_raises_lookup_failure(db_path):
    with patch.object(wikidata_client, "search_entity", return_value=[]):
        with pytest.raises(canfile_main.LookupFailure):
            canfile_main.add_company("Totally Fictional Xyz", db_path=db_path)


def test_add_company_with_foreign_parent(db_path):
    claims_with_parent = {"P17": ["Q16"], "P159": [], "P749": ["Q99"], "P127": [], "P31": []}
    labels = {"Q16": "Canada", "Q99": "US Holdco"}

    def fake_get_claims(qid):
        if qid == "Q1524829":
            return claims_with_parent
        return {"P17": ["Q30"], "P159": [], "P749": [], "P127": [], "P31": []}

    def fake_resolve_labels(qids):
        if "Q30" in qids:
            return {"Q30": "United States of America"}
        return labels

    with patch.object(wikidata_client, "search_entity", return_value=SEARCH_RESULT), \
         patch.object(wikidata_client, "get_claims", side_effect=fake_get_claims), \
         patch.object(wikidata_client, "resolve_labels", side_effect=fake_resolve_labels), \
         patch.object(wikipedia_client, "get_summary", return_value=None):
        card = canfile_main.add_company("Tim Hortons", db_path=db_path)

    assert card["verdict"] == "foreign"
    assert "United States of America" in card["assessment_text"]


def test_add_company_network_failure_does_not_write_card(db_path):
    with patch.object(wikidata_client, "search_entity", side_effect=wikidata_client.WikidataError("down")):
        with pytest.raises(wikidata_client.WikidataError):
            canfile_main.add_company("Tim Hortons", db_path=db_path)

    conn = storage.get_connection(db_path)
    try:
        assert storage.list_latest(conn) == []
    finally:
        conn.close()


def test_cmd_add_prints_and_returns_zero_on_success(db_path, capsys):
    args = canfile_main.build_parser().parse_args(["--db", db_path, "add", "Tim Hortons"])
    with patch.object(wikidata_client, "search_entity", return_value=SEARCH_RESULT), \
         patch.object(wikidata_client, "get_claims", return_value=CLAIMS_CANADIAN), \
         patch.object(wikidata_client, "resolve_labels", return_value=LABELS_CANADIAN), \
         patch.object(wikipedia_client, "get_summary", return_value=WIKI_SUMMARY):
        exit_code = canfile_main.cmd_add(args)
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Tim Hortons" in captured.out


def test_cmd_add_returns_one_on_lookup_failure(db_path, capsys):
    args = canfile_main.build_parser().parse_args(["--db", db_path, "add", "Nonexistent Co"])
    with patch.object(wikidata_client, "search_entity", return_value=[]):
        exit_code = canfile_main.cmd_add(args)
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error" in captured.err


def test_cmd_show_returns_one_when_no_card_exists(db_path, capsys):
    args = canfile_main.build_parser().parse_args(["--db", db_path, "show", "Nobody Inc"])
    exit_code = canfile_main.cmd_show(args)
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "No knowledge card" in captured.err


def test_cmd_list_reports_empty_state(db_path, capsys):
    args = canfile_main.build_parser().parse_args(["--db", db_path, "list"])
    exit_code = canfile_main.cmd_list(args)
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "No knowledge cards yet" in captured.out


def test_cmd_export_html_writes_file(db_path, tmp_path):
    output_path = os.path.join(tmp_path, "report.html")
    conn = storage.get_connection(db_path)
    storage.insert_card(
        conn,
        company_name="Tim Hortons",
        qid="Q1524829",
        wikidata_facts={"country_labels": ["Canada"]},
        wikipedia_summary="A summary.",
        assessment_text="Likely Canadian-owned.",
        confidence="high",
        verdict="canadian",
        source_urls=["https://www.wikidata.org/wiki/Q1524829"],
    )
    conn.close()

    args = canfile_main.build_parser().parse_args(["--db", db_path, "export-html", output_path])
    exit_code = canfile_main.cmd_export_html(args)

    assert exit_code == 0
    assert os.path.exists(output_path)
    with open(output_path, encoding="utf-8") as handle:
        content = handle.read()
    assert "Tim Hortons" in content
