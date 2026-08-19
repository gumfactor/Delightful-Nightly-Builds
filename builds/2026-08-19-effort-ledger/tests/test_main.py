import csv

from src.main import build_arg_parser, run_audit, write_annotated_budget_csv, write_annotated_effort_csv


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def test_annotated_csvs_do_not_cross_contaminate_row_numbers(tmp_path):
    """Regression test: budget.csv and effort.csv have independent row numbering
    (both start at row 2), so a flag on budget row 7 must never be annotated onto
    effort row 7 — they are different files. Caught during manual verification:
    the CLI was building one row_number->codes map from the merged flag list and
    reusing it for both CSV writers."""
    budget_path = tmp_path / "budget.csv"
    effort_path = tmp_path / "effort.csv"

    # Budget row 7 (6th data row) gets a subcontract_threshold_applied flag.
    write_csv(
        budget_path,
        ["grant_id", "grant_name", "fiscal_year", "category", "description", "direct_cost"],
        [
            ["G1", "Grant One", "2026", "Personnel", "PI", "10000"],
            ["G1", "Grant One", "2026", "Fringe Benefits", "Fringe", "2700"],
            ["G1", "Grant One", "2026", "Travel", "Travel", "1000"],
            ["G1", "Grant One", "2026", "Supplies", "Supplies", "500"],
            ["G1", "Grant One", "2026", "Other", "Other", "200"],
            ["G1", "Grant One", "2026", "Subcontract", "Sub", "40000"],
        ],
    )
    # Effort row 7 (6th data row) is an unrelated, entirely clean commitment.
    write_csv(
        effort_path,
        ["person_name", "grant_id", "grant_name", "period_start", "period_end", "percent_effort"],
        [
            ["A", "G1", "Grant One", "2026-01-01", "2026-03-31", "10"],
            ["B", "G1", "Grant One", "2026-01-01", "2026-03-31", "10"],
            ["C", "G1", "Grant One", "2026-01-01", "2026-03-31", "10"],
            ["D", "G1", "Grant One", "2026-01-01", "2026-03-31", "10"],
            ["E", "G1", "Grant One", "2026-01-01", "2026-03-31", "10"],
            ["F", "G1", "Grant One", "2026-01-01", "2026-03-31", "10"],
        ],
    )

    args = build_arg_parser().parse_args(
        ["--budget", str(budget_path), "--effort", str(effort_path), "--far-rate", "0.5"]
    )
    result = run_audit(args)

    assert any(f.code == "subcontract_threshold_applied" for f in result["budget_flags"])
    assert not any(f.code == "subcontract_threshold_applied" for f in result["effort_flags"])

    budget_out = tmp_path / "budget_flagged.csv"
    effort_out = tmp_path / "effort_flagged.csv"
    write_annotated_budget_csv(str(budget_out), result["budget_lines"], result["budget_flags"])
    write_annotated_effort_csv(str(effort_out), result["effort_lines"], result["effort_flags"])

    with open(effort_out, newline="", encoding="utf-8") as f:
        effort_rows = list(csv.DictReader(f))
    # Row 7 in effort.csv (person "F") must have an empty Flags column — it must never
    # inherit budget row 7's subcontract_threshold_applied flag.
    assert effort_rows[5]["person_name"] == "F"
    assert effort_rows[5]["Flags"] == ""

    with open(budget_out, newline="", encoding="utf-8") as f:
        budget_rows = list(csv.DictReader(f))
    assert budget_rows[5]["category"] == "Subcontract"
    assert "subcontract_threshold_applied" in budget_rows[5]["Flags"]
