import csv
import json
import subprocess
import sys
import os

from src import main as cli_main

BUILD_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_CSV = os.path.join(BUILD_ROOT, "sample_transactions.csv")


def _run_cli(args):
    return subprocess.run(
        [sys.executable, os.path.join(BUILD_ROOT, "src", "main.py"), *args],
        capture_output=True, text=True, timeout=30, cwd=BUILD_ROOT,
        env={**os.environ, "ANTHROPIC_API_KEY": ""},
    )


def test_cli_end_to_end_produces_json_output(tmp_path):
    result = _run_cli(["analyze", SAMPLE_CSV, "--json", "--no-ai"])
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["summary"]["transaction_count"] > 30
    assert payload["summary"]["total_income"] > 0
    assert len(payload["categories"]) > 0


def test_cli_end_to_end_produces_html_output(tmp_path):
    out_html = tmp_path / "report.html"
    result = _run_cli(["analyze", SAMPLE_CSV, "--html", str(out_html), "--no-ai"])
    assert result.returncode == 0
    content = out_html.read_text(encoding="utf-8")
    assert content.startswith("<!DOCTYPE html>")
    assert "Ledger Lens" in content


def test_cli_html_output_categorizes_all_transactions(tmp_path):
    out_html = tmp_path / "report.html"
    _run_cli(["analyze", SAMPLE_CSV, "--html", str(out_html), "--no-ai"])
    content = out_html.read_text(encoding="utf-8")
    import re
    match = re.search(
        r'<script id="ledger-data" type="application/json">(.*?)</script>', content, re.DOTALL
    )
    data = json.loads(match.group(1))
    assert all(t["category"] for t in data["transactions"])
    assert len(data["transactions"]) == data["summary"]["transaction_count"]


def test_cli_out_csv_includes_category_column(tmp_path):
    out_csv = tmp_path / "cleaned.csv"
    result = _run_cli(["analyze", SAMPLE_CSV, "--out-csv", str(out_csv), "--no-ai"])
    assert result.returncode == 0
    with open(out_csv, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) > 30
    assert "Category" in rows[0]
    assert "Recurring" in rows[0]
    assert all(row["Category"] for row in rows)


def test_cli_missing_file_errors_gracefully():
    result = _run_cli(["analyze", "/nonexistent/path/does_not_exist.csv"])
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "Error" in result.stderr


def test_cli_terminal_output_by_default():
    result = _run_cli(["analyze", SAMPLE_CSV, "--no-ai"])
    assert result.returncode == 0
    assert "Ledger Lens" in result.stdout
    assert "Overview" in result.stdout


def test_cli_recurring_charges_appear_in_output():
    result = _run_cli(["analyze", SAMPLE_CSV, "--json", "--no-ai"])
    payload = json.loads(result.stdout)
    merchants = [r["merchant"] for r in payload["recurring"]]
    assert any("NETFLIX" in m.upper() for m in merchants)


def test_cli_with_budgets_flags_over_budget(tmp_path):
    budgets_path = tmp_path / "budgets.json"
    budgets_path.write_text(json.dumps({"Groceries": 50}), encoding="utf-8")
    result = _run_cli(["analyze", SAMPLE_CSV, "--json", "--budgets", str(budgets_path), "--no-ai"])
    payload = json.loads(result.stdout)
    groceries = next(b for b in payload["budget_status"] if b["category"] == "Groceries")
    assert groceries["over_budget"] is True


def test_run_analysis_no_ai_uses_deterministic_insights(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    parser = cli_main.build_parser()
    args = parser.parse_args(["analyze", SAMPLE_CSV, "--no-ai"])
    result = cli_main.run_analysis(args)
    assert result["insights"]
    assert isinstance(result["insights"], str)
