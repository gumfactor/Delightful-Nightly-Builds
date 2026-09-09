import json

import pytest

from src.cli import build_parser


def run(args, capsys):
    parser = build_parser()
    parsed = parser.parse_args(args)
    parsed.func(parsed)
    return capsys.readouterr()


def test_init_creates_data_file(tmp_path, capsys):
    data_path = tmp_path / "headroom.json"
    run(["init", "--data", str(data_path), "--birth-year", "1990"], capsys)
    assert data_path.exists()
    data = json.loads(data_path.read_text())
    assert data["profile"]["birth_year"] == 1990


def test_init_refuses_to_overwrite_without_force(tmp_path, capsys):
    data_path = tmp_path / "headroom.json"
    run(["init", "--data", str(data_path), "--birth-year", "1990"], capsys)
    run(["init", "--data", str(data_path), "--birth-year", "1999"], capsys)
    data = json.loads(data_path.read_text())
    assert data["profile"]["birth_year"] == 1990  # unchanged


def test_init_force_overwrites(tmp_path, capsys):
    data_path = tmp_path / "headroom.json"
    run(["init", "--data", str(data_path), "--birth-year", "1990"], capsys)
    run(["init", "--data", str(data_path), "--birth-year", "1999", "--force"], capsys)
    data = json.loads(data_path.read_text())
    assert data["profile"]["birth_year"] == 1999


def test_add_contribution_then_status_round_trip(tmp_path, capsys):
    data_path = tmp_path / "headroom.json"
    run(["init", "--data", str(data_path), "--birth-year", "1980"], capsys)
    run(
        [
            "add-contribution",
            "--data",
            str(data_path),
            "--account",
            "tfsa",
            "--date",
            "2020-06-01",
            "--amount",
            "6000",
        ],
        capsys,
    )
    output = run(["status", "--data", str(data_path)], capsys)
    assert "TFSA" in output.out
    assert "RRSP" in output.out


def test_add_rrsp_contribution_defaults_tax_year_to_transaction_year(tmp_path, capsys):
    data_path = tmp_path / "headroom.json"
    run(["init", "--data", str(data_path), "--birth-year", "1980"], capsys)
    run(
        [
            "add-contribution",
            "--data",
            str(data_path),
            "--account",
            "rrsp",
            "--date",
            "2023-05-01",
            "--amount",
            "5000",
        ],
        capsys,
    )
    data = json.loads(data_path.read_text())
    assert data["rrsp_contributions"][0]["tax_year"] == 2023


def test_add_withdrawal(tmp_path, capsys):
    data_path = tmp_path / "headroom.json"
    run(["init", "--data", str(data_path), "--birth-year", "1980"], capsys)
    run(
        ["add-withdrawal", "--data", str(data_path), "--date", "2023-11-01", "--amount", "3000"],
        capsys,
    )
    data = json.loads(data_path.read_text())
    assert data["tfsa_withdrawals"][0]["amount"] == 3000


def test_add_income(tmp_path, capsys):
    data_path = tmp_path / "headroom.json"
    run(["init", "--data", str(data_path), "--birth-year", "1980"], capsys)
    run(
        ["add-income", "--data", str(data_path), "--year", "2023", "--amount", "90000"],
        capsys,
    )
    data = json.loads(data_path.read_text())
    assert data["rrsp_income"][0]["earned_income"] == 90000


def test_import_csv_contributions(tmp_path, capsys):
    data_path = tmp_path / "headroom.json"
    csv_path = tmp_path / "contribs.csv"
    csv_path.write_text("Date,Amount\n2024-01-15,3000\n")
    run(["init", "--data", str(data_path), "--birth-year", "1980"], capsys)
    run(
        [
            "import-csv",
            "--data",
            str(data_path),
            "--file",
            str(csv_path),
            "--type",
            "contributions-tfsa",
        ],
        capsys,
    )
    data = json.loads(data_path.read_text())
    assert len(data["tfsa_contributions"]) == 1


def test_report_writes_html_without_api_key(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    data_path = tmp_path / "headroom.json"
    out_path = tmp_path / "report.html"
    run(["init", "--data", str(data_path), "--birth-year", "1980"], capsys)
    run(
        [
            "add-contribution",
            "--data",
            str(data_path),
            "--account",
            "tfsa",
            "--date",
            "2020-06-01",
            "--amount",
            "6000",
        ],
        capsys,
    )
    run(["report", "--data", str(data_path), "--out", str(out_path)], capsys)
    assert out_path.exists()
    html = out_path.read_text()
    assert "Headroom" in html
    assert "<!doctype html>" in html


def test_status_on_missing_data_file_raises_storage_error(tmp_path, capsys):
    parser = build_parser()
    parsed = parser.parse_args(["status", "--data", str(tmp_path / "nope.json")])
    with pytest.raises(Exception):
        parsed.func(parsed)
