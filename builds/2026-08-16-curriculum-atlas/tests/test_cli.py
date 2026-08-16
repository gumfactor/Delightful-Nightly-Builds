import os
from unittest.mock import patch

import pytest

from src import cli

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def test_end_to_end_two_courses_share_concept_and_gap_is_flagged(tmp_path, capsys):
    db = str(tmp_path / "atlas.db")
    assert cli.main(["--db", db, "add-course", "--name", "Stress and Coping"]) == 0
    assert cli.main(["--db", db, "add-course", "--name", "Social Affective Neuroscience"]) == 0
    assert cli.main(["--db", db, "add-course", "--name", "AI Applications for Psychologists"]) == 0

    assert cli.main([
        "--db", db, "ingest", "--course", "Stress and Coping", "--term", "Fall 2026",
        "--file", os.path.join(FIXTURES, "stress_coping_w3.md"),
    ]) == 0
    assert cli.main([
        "--db", db, "ingest", "--course", "Social Affective Neuroscience", "--term", "Fall 2026",
        "--file", os.path.join(FIXTURES, "social_affective_w1.md"),
    ]) == 0
    assert cli.main([
        "--db", db, "ingest", "--course", "AI Applications for Psychologists", "--term", "Fall 2026",
        "--file", os.path.join(FIXTURES, "ai_apps_w2.md"),
    ]) == 0

    capsys.readouterr()
    assert cli.main(["--db", db, "overlap"]) == 0
    out = capsys.readouterr().out
    assert "HPA" in out  # concept shared between the two neuroscience courses

    assert cli.main([
        "--db", db, "gaps", "--course", "AI Applications for Psychologists", "--term", "Fall 2026",
    ]) == 0
    out = capsys.readouterr().out
    assert "FLAGGED" in out
    assert "saliency" in out.lower()

    out_html = str(tmp_path / "report.html")
    assert cli.main(["--db", db, "render", "--out", out_html]) == 0
    assert os.path.exists(out_html)
    assert os.path.getsize(out_html) > 0


def test_ingest_unknown_course_exits_nonzero(tmp_path):
    db = str(tmp_path / "atlas.db")
    with pytest.raises(SystemExit) as exc:
        cli.main([
            "--db", db, "ingest", "--course", "Nonexistent", "--term", "Fall 2026",
            "--file", os.path.join(FIXTURES, "stress_coping_w3.md"),
        ])
    assert exc.value.code != 0


def test_ingest_missing_file_returns_nonzero(tmp_path):
    db = str(tmp_path / "atlas.db")
    cli.main(["--db", db, "add-course", "--name", "Course A"])
    result = cli.main([
        "--db", db, "ingest", "--course", "Course A", "--term", "Fall 2026",
        "--file", os.path.join(FIXTURES, "does_not_exist.md"),
    ])
    assert result == 1


def test_unknown_command_exits_nonzero():
    with pytest.raises(SystemExit):
        cli.main(["nope"])


def test_list_courses_empty_message(tmp_path, capsys):
    db = str(tmp_path / "atlas.db")
    cli.main(["--db", db, "list-courses"])
    out = capsys.readouterr().out
    assert "No courses" in out


def test_diff_reports_kept_concepts_when_terms_are_identical(tmp_path, capsys):
    db = str(tmp_path / "atlas.db")
    cli.main(["--db", db, "add-course", "--name", "Stress and Coping"])
    cli.main([
        "--db", db, "ingest", "--course", "Stress and Coping", "--term", "Fall 2025",
        "--file", os.path.join(FIXTURES, "stress_coping_w3.md"),
    ])
    cli.main([
        "--db", db, "ingest", "--course", "Stress and Coping", "--term", "Fall 2026",
        "--file", os.path.join(FIXTURES, "stress_coping_w3.md"),
    ])
    capsys.readouterr()
    result = cli.main([
        "--db", db, "diff", "--course", "Stress and Coping",
        "--term-a", "Fall 2025", "--term-b", "Fall 2026",
    ])
    assert result == 0
    out = capsys.readouterr().out
    assert "Added:   (none)" in out
    assert "Removed: (none)" in out
    assert "HPA" in out


def test_ingest_ai_mark_makes_zero_network_calls_with_no_key(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    db = str(tmp_path / "atlas.db")
    cli.main(["--db", db, "add-course", "--name", "Stress and Coping"])
    with patch("src.ai_enrich.urllib.request.urlopen") as mock_urlopen:
        result = cli.main([
            "--db", db, "ingest", "--course", "Stress and Coping", "--term", "Fall 2026",
            "--file", os.path.join(FIXTURES, "stress_coping_w3.md"), "--ai-mark",
        ])
    mock_urlopen.assert_not_called()
    assert result == 0


def test_concepts_ai_notes_makes_zero_network_calls_with_no_key(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    db = str(tmp_path / "atlas.db")
    cli.main(["--db", db, "add-course", "--name", "Stress and Coping"])
    cli.main([
        "--db", db, "ingest", "--course", "Stress and Coping", "--term", "Fall 2026",
        "--file", os.path.join(FIXTURES, "stress_coping_w3.md"),
    ])
    with patch("src.ai_enrich.urllib.request.urlopen") as mock_urlopen:
        result = cli.main(["--db", db, "concepts", "--course", "Stress and Coping", "--ai-notes"])
    mock_urlopen.assert_not_called()
    assert result == 0


def test_reingest_via_cli_does_not_duplicate_concepts(tmp_path, capsys):
    db = str(tmp_path / "atlas.db")
    cli.main(["--db", db, "add-course", "--name", "Stress and Coping"])
    cli.main([
        "--db", db, "ingest", "--course", "Stress and Coping", "--term", "Fall 2026",
        "--file", os.path.join(FIXTURES, "stress_coping_w3.md"),
    ])
    capsys.readouterr()
    cli.main([
        "--db", db, "ingest", "--course", "Stress and Coping", "--term", "Fall 2026",
        "--file", os.path.join(FIXTURES, "stress_coping_w3.md"),
    ])
    capsys.readouterr()
    cli.main(["--db", db, "concepts", "--course", "Stress and Coping"])
    out = capsys.readouterr().out
    # HPA axis should appear exactly once, not twice, after two identical ingests
    assert out.count("HPA axis") == 1
