from pathlib import Path

from src.main import EXIT_LINT_FAILURE, EXIT_OK, EXIT_USAGE_ERROR, main

FIXTURES = Path(__file__).parent / "fixtures"
CLEAN = FIXTURES / "clean" / "instructions.md"
BROKEN = FIXTURES / "broken" / "instructions.md"


def test_cli_exit_code_zero_when_clean(capsys):
    exit_code = main([
        "audit", str(CLEAN),
        "--require-sections", "Goal,Scope,Testing",
        "--skip-ai", "--format", "json",
    ])
    assert exit_code == EXIT_OK


def test_cli_exit_code_one_on_error_severity_with_fail_on(capsys):
    exit_code = main([
        "audit", str(BROKEN),
        "--require-sections", "Goal,Scope,Testing",
        "--skip-ai", "--format", "json", "--fail-on", "error",
    ])
    assert exit_code == EXIT_LINT_FAILURE


def test_cli_fail_on_none_always_zero(capsys):
    exit_code = main([
        "audit", str(BROKEN),
        "--require-sections", "Goal,Scope,Testing",
        "--skip-ai", "--fail-on", "none",
    ])
    assert exit_code == EXIT_OK


def test_cli_missing_input_file_errors_gracefully(capsys):
    exit_code = main(["audit", "/nonexistent/path/does-not-exist.md", "--skip-ai"])
    assert exit_code == EXIT_USAGE_ERROR
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_cli_writes_html_output_file(tmp_path, capsys):
    out_path = tmp_path / "report.html"
    exit_code = main([
        "audit", str(CLEAN), "--skip-ai", "--format", "html", "--out", str(out_path),
    ])
    assert exit_code == EXIT_OK
    content = out_path.read_text(encoding="utf-8")
    assert content.startswith("<!doctype html>")


def test_cli_missing_ground_truth_file_adds_error_finding(capsys):
    exit_code = main([
        "audit", str(CLEAN), "--skip-ai", "--format", "json",
        "--ground-truth", "/nonexistent/ground-truth.md",
    ])
    captured = capsys.readouterr()
    assert exit_code == EXIT_LINT_FAILURE
    assert "missing_ground_truth_file" in captured.out


def test_cli_warning_only_does_not_fail_with_default_threshold(capsys):
    exit_code = main([
        "audit", str(BROKEN), "--skip-ai", "--format", "json", "--fail-on", "warning",
    ])
    assert exit_code == EXIT_LINT_FAILURE
