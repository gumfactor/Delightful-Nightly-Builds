import os
import shutil
import subprocess
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


def run_backlinks(workspace, extra_args=None):
    parser = cli.build_parser()
    args = parser.parse_args(
        ["--db", workspace["db_path"], "backlinks", "--notes-dir", workspace["notes_dir"]]
        + (extra_args or [])
    )
    args.func(args)


def read_note(workspace, filename):
    with open(os.path.join(workspace["notes_dir"], filename), encoding="utf-8") as f:
        return f.read()


def test_backlinks_dry_run_does_not_modify_files(workspace, capsys):
    run_index(workspace)
    before = read_note(workspace, "note_a.md")
    capsys.readouterr()
    run_backlinks(workspace)
    out = capsys.readouterr().out
    assert "Dry run" in out
    assert read_note(workspace, "note_a.md") == before


def test_backlinks_write_without_git_repo_refuses_and_leaves_files_unchanged(workspace):
    run_index(workspace)
    before = read_note(workspace, "note_a.md")
    with pytest.raises(SystemExit):
        run_backlinks(workspace, ["--write"])
    assert read_note(workspace, "note_a.md") == before


def git_commit_all(directory):
    subprocess.run(["git", "init", "-q", directory], check=True)
    subprocess.run(["git", "-C", directory, "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", directory, "-c", "user.email=test@example.com", "-c", "user.name=Test",
         "commit", "-q", "-m", "initial notes"],
        check=True,
    )


def test_backlinks_write_refuses_when_git_repo_has_no_commits_yet(workspace):
    subprocess.run(["git", "init", "-q", workspace["notes_dir"]], check=True)
    run_index(workspace)
    before = read_note(workspace, "note_a.md")
    with pytest.raises(SystemExit):
        run_backlinks(workspace, ["--write"])
    assert read_note(workspace, "note_a.md") == before


def test_backlinks_write_refuses_when_working_tree_is_dirty(workspace):
    git_commit_all(workspace["notes_dir"])
    with open(os.path.join(workspace["notes_dir"], "note_a.md"), "a", encoding="utf-8") as f:
        f.write("\nuncommitted local edit\n")
    run_index(workspace)
    before = read_note(workspace, "note_a.md")
    with pytest.raises(SystemExit):
        run_backlinks(workspace, ["--write"])
    assert read_note(workspace, "note_a.md") == before


def test_backlinks_write_skip_git_check_bypasses_the_guardrail(workspace, capsys):
    run_index(workspace)
    capsys.readouterr()
    run_backlinks(workspace, ["--write", "--skip-git-check"])
    out = capsys.readouterr().out
    assert "Wrote backlinks to" in out


def test_backlinks_write_in_git_repo_inserts_wiki_links_and_is_idempotent(workspace, capsys):
    git_commit_all(workspace["notes_dir"])
    run_index(workspace)
    capsys.readouterr()
    run_backlinks(workspace, ["--write"])
    out = capsys.readouterr().out
    assert "Wrote backlinks to" in out
    updated = read_note(workspace, "note_a.md")
    assert "[[note_b|Investment Workflow]]" in updated

    # Re-running against unchanged notes on disk should be a no-op.
    capsys.readouterr()
    run_backlinks(workspace, ["--write"])
    out = capsys.readouterr().out
    assert "already up to date" in out


def test_backlinks_write_syncs_db_so_next_index_run_skips_written_notes(workspace, capsys):
    git_commit_all(workspace["notes_dir"])
    run_index(workspace)
    run_backlinks(workspace, ["--write"])
    capsys.readouterr()
    run_index(workspace)
    out = capsys.readouterr().out
    assert "Indexed 0 new/changed note(s)" in out


def test_backlinks_write_skips_note_edited_since_last_index(workspace, capsys):
    git_commit_all(workspace["notes_dir"])
    run_index(workspace)
    with open(os.path.join(workspace["notes_dir"], "note_a.md"), "a", encoding="utf-8") as f:
        f.write("\nEdited after indexing, before backlinks was run.\n")
    # Commit the edit so the git-baseline guardrail passes and we can isolate
    # the separate content-hash staleness guard inside write_plans itself.
    git_commit_all(workspace["notes_dir"])
    capsys.readouterr()
    run_backlinks(workspace, ["--write"])
    out = capsys.readouterr().out
    assert "Skipped" in out
    assert "note_a.md" in out
    assert "Edited after indexing, before backlinks was run." in read_note(workspace, "note_a.md")
