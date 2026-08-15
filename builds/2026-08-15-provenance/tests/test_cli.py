from unittest.mock import patch

import pytest

from src import cli

SEARCH_RESULTS = {"Acme Canadiana Ltd.": "Q1"}
CLAIMS_BY_QID = {"Q1": {"country": "Q16", "headquarters": None, "parent_org": None, "owned_by": None}}


def _fake_search_entity(name):
    return SEARCH_RESULTS.get(name)


def _fake_get_claims(qid):
    return CLAIMS_BY_QID.get(qid, {"country": None, "headquarters": None, "parent_org": None, "owned_by": None})


@pytest.fixture
def mocked_wikidata():
    with patch("src.batch.wikidata.search_entity", side_effect=_fake_search_entity), \
         patch("src.batch.wikidata.get_claims", side_effect=_fake_get_claims):
        yield


@pytest.fixture
def input_csv(tmp_path):
    path = tmp_path / "businesses.csv"
    path.write_text("name,website\nAcme Canadiana Ltd.,https://acme-canadiana.example\n")
    return path


def test_main_with_no_command_prints_usage_and_exits_nonzero(capsys):
    exit_code = cli.main([])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "usage" in captured.out.lower()


def test_classify_end_to_end_writes_expected_columns(mocked_wikidata, input_csv, tmp_path):
    out_path = tmp_path / "out.csv"
    db_path = tmp_path / "test.db"
    exit_code = cli.main(["classify", str(input_csv), "--out", str(out_path), "--db", str(db_path)])
    assert exit_code == 0
    assert out_path.exists()

    content = out_path.read_text()
    header = content.splitlines()[0]
    for column in ("name", "website", "verdict", "confidence", "evidence", "wikidata_qid", "ai_note"):
        assert column in header


def test_classify_rejects_csv_without_name_column(tmp_path):
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("company,url\nAcme,https://acme.example\n")
    exit_code = cli.main(["classify", str(bad_csv), "--db", str(tmp_path / "t.db")])
    assert exit_code == 1


def test_classify_rejects_empty_csv(tmp_path):
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("name,website\n")
    exit_code = cli.main(["classify", str(empty_csv), "--db", str(tmp_path / "t.db")])
    assert exit_code == 1


def test_classify_with_render_writes_html_report(mocked_wikidata, input_csv, tmp_path):
    out_path = tmp_path / "out.csv"
    report_path = tmp_path / "report.html"
    db_path = tmp_path / "test.db"
    exit_code = cli.main([
        "classify", str(input_csv), "--out", str(out_path), "--db", str(db_path), "--render", str(report_path),
    ])
    assert exit_code == 0
    assert report_path.exists()
    assert "<!doctype html>" in report_path.read_text().lower()


def test_history_with_no_prior_data_returns_nonzero(tmp_path, capsys):
    db_path = tmp_path / "empty.db"
    exit_code = cli.main(["history", "Nobody Has Heard Of This Co", "--db", str(db_path)])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "no history" in captured.out.lower()


def test_history_after_classify_shows_verdict(mocked_wikidata, input_csv, tmp_path, capsys):
    db_path = tmp_path / "test.db"
    cli.main(["classify", str(input_csv), "--out", str(tmp_path / "out.csv"), "--db", str(db_path)])

    exit_code = cli.main(["history", "Acme Canadiana Ltd.", "--db", str(db_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "canadian" in captured.out.lower()
