import csv
import json
from pathlib import Path

from src.main import main, run_qc, write_cleaned_csv, write_json_report
from src.schema import Schema

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_directory.csv"


def _run_fixture(use_ai=False):
    csv_bytes = FIXTURE_PATH.read_bytes()
    return run_qc(csv_bytes, Schema.default(), use_ai=use_ai)


def test_run_qc_flags_every_seeded_issue_type():
    report = _run_fixture()
    codes_by_row = {
        row["row_index"]: {f["code"] for f in row["flags"]} for row in report["rows"]
    }

    assert "missing_required_field" in codes_by_row[2]
    assert "ragged_row" in codes_by_row[3]
    assert "invalid_province" in codes_by_row[4]
    assert "invalid_website" in codes_by_row[5]
    assert "ownership_pct_out_of_range" in codes_by_row[6]
    assert "ownership_pct_not_numeric" in codes_by_row[7]
    assert "unmapped_ownership_status" in codes_by_row[8]
    assert "invalid_email" in codes_by_row[9]
    assert "exact_duplicate" in codes_by_row[10]
    assert "exact_duplicate" in codes_by_row[11]
    assert "near_duplicate" in codes_by_row[12]
    assert "near_duplicate" in codes_by_row[13]


def test_run_qc_clean_rows_have_no_flags():
    report = _run_fixture()
    codes_by_row = {
        row["row_index"]: {f["code"] for f in row["flags"]} for row in report["rows"]
    }
    assert codes_by_row[1] == set()
    assert codes_by_row[15] == set()


def test_run_qc_summary_counts_match_expected_distribution():
    report = _run_fixture()
    summary = report["summary"]
    assert summary["total_rows"] == 15
    assert summary["error_rows"] == 5   # rows 2, 3, 4, 6, 7
    assert summary["warning_rows"] == 7  # rows 5, 8, 9, 10, 11, 12, 13
    assert summary["clean_rows"] == 3    # rows 1, 14, 15
    assert summary["duplicate_cluster_count"] == 2


def test_run_qc_recommended_actions_match_severity():
    report = _run_fixture()
    actions_by_row = {row["row_index"]: row["recommended_action"] for row in report["rows"]}
    assert actions_by_row[2] == "drop"
    assert actions_by_row[5] == "review"
    assert actions_by_row[1] == "keep"


def test_run_qc_without_ai_key_generated_with_ai_is_false(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    report = _run_fixture(use_ai=True)
    assert report["generated_with_ai"] is False


def test_write_cleaned_csv_includes_flag_columns(tmp_path):
    report = _run_fixture()
    out_path = tmp_path / "cleaned.csv"
    write_cleaned_csv(report, out_path)

    with open(out_path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 15
    assert "QC_Flags" in rows[0]
    assert "Recommended_Action" in rows[0]
    row2 = rows[1]
    assert row2["Recommended_Action"] == "drop"
    assert "missing_required_field" in row2["QC_Flags"]


def test_write_json_report_round_trips(tmp_path):
    report = _run_fixture()
    out_path = tmp_path / "report.json"
    write_json_report(report, out_path)
    loaded = json.loads(out_path.read_text(encoding="utf-8"))
    assert loaded["summary"]["total_rows"] == 15


def test_main_end_to_end_writes_all_outputs(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    out_dir = tmp_path / "output"
    exit_code = main([str(FIXTURE_PATH), "--out-dir", str(out_dir)])
    assert exit_code == 0
    assert (out_dir / "cleaned.csv").exists()
    assert (out_dir / "report.json").exists()
    assert (out_dir / "report.html").exists()
    html = (out_dir / "report.html").read_text(encoding="utf-8")
    assert "alert(1)</script>" not in html


def test_main_returns_error_code_for_missing_file(tmp_path, capsys):
    exit_code = main([str(tmp_path / "does-not-exist.csv")])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_main_returns_error_code_for_missing_schema_file(tmp_path, capsys):
    exit_code = main([str(FIXTURE_PATH), "--schema", str(tmp_path / "no-such-schema.json")])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "schema file not found" in captured.err


def test_main_respects_custom_schema(tmp_path):
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps({"required_columns": ["business_name"]}), encoding="utf-8")
    out_dir = tmp_path / "output"
    exit_code = main([str(FIXTURE_PATH), "--schema", str(schema_path), "--out-dir", str(out_dir)])
    assert exit_code == 0
    report = json.loads((out_dir / "report.json").read_text(encoding="utf-8"))
    # With only business_name required, row 3 (ragged, but has a business_name)
    # no longer gets a missing_required_field flag for the empty website.
    row3 = next(r for r in report["rows"] if r["row_index"] == 3)
    assert "missing_required_field" not in {f["code"] for f in row3["flags"]}
