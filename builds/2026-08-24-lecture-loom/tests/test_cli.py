import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import main  # noqa: E402

LECTURE_TEXT = (
    "# Test Lecture\n\n"
    "## Objectives\n- Learn one thing\n\n"
    "## Section One\n- a bullet\n- another bullet\n"
)


def _write_lecture(tmp_path, name="lecture.md"):
    path = tmp_path / name
    path.write_text(LECTURE_TEXT, encoding="utf-8")
    return path


def test_missing_path_returns_error_code(capsys):
    code = main.run(["check", "/no/such/path/at/all.md"])
    assert code == 1
    captured = capsys.readouterr()
    assert "error" in captured.err


def test_empty_folder_returns_error_code(tmp_path, capsys):
    code = main.run(["check", str(tmp_path)])
    assert code == 1
    captured = capsys.readouterr()
    assert "no .md or .txt files" in captured.err


def test_invalid_target_minutes_rejected(tmp_path):
    lecture_path = _write_lecture(tmp_path)
    code = main.run(["check", str(lecture_path), "--target-minutes", "0"])
    assert code == 2


def test_invalid_wpm_rejected(tmp_path):
    lecture_path = _write_lecture(tmp_path)
    code = main.run(["check", str(lecture_path), "--wpm", "-10"])
    assert code == 2


def test_check_prints_summary_to_stdout(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    lecture_path = _write_lecture(tmp_path)
    code = main.run(["check", str(lecture_path)])
    assert code == 0
    captured = capsys.readouterr()
    assert "Test Lecture" in captured.out
    assert "timing:" in captured.out
    assert "objectives:" in captured.out


def test_format_writes_outline_and_handout(tmp_path):
    lecture_path = _write_lecture(tmp_path)
    output_dir = tmp_path / "out"
    code = main.run(["format", str(lecture_path), "--output", str(output_dir)])
    assert code == 0
    assert (output_dir / "lecture.outline.md").exists()
    assert (output_dir / "lecture.handout.md").exists()
    outline_text = (output_dir / "lecture.outline.md").read_text(encoding="utf-8")
    assert "Test Lecture" in outline_text


def test_render_writes_dashboard(tmp_path):
    _write_lecture(tmp_path, "one.md")
    _write_lecture(tmp_path, "two.md")
    output_dir = tmp_path / "out"
    code = main.run(["render", str(tmp_path), "--output", str(output_dir)])
    assert code == 0
    dashboard = output_dir / "dashboard.html"
    assert dashboard.exists()
    html = dashboard.read_text(encoding="utf-8")
    assert "<!doctype html>" in html


def test_format_batch_processes_every_file_in_folder(tmp_path):
    _write_lecture(tmp_path, "one.md")
    _write_lecture(tmp_path, "two.md")
    (tmp_path / "ignore.pdf").write_text("not a lecture", encoding="utf-8")
    output_dir = tmp_path / "out"
    code = main.run(["format", str(tmp_path), "--output", str(output_dir)])
    assert code == 0
    written = sorted(p.name for p in output_dir.iterdir())
    assert written == [
        "one.handout.md",
        "one.outline.md",
        "two.handout.md",
        "two.outline.md",
    ]


def test_ai_polish_flag_makes_zero_network_calls_without_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import ai_polish

    def fail_if_called(*args, **kwargs):
        raise AssertionError("should never call urlopen with no API key")

    monkeypatch.setattr(ai_polish, "urlopen", fail_if_called)
    lecture_path = _write_lecture(tmp_path)
    code = main.run(["check", str(lecture_path), "--ai-polish"])
    assert code == 0
