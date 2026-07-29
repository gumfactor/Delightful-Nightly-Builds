import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
import main as cli
import crossref_client
import store


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "cli_test.db")


def test_add_manual(db_path, capsys):
    rc = cli.main(["--db", db_path, "add", "--manual", "--title", "Manual Paper", "--authors", "Jane Doe"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Manual Paper" in out


def test_add_manual_missing_title_errors(db_path, capsys):
    rc = cli.main(["--db", db_path, "add", "--manual"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "requires --title" in err


def test_add_no_args_errors(db_path, capsys):
    rc = cli.main(["--db", db_path, "add"])
    assert rc == 1


def test_add_via_doi_mocked(db_path, monkeypatch, capsys):
    def fake_lookup(doi, request_fn=None):
        return {"doi": doi, "title": "Mocked Paper", "authors": ["X"], "year": 2020,
                "journal": "J", "abstract": "abs"}
    monkeypatch.setattr(cli.crossref_client, "lookup_doi", fake_lookup)
    rc = cli.main(["--db", db_path, "add", "10.1/mock"])
    assert rc == 0
    assert "Mocked Paper" in capsys.readouterr().out


def test_add_duplicate_doi_errors(db_path, monkeypatch, capsys):
    def fake_lookup(doi, request_fn=None):
        return {"doi": doi, "title": "P", "authors": [], "year": 2020, "journal": None, "abstract": None}
    monkeypatch.setattr(cli.crossref_client, "lookup_doi", fake_lookup)
    cli.main(["--db", db_path, "add", "10.1/dup"])
    rc = cli.main(["--db", db_path, "add", "10.1/dup"])
    assert rc == 1
    assert "already exists" in capsys.readouterr().err


def test_status_and_list(db_path, capsys):
    cli.main(["--db", db_path, "add", "--manual", "--title", "P1", "--authors", "A"])
    rc = cli.main(["--db", db_path, "status", "1", "reading"])
    assert rc == 0
    capsys.readouterr()
    cli.main(["--db", db_path, "list"])
    out = capsys.readouterr().out
    assert "P1" in out
    assert "reading" in out


def test_status_nonexistent_paper_errors(db_path, capsys):
    rc = cli.main(["--db", db_path, "status", "999", "read"])
    assert rc == 1


def test_note_add_and_show(db_path, capsys):
    cli.main(["--db", db_path, "add", "--manual", "--title", "P1", "--authors", "A"])
    capsys.readouterr()
    rc = cli.main(["--db", db_path, "note", "1", "Interesting methodology."])
    assert rc == 0
    capsys.readouterr()
    cli.main(["--db", db_path, "show", "1"])
    out = capsys.readouterr().out
    assert "Interesting methodology." in out


def test_tag_manual(db_path, capsys):
    cli.main(["--db", db_path, "add", "--manual", "--title", "P1", "--authors", "A"])
    capsys.readouterr()
    rc = cli.main(["--db", db_path, "tag", "1", "stress,empathy"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "empathy" in out
    assert "stress" in out


def test_tag_ai_no_key_uses_fallback(db_path, monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cli.main(["--db", db_path, "add", "--manual", "--title", "Stress and Cortisol Study", "--authors", "A"])
    capsys.readouterr()
    rc = cli.main(["--db", db_path, "tag", "1", "--ai-tag"])
    assert rc == 0


def test_export_bibtex_to_stdout(db_path, capsys):
    cli.main(["--db", db_path, "add", "--manual", "--title", "Exportable Paper", "--authors", "Jane Doe", "--year", "2022"])
    capsys.readouterr()
    rc = cli.main(["--db", db_path, "export", "bibtex"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "@article{" in out
    assert "Exportable Paper" in out


def test_export_bibtex_to_file(db_path, tmp_path):
    cli.main(["--db", db_path, "add", "--manual", "--title", "P", "--authors", "A"])
    out_file = str(tmp_path / "refs.bib")
    rc = cli.main(["--db", db_path, "export", "bibtex", "--out", out_file])
    assert rc == 0
    assert os.path.exists(out_file)
    with open(out_file) as f:
        assert "@article{" in f.read()


def test_render_writes_html_file(db_path, tmp_path):
    cli.main(["--db", db_path, "add", "--manual", "--title", "P", "--authors", "A"])
    out_file = str(tmp_path / "dashboard.html")
    rc = cli.main(["--db", db_path, "render", "--out", out_file])
    assert rc == 0
    with open(out_file) as f:
        content = f.read()
        assert "<html" in content


def test_resurface_no_candidates(db_path, capsys):
    cli.main(["--db", db_path, "add", "--manual", "--title", "P", "--authors", "A"])
    capsys.readouterr()
    rc = cli.main(["--db", db_path, "resurface"])
    assert rc == 0
    assert "Nothing to resurface" in capsys.readouterr().out
