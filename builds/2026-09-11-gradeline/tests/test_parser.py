import pytest

from src.parser import ParseError, load_from_delimited_file, load_from_folder, load_submissions


def test_load_from_folder_reads_txt_and_md(tmp_path):
    (tmp_path / "alice.txt").write_text("Alice's submission text.")
    (tmp_path / "bob.md").write_text("Bob's submission text.")
    subs = load_from_folder(str(tmp_path))
    identifiers = sorted(s.identifier for s in subs)
    assert identifiers == ["alice", "bob"]


def test_load_from_folder_ignores_other_extensions(tmp_path):
    (tmp_path / "alice.txt").write_text("Alice's submission text.")
    (tmp_path / "notes.pdf").write_bytes(b"%PDF-fake")
    (tmp_path / ".DS_Store").write_bytes(b"junk")
    subs = load_from_folder(str(tmp_path))
    assert [s.identifier for s in subs] == ["alice"]


def test_load_from_folder_missing_dir_raises(tmp_path):
    with pytest.raises(ParseError, match="Not a directory"):
        load_from_folder(str(tmp_path / "does_not_exist"))


def test_load_from_folder_empty_dir_raises(tmp_path):
    with pytest.raises(ParseError, match="No .txt/.md files"):
        load_from_folder(str(tmp_path))


def test_load_from_delimited_file_splits_correctly(tmp_path):
    path = tmp_path / "all.txt"
    path.write_text("=== Alice ===\nAlice text here.\n=== Bob ===\nBob text here.\n")
    subs = load_from_delimited_file(str(path))
    assert [s.identifier for s in subs] == ["Alice", "Bob"]
    assert subs[0].text == "Alice text here."
    assert subs[1].text == "Bob text here."


def test_load_from_delimited_file_last_section_runs_to_eof(tmp_path):
    path = tmp_path / "all.txt"
    path.write_text("=== Alice ===\nLine one.\nLine two.\n")
    subs = load_from_delimited_file(str(path))
    assert len(subs) == 1
    assert "Line one." in subs[0].text
    assert "Line two." in subs[0].text


def test_load_from_delimited_file_no_delimiters_raises(tmp_path):
    path = tmp_path / "plain.txt"
    path.write_text("Just some plain text, no delimiters.")
    with pytest.raises(ParseError, match="delimiters"):
        load_from_delimited_file(str(path))


def test_load_from_delimited_file_missing_file_raises(tmp_path):
    with pytest.raises(ParseError, match="Not a file"):
        load_from_delimited_file(str(tmp_path / "missing.txt"))


def test_load_submissions_dispatches_to_folder(tmp_path):
    (tmp_path / "alice.txt").write_text("Alice text.")
    subs = load_submissions(str(tmp_path))
    assert subs[0].identifier == "alice"


def test_load_submissions_dispatches_to_file(tmp_path):
    path = tmp_path / "all.txt"
    path.write_text("=== Alice ===\nAlice text.\n")
    subs = load_submissions(str(path))
    assert subs[0].identifier == "Alice"
