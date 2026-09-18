import csv
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import run  # noqa: E402

SAMPLE_CSV = os.path.join(os.path.dirname(__file__), "..", "sample_data", "sample_budget.csv")


def test_missing_input_file_exits_nonzero(capsys):
    exit_code = run(["/tmp/does-not-exist-eligible-spend.csv", "--grant-start", "2026-04-01", "--grant-end", "2027-03-31"])
    assert exit_code != 0
    captured = capsys.readouterr()
    assert "not found" in captured.err.lower()


def test_grant_start_after_grant_end_exits_nonzero(capsys):
    exit_code = run([SAMPLE_CSV, "--grant-start", "2027-03-31", "--grant-end", "2026-04-01"])
    assert exit_code != 0
    captured = capsys.readouterr()
    assert "grant-start" in captured.err.lower()


def test_invalid_date_format_exits_nonzero():
    exit_code = None
    try:
        run([SAMPLE_CSV, "--grant-start", "04-01-2026", "--grant-end", "2027-03-31"])
    except SystemExit as exc:
        exit_code = exc.code
    assert exit_code is not None and exit_code != 0


def test_successful_run_produces_report_and_flagged_csv_matching_fixture(capsys):
    out_dir = tempfile.mkdtemp(prefix="eligible_spend_test_")
    try:
        exit_code = run(
            [
                SAMPLE_CSV,
                "--grant-start",
                "2026-04-01",
                "--grant-end",
                "2027-03-31",
                "--out-dir",
                out_dir,
            ]
        )
        assert exit_code == 0

        report_path = os.path.join(out_dir, "report.html")
        flagged_path = os.path.join(out_dir, "flagged_items.csv")
        assert os.path.exists(report_path)
        assert os.path.exists(flagged_path)

        with open(flagged_path, newline="", encoding="utf-8") as f:
            flagged_rows = list(csv.DictReader(f))
        # Hand-computed against sample_data/sample_budget.csv (see PRD.md):
        # 16 line items total; 4 clean (no_blocking_rule_found), 2
        # requires_justification, 8 ineligible, 2 outside_grant_period ->
        # 12 flagged rows.
        assert len(flagged_rows) == 12

        captured = capsys.readouterr()
        assert "$26,880.00" in captured.out  # hand-computed total budget
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)


def test_ai_flag_without_api_key_still_completes(monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    out_dir = tempfile.mkdtemp(prefix="eligible_spend_test_ai_")
    try:
        exit_code = run(
            [
                SAMPLE_CSV,
                "--grant-start",
                "2026-04-01",
                "--grant-end",
                "2027-03-31",
                "--out-dir",
                out_dir,
                "--ai",
            ]
        )
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "deterministic fallback" in captured.err.lower()
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)
