import json

import pytest

from src import ai_extract, cli, crossref, db

SAMPLE_BIB = """
@article{smith2020,
  author = {Smith, Jane Marie and Jones, Alice B.},
  title = {The effects of sleep on memory: a randomized trial},
  journal = {Journal of Cognitive Science},
  year = {2020},
  volume = {12},
  number = {3},
  pages = {45--60},
  doi = {10.1000/xyz123}
}
"""


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "citeforge.db")


def _run(argv, db_path):
    return cli.main(["--db", db_path, *argv])


def test_main_add_bibtex_then_list(tmp_path, db_path, capsys):
    bib_file = tmp_path / "refs.bib"
    bib_file.write_text(SAMPLE_BIB, encoding="utf-8")

    code = _run(["add-bibtex", str(bib_file)], db_path)
    assert code == 0
    out = capsys.readouterr().out
    assert "1 added" in out

    code = _run(["list"], db_path)
    assert code == 0
    out = capsys.readouterr().out
    assert "Smith" in out
    assert "The effects of sleep on memory" in out


def test_main_add_bibtex_then_format_apa_matches_worked_example(tmp_path, db_path, capsys):
    bib_file = tmp_path / "refs.bib"
    bib_file.write_text(SAMPLE_BIB, encoding="utf-8")
    _run(["add-bibtex", str(bib_file)], db_path)
    capsys.readouterr()

    code = _run(["format", "--style", "apa"], db_path)
    assert code == 0
    out = capsys.readouterr().out
    assert (
        "Smith, J. M., & Jones, A. B. (2020). The effects of sleep on memory: "
        "A randomized trial. *Journal of Cognitive Science*, *12*(3), 45–60. "
        "https://doi.org/10.1000/xyz123" in out
    )


def test_main_add_bibtex_reimport_does_not_duplicate(tmp_path, db_path):
    bib_file = tmp_path / "refs.bib"
    bib_file.write_text(SAMPLE_BIB, encoding="utf-8")
    _run(["add-bibtex", str(bib_file)], db_path)
    _run(["add-bibtex", str(bib_file)], db_path)

    conn = db.connect(db_path)
    try:
        assert len(db.list_references(conn)) == 1
    finally:
        conn.close()


def test_main_add_bibtex_missing_file_returns_error(db_path, capsys):
    code = _run(["add-bibtex", "/nonexistent/path.bib"], db_path)
    assert code == 1
    assert "not found" in capsys.readouterr().out


def test_cmd_add_doi_uses_injected_transport_and_caches(tmp_path, db_path):
    calls = []

    def fake_transport(url):
        calls.append(url)
        message = {
            "type": "journal-article",
            "title": ["A study"],
            "author": [{"family": "Doe", "given": "Jane"}],
            "container-title": ["Journal X"],
            "issued": {"date-parts": [[2021]]},
            "DOI": "10.1000/abc",
        }
        return json.dumps({"message": message}).encode("utf-8")

    conn = db.connect(db_path)
    args = cli.build_parser().parse_args(["--db", db_path, "add-doi", "10.1000/abc"])
    try:
        code = cli.cmd_add_doi(args, conn, transport=fake_transport)
        assert code == 0
        assert len(calls) == 1
        # a second resolution of the same DOI should hit the cache, not the network
        code = cli.cmd_add_doi(args, conn, transport=fake_transport)
        assert code == 0
        assert len(calls) == 1
    finally:
        conn.close()


def test_cmd_add_doi_handles_not_found_gracefully(db_path, capsys):
    from urllib.error import HTTPError

    def failing_transport(url):
        raise HTTPError(url, 404, "Not Found", {}, None)

    conn = db.connect(db_path)
    args = cli.build_parser().parse_args(["--db", db_path, "add-doi", "10.9999/missing"])
    try:
        code = cli.cmd_add_doi(args, conn, transport=failing_transport)
        assert code == 0  # a resolution error is reported, not a crash
        out = capsys.readouterr().out
        assert "1 error" in out
    finally:
        conn.close()


def test_cmd_add_text_flags_needs_review_without_ai(tmp_path, db_path, capsys):
    text_file = tmp_path / "refs.txt"
    text_file.write_text("just some unstructured text with no clear fields\n", encoding="utf-8")

    conn = db.connect(db_path)
    args = cli.build_parser().parse_args(["--db", db_path, "add-text", str(text_file)])
    try:
        code = cli.cmd_add_text(args, conn, ai_transport=lambda u, p: b"")
        assert code == 0
        out = capsys.readouterr().out
        assert "1 flagged needs_review" in out
    finally:
        conn.close()


def test_cmd_remove(tmp_path, db_path):
    bib_file = tmp_path / "refs.bib"
    bib_file.write_text(SAMPLE_BIB, encoding="utf-8")
    _run(["add-bibtex", str(bib_file)], db_path)

    conn = db.connect(db_path)
    try:
        ref_id = db.list_references(conn)[0].ref_id
    finally:
        conn.close()

    code = _run(["remove", str(ref_id)], db_path)
    assert code == 0

    conn = db.connect(db_path)
    try:
        assert db.list_references(conn) == []
    finally:
        conn.close()


def test_format_on_empty_library_returns_error(db_path):
    code = _run(["format", "--style", "apa"], db_path)
    assert code == 1


def test_compare_prints_all_four_styles(tmp_path, db_path, capsys):
    bib_file = tmp_path / "refs.bib"
    bib_file.write_text(SAMPLE_BIB, encoding="utf-8")
    _run(["add-bibtex", str(bib_file)], db_path)
    capsys.readouterr()

    code = _run(["compare"], db_path)
    assert code == 0
    out = capsys.readouterr().out
    assert "APA 7th Edition" in out
    assert "AMA 11th Edition" in out
    assert "Vancouver / ICMJE" in out
    assert "Chicago Author-Date 17th Edition" in out


def test_render_writes_html_file(tmp_path, db_path):
    bib_file = tmp_path / "refs.bib"
    bib_file.write_text(SAMPLE_BIB, encoding="utf-8")
    _run(["add-bibtex", str(bib_file)], db_path)

    output_path = tmp_path / "report.html"
    code = _run(["render", "-o", str(output_path)], db_path)
    assert code == 0
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content


def test_parse_ids_handles_comma_separated_list():
    assert cli._parse_ids("1,2,3") == [1, 2, 3]
    assert cli._parse_ids(None) == []
    assert cli._parse_ids("") == []
