import argparse

import pytest

from src import db, main, pubmed_client


@pytest.fixture
def conn(tmp_path):
    connection = db.connect(str(tmp_path / "cli_test.db"))
    yield connection
    connection.close()


def _fake_articles(n=2):
    return [
        pubmed_client.PubMedArticle(
            pmid=str(1000 + i),
            title=f"Study Number {i}",
            abstract=f"A sample of {20 + i} participants (N={20 + i}) completed a survey, r = 0.{i}1, p < .05.",
            journal="Journal of Testing",
            pub_year=2023,
        )
        for i in range(n)
    ]


def test_generate_requires_course(conn, capsys):
    args = argparse.Namespace(course="  ", query="stress", n=2, ai_polish=False, register="undergrad", force=False)
    exit_code = main.cmd_generate(args, conn)
    assert exit_code == 2


def test_generate_requires_query(conn):
    args = argparse.Namespace(course="Stress and Coping", query="", n=2, ai_polish=False, register="undergrad", force=False)
    exit_code = main.cmd_generate(args, conn)
    assert exit_code == 2


def test_generate_rejects_out_of_range_n(conn):
    args = argparse.Namespace(course="Stress and Coping", query="stress", n=0, ai_polish=False, register="undergrad", force=False)
    assert main.cmd_generate(args, conn) == 2

    args_too_many = argparse.Namespace(course="Stress and Coping", query="stress", n=999, ai_polish=False, register="undergrad", force=False)
    assert main.cmd_generate(args_too_many, conn) == 2


def test_generate_end_to_end_creates_cases(monkeypatch, conn):
    monkeypatch.setattr(pubmed_client, "search_pmids", lambda query, retmax: ["1000", "1001"])
    monkeypatch.setattr(pubmed_client, "fetch_articles", lambda pmids: _fake_articles(2))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    args = argparse.Namespace(
        course="Stress and Coping", query="cortisol stress", n=2, ai_polish=False,
        register="undergrad", force=False,
    )
    exit_code = main.cmd_generate(args, conn)
    assert exit_code == 0
    cases = db.list_cases(conn)
    assert len(cases) == 2
    assert all(case.vignette_source == "deterministic" for case in cases)


def test_generate_skips_already_seen_pmids(monkeypatch, conn):
    monkeypatch.setattr(pubmed_client, "search_pmids", lambda query, retmax: ["1000", "1001"])
    monkeypatch.setattr(pubmed_client, "fetch_articles", lambda pmids: [a for a in _fake_articles(2) if a.pmid in pmids])

    args = argparse.Namespace(
        course="Stress and Coping", query="cortisol stress", n=2, ai_polish=False,
        register="undergrad", force=False,
    )
    main.cmd_generate(args, conn)
    assert len(db.list_cases(conn)) == 2

    # Re-running the identical query must not duplicate the same PMIDs.
    main.cmd_generate(args, conn)
    assert len(db.list_cases(conn)) == 2


def test_generate_force_overwrites_existing_case(monkeypatch, conn):
    monkeypatch.setattr(pubmed_client, "search_pmids", lambda query, retmax: ["1000"])
    monkeypatch.setattr(pubmed_client, "fetch_articles", lambda pmids: [_fake_articles(1)[0]])

    args = argparse.Namespace(
        course="Stress and Coping", query="cortisol stress", n=1, ai_polish=False,
        register="undergrad", force=False,
    )
    main.cmd_generate(args, conn)
    first_created_at = db.get_case(conn, "1000").created_at

    force_args = argparse.Namespace(
        course="Stress and Coping", query="cortisol stress", n=1, ai_polish=False,
        register="undergrad", force=True,
    )
    main.cmd_generate(force_args, conn)
    assert len(db.list_cases(conn)) == 1


def test_generate_handles_pubmed_search_error(monkeypatch, conn):
    def raise_error(query, retmax):
        raise pubmed_client.PubMedError("blocked by proxy")

    monkeypatch.setattr(pubmed_client, "search_pmids", raise_error)
    args = argparse.Namespace(
        course="Stress and Coping", query="cortisol stress", n=2, ai_polish=False,
        register="undergrad", force=False,
    )
    assert main.cmd_generate(args, conn) == 1


