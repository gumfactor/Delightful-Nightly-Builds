import os
import shutil
import tempfile

import pytest

import main as cli

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


@pytest.fixture
def workspace():
    tmp_dir = tempfile.mkdtemp()
    notes_dir = os.path.join(tmp_dir, "notes")
    shutil.copytree(FIXTURES_DIR, notes_dir)
    db_path = os.path.join(tmp_dir, "test.db")
    yield {"tmp_dir": tmp_dir, "notes_dir": notes_dir, "db_path": db_path}
    shutil.rmtree(tmp_dir, ignore_errors=True)


def run_index(workspace, ai=False):
    parser = cli.build_parser()
    args = parser.parse_args(["--db", workspace["db_path"], "index",
                               "--notes-dir", workspace["notes_dir"]] + (["--ai"] if ai else []))
    args.func(args)


def test_index_populates_notes_and_links(workspace, capsys):
    run_index(workspace)
    out = capsys.readouterr().out
    assert "Indexed 4 new/changed note(s), skipped 0 unchanged, removed 0." in out


def test_reindexing_unchanged_files_skips_extraction(workspace, capsys):
    run_index(workspace)
    capsys.readouterr()  # clear first run's output
    run_index(workspace)
    out = capsys.readouterr().out
    assert "Indexed 0 new/changed note(s), skipped 4 unchanged, removed 0." in out


def test_index_detects_changed_file_content(workspace, capsys):
    run_index(workspace)
    with open(os.path.join(workspace["notes_dir"], "note_a.md"), "a", encoding="utf-8") as f:
        f.write("\nExtra content about new automation ideas.\n")
    capsys.readouterr()
    run_index(workspace)
    out = capsys.readouterr().out
    assert "Indexed 1 new/changed note(s), skipped 3 unchanged, removed 0." in out


def test_index_detects_deleted_file(workspace, capsys):
    run_index(workspace)
    os.remove(os.path.join(workspace["notes_dir"], "unrelated.md"))
    capsys.readouterr()
    run_index(workspace)
    out = capsys.readouterr().out
    assert "removed 1." in out


def test_index_ignores_non_note_extensions(workspace):
    with open(os.path.join(workspace["notes_dir"], "image.png"), "wb") as f:
        f.write(b"\x89PNG fake binary data")
    run_index(workspace)
    conn = cli.storage.connect(workspace["db_path"])
    paths = [row["path"] for row in cli.storage.all_notes(conn)]
    assert "image.png" not in paths


def test_index_empty_notes_dir_does_not_crash(tmp_path, capsys):
    empty_dir = tmp_path / "empty_notes"
    empty_dir.mkdir()
    db_path = tmp_path / "empty.db"
    parser = cli.build_parser()
    args = parser.parse_args(["--db", str(db_path), "index", "--notes-dir", str(empty_dir)])
    args.func(args)
    out = capsys.readouterr().out
    assert "Total notes: 0." in out


def test_search_finds_notes_by_shared_topic(workspace, capsys):
    run_index(workspace)
    parser = cli.build_parser()
    args = parser.parse_args(["--db", workspace["db_path"], "search", "workflow"])
    args.func(args)
    out = capsys.readouterr().out
    assert "Agent Workflow" in out
    assert "Investment Workflow" in out


def test_search_no_match_reports_cleanly(workspace, capsys):
    run_index(workspace)
    parser = cli.build_parser()
    args = parser.parse_args(["--db", workspace["db_path"], "search", "zzz_no_such_term"])
    args.func(args)
    out = capsys.readouterr().out
    assert "No notes match" in out


def test_related_reports_shared_concepts(workspace, capsys):
    run_index(workspace)
    parser = cli.build_parser()
    args = parser.parse_args(["--db", workspace["db_path"], "related", "Agent Workflow"])
    args.func(args)
    out = capsys.readouterr().out
    assert "Investment Workflow" in out


def test_related_reports_none_for_isolated_note(workspace, capsys):
    run_index(workspace)
    parser = cli.build_parser()
    args = parser.parse_args(["--db", workspace["db_path"], "related", "Golf Strategy"])
    args.func(args)
    out = capsys.readouterr().out
    assert "no related notes yet" in out


def test_stats_reports_note_and_concept_counts(workspace, capsys):
    run_index(workspace)
    parser = cli.build_parser()
    args = parser.parse_args(["--db", workspace["db_path"], "stats"])
    args.func(args)
    out = capsys.readouterr().out
    assert "Notes: 4" in out


def test_derive_title_prefers_markdown_heading():
    title = cli.derive_title("some-file.md", "# My Real Title\n\nbody")
    assert title == "My Real Title"


def test_derive_title_falls_back_to_filename():
    title = cli.derive_title("my-cool-note.md", "no heading here")
    assert title == "My Cool Note"
