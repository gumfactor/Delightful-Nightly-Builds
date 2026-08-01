import json

import pytest

from itemscope.cli import build_parser, main


@pytest.fixture
def binary_csv(tmp_path):
    path = tmp_path / "responses.csv"
    rows = ["student_id,item_1,item_2,item_3"]
    for i in range(20):
        rows.append(f"S{i:02d},{1 if i >= 2 else 0},{1 if i >= 10 else 0},1")
    path.write_text("\n".join(rows) + "\n")
    return str(path)


def test_analyze_json_output_has_correct_counts(binary_csv, capsys):
    exit_code = main(["analyze", binary_csv, "--format", "json"])

    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["n_students"] == 20
    assert data["n_items"] == 3


def test_analyze_text_output_contains_header(binary_csv, capsys):
    exit_code = main(["analyze", binary_csv, "--format", "text"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "ItemScope" in captured.out


def test_analyze_html_output_contains_canvas(binary_csv, capsys):
    exit_code = main(["analyze", binary_csv, "--format", "html"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "<canvas" in captured.out


def test_missing_input_file_returns_error_code_not_traceback(tmp_path, capsys):
    missing = str(tmp_path / "nope.csv")

    exit_code = main(["analyze", missing])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err


def test_output_flag_writes_to_file(binary_csv, tmp_path, capsys):
    out_path = tmp_path / "report.html"
    exit_code = main(["analyze", binary_csv, "--format", "html", "--output", str(out_path)])

    assert exit_code == 0
    assert out_path.exists()
    assert "<canvas" in out_path.read_text()


def test_default_format_is_html(binary_csv, capsys):
    exit_code = main(["analyze", binary_csv])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "<!doctype html>" in captured.out


def test_parser_requires_a_command():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])
