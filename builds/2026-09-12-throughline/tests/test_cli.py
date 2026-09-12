import pytest

from src import cli, storage
from src.semantic_scholar import AuthorCandidate, Paper, SemanticScholarError


def make_db(tmp_path):
    return str(tmp_path / "throughline.db")


def test_parser_requires_a_command():
    parser = cli.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_cmd_lookup_prints_candidates(capsys):
    args = cli.build_parser().parse_args(["lookup", "Jane Doe"])

    def fake_search(name):
        assert name == "Jane Doe"
        return [AuthorCandidate("12345", "Jane Doe", ["State U"], 10, 100, ["Paper A"])]

    exit_code = cli.cmd_lookup(args, search_fn=fake_search)
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "id=12345" in output
    assert "State U" in output
    assert "sync --author-id" in output


def test_cmd_lookup_reports_no_results(capsys):
    args = cli.build_parser().parse_args(["lookup", "Nobody"])
    exit_code = cli.cmd_lookup(args, search_fn=lambda name: [])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "No authors found" in output


def test_cmd_lookup_handles_api_error(capsys):
    args = cli.build_parser().parse_args(["lookup", "Jane Doe"])

    def failing_search(name):
        raise SemanticScholarError("boom")

    exit_code = cli.cmd_lookup(args, search_fn=failing_search)
    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Error: boom" in output


def test_cmd_sync_writes_papers_to_db(tmp_path, capsys):
    db_path = make_db(tmp_path)
    args = cli.build_parser().parse_args(["--db", db_path, "sync", "--author-id", "12345", "--name", "Jane Doe"])

    def fake_fetch(author_id):
        assert author_id == "12345"
        return [Paper("p1", "Some Paper", "abstract", 2020, "Venue", 10, None)]

    conn = storage.connect(db_path)
    exit_code = cli.cmd_sync(args, conn, fetch_fn=fake_fetch)
    conn.close()

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Synced 1 paper" in output

    conn = storage.connect(db_path)
    papers = storage.list_papers(conn)
    conn.close()
    assert len(papers) == 1
    assert papers[0]["title"] == "Some Paper"


def test_cmd_sync_handles_api_error(tmp_path, capsys):
    db_path = make_db(tmp_path)
    args = cli.build_parser().parse_args(["--db", db_path, "sync", "--author-id", "bad", "--name", "X"])
    conn = storage.connect(db_path)
    exit_code = cli.cmd_sync(args, conn, fetch_fn=lambda aid: (_ for _ in ()).throw(SemanticScholarError("nope")))
    conn.close()
    assert exit_code == 1
    assert "Error: nope" in capsys.readouterr().out


def test_cmd_cluster_requires_papers_first(tmp_path, capsys):
    db_path = make_db(tmp_path)
    conn = storage.connect(db_path)
    args = cli.build_parser().parse_args(["--db", db_path, "cluster"])
    exit_code = cli.cmd_cluster(args, conn)
    conn.close()
    assert exit_code == 1
    assert "Run 'sync' first" in capsys.readouterr().out


def test_cmd_cluster_computes_and_stores_clusters(tmp_path, capsys):
    db_path = make_db(tmp_path)
    conn = storage.connect(db_path)
    storage.upsert_papers(conn, [Paper("p1", "Alpha Bravo Charlie", None, 2020, None, 0, None)])
    args = cli.build_parser().parse_args(["--db", db_path, "cluster"])
    exit_code = cli.cmd_cluster(args, conn)
    output = capsys.readouterr().out
    conn.close()
    assert exit_code == 0
    assert "Computed 1 cluster" in output


def test_cmd_narrative_requires_clusters_first(tmp_path, capsys):
    db_path = make_db(tmp_path)
    conn = storage.connect(db_path)
    args = cli.build_parser().parse_args(["--db", db_path, "narrative"])
    exit_code = cli.cmd_narrative(args, conn)
    conn.close()
    assert exit_code == 1
    assert "Run 'cluster' first" in capsys.readouterr().out


def test_cmd_narrative_generates_deterministic_summary(tmp_path, capsys):
    db_path = make_db(tmp_path)
    conn = storage.connect(db_path)
    storage.upsert_papers(conn, [Paper("p1", "Alpha Bravo Charlie", "abstract", 2020, None, 3, None)])
    storage.replace_clusters(conn, [{"label": "alpha / bravo", "keywords": ["alpha", "bravo"], "paper_ids": ["p1"]}])

    args = cli.build_parser().parse_args(["--db", db_path, "narrative"])
    exit_code = cli.cmd_narrative(args, conn)
    output = capsys.readouterr().out
    conn.close()

    assert exit_code == 0
    assert "[deterministic]" in output


def test_cmd_growth_requires_sync_first(tmp_path, capsys):
    db_path = make_db(tmp_path)
    conn = storage.connect(db_path)
    args = cli.build_parser().parse_args(["--db", db_path, "growth"])
    exit_code = cli.cmd_growth(args, conn)
    conn.close()
    assert exit_code == 1
    assert "Run 'sync' first" in capsys.readouterr().out


def test_cmd_growth_prints_deltas(tmp_path, capsys):
    db_path = make_db(tmp_path)
    conn = storage.connect(db_path)
    storage.upsert_papers(conn, [Paper("p1", "Title", None, 2020, None, 5, None)])
    storage.upsert_papers(conn, [Paper("p1", "Title", None, 2020, None, 9, None)])
    args = cli.build_parser().parse_args(["--db", db_path, "growth"])
    exit_code = cli.cmd_growth(args, conn)
    output = capsys.readouterr().out
    conn.close()
    assert exit_code == 0
    assert "+4" in output


def test_cmd_render_requires_papers_first(tmp_path, capsys):
    db_path = make_db(tmp_path)
    conn = storage.connect(db_path)
    args = cli.build_parser().parse_args(["--db", db_path, "render"])
    exit_code = cli.cmd_render(args, conn)
    conn.close()
    assert exit_code == 1
    assert "Run 'sync' first" in capsys.readouterr().out


def test_cmd_render_writes_html_file(tmp_path, capsys):
    db_path = make_db(tmp_path)
    output_path = tmp_path / "dashboard.html"
    conn = storage.connect(db_path)
    storage.upsert_papers(conn, [Paper("p1", "Title", None, 2020, None, 5, None)])
    args = cli.build_parser().parse_args(["--db", db_path, "render", "--output", str(output_path)])
    exit_code = cli.cmd_render(args, conn)
    conn.close()
    assert exit_code == 0
    assert output_path.exists()
    assert "<!doctype html>" in output_path.read_text()


def test_cmd_papers_lists_stored_papers(tmp_path, capsys):
    db_path = make_db(tmp_path)
    conn = storage.connect(db_path)
    storage.upsert_papers(conn, [Paper("p1", "My Great Paper", None, 2022, None, 12, None)])
    args = cli.build_parser().parse_args(["--db", db_path, "papers"])
    exit_code = cli.cmd_papers(args, conn)
    output = capsys.readouterr().out
    conn.close()
    assert exit_code == 0
    assert "My Great Paper" in output
    assert "12 citations" in output


def test_main_dispatches_papers_command_end_to_end(tmp_path, capsys):
    db_path = make_db(tmp_path)
    exit_code = cli.main(["--db", db_path, "papers"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "No papers" in output