def test_generate_with_ai_polish_makes_zero_network_calls_without_key(monkeypatch, conn):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(pubmed_client, "search_pmids", lambda query, retmax: ["1000"])
    monkeypatch.setattr(pubmed_client, "fetch_articles", lambda pmids: [_fake_articles(1)[0]])

    call_count = {"n": 0}

    def fake_urlopen(*args, **kwargs):
        call_count["n"] += 1
        raise AssertionError("must not be called with no API key")

    from src import ai_client

    monkeypatch.setattr(ai_client.urllib.request, "urlopen", fake_urlopen)

    args = argparse.Namespace(
        course="Stress and Coping", query="cortisol stress", n=1, ai_polish=True,
        register="undergrad", force=False,
    )
    exit_code = main.cmd_generate(args, conn)
    assert exit_code == 0
    assert call_count["n"] == 0
    assert db.list_cases(conn)[0].vignette_source == "deterministic"


def test_list_reports_empty_library(conn, capsys):
    args = argparse.Namespace(course=None)
    main.cmd_list(args, conn)
    captured = capsys.readouterr()
    assert "No cases" in captured.out


def test_list_and_show_and_search_round_trip(monkeypatch, conn, capsys):
    monkeypatch.setattr(pubmed_client, "search_pmids", lambda query, retmax: ["1000"])
    monkeypatch.setattr(pubmed_client, "fetch_articles", lambda pmids: [_fake_articles(1)[0]])
    gen_args = argparse.Namespace(
        course="Stress and Coping", query="cortisol stress", n=1, ai_polish=False,
        register="undergrad", force=False,
    )
    main.cmd_generate(gen_args, conn)

    main.cmd_list(argparse.Namespace(course=None), conn)
    captured = capsys.readouterr()
    assert "1000" in captured.out

    show_exit = main.cmd_show(argparse.Namespace(pmid="1000"), conn)
    assert show_exit == 0
    captured = capsys.readouterr()
    assert "Study Number 0" in captured.out

    missing_exit = main.cmd_show(argparse.Namespace(pmid="does-not-exist"), conn)
    assert missing_exit == 1

    search_exit = main.cmd_search(argparse.Namespace(keyword="Study"), conn)
    assert search_exit == 0
    captured = capsys.readouterr()
    assert "1000" in captured.out


def test_export_markdown_to_file(monkeypatch, conn, tmp_path):
    monkeypatch.setattr(pubmed_client, "search_pmids", lambda query, retmax: ["1000"])
    monkeypatch.setattr(pubmed_client, "fetch_articles", lambda pmids: [_fake_articles(1)[0]])
    main.cmd_generate(
        argparse.Namespace(
            course="Stress and Coping", query="cortisol stress", n=1, ai_polish=False,
            register="undergrad", force=False,
        ),
        conn,
    )

    out_file = tmp_path / "cases.md"
    export_args = argparse.Namespace(format="markdown", course=None, out=str(out_file))
    exit_code = main.cmd_export(export_args, conn)
    assert exit_code == 0
    content = out_file.read_text(encoding="utf-8")
    assert "Study Number 0" in content
    assert "Discussion Questions" in content


def test_export_with_no_cases_reports_gracefully(conn, capsys):
    export_args = argparse.Namespace(format="markdown", course=None, out=None)
    exit_code = main.cmd_export(export_args, conn)
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "No cases to export" in captured.out


def test_render_writes_html_file(monkeypatch, conn, tmp_path):
    monkeypatch.setattr(pubmed_client, "search_pmids", lambda query, retmax: ["1000"])
    monkeypatch.setattr(pubmed_client, "fetch_articles", lambda pmids: [_fake_articles(1)[0]])
    main.cmd_generate(
        argparse.Namespace(
            course="Stress and Coping", query="cortisol stress", n=1, ai_polish=False,
            register="undergrad", force=False,
        ),
        conn,
    )

    out_file = tmp_path / "cases.html"
    exit_code = main.cmd_render(argparse.Namespace(out=str(out_file)), conn)
    assert exit_code == 0
    assert out_file.exists()
    assert "CaseForge" in out_file.read_text(encoding="utf-8")


def test_build_parser_generate_defaults():
    parser = main.build_parser()
    args = parser.parse_args(["generate", "--course", "X", "--query", "Y"])
    assert args.n == 3
    assert args.ai_polish is False
    assert args.register == "undergrad"
    assert args.force is False


def test_build_parser_requires_a_command():
    parser = main.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])
