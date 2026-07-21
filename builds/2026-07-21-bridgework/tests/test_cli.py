import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import cli


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "cli_test.db")


def run(argv, db_path):
    args = argv + ["--db", db_path] if "--db" not in argv else argv
    out = io.StringIO()
    code = cli.main(args, out=out)
    return code, out.getvalue()


def test_generate_inserts_requested_count(db_path):
    code, out = run(["generate", "--count", "3", "--no-ai", "--seed", "1"], db_path)
    assert code == 0
    assert out.count("[") == 3


def test_generate_respects_concept_filter(db_path):
    code, out = run(
        ["generate", "--count", "2", "--concept", "allostatic_load", "--no-ai", "--seed", "1"],
        db_path,
    )
    assert code == 0
    code2, list_out = run(["list", "--concept", "allostatic_load"], db_path)
    assert list_out.count("Allostatic Load") == 2


def test_generate_respects_domain_and_audience_filters(db_path):
    code, out = run(
        [
            "generate", "--count", "1", "--domain", "garden", "--audience", "book_chapter",
            "--no-ai", "--seed", "1",
        ],
        db_path,
    )
    assert code == 0
    code2, list_out = run(["list", "--domain", "garden", "--audience", "book_chapter"], db_path)
    assert "book_chapter" in list_out


def test_generate_invalid_concept_returns_error(db_path):
    code, out = run(["generate", "--concept", "not_a_concept", "--no-ai"], db_path)
    assert code == 1


def test_list_empty_db_reports_no_matches(db_path):
    code, out = run(["list"], db_path)
    assert code == 0
    assert "No analogies" in out


def test_list_search_filters(db_path):
    run(["generate", "--count", "3", "--no-ai", "--seed", "1"], db_path)
    code, out = run(["list", "--search", "zzz_no_match_zzz"], db_path)
    assert "No analogies" in out


def test_show_returns_entry_details(db_path):
    run(["generate", "--count", "1", "--no-ai", "--seed", "1"], db_path)
    code, out = run(["show", "1"], db_path)
    assert code == 0
    assert "Hook:" in out
    assert "Analogy:" in out


def test_show_missing_id_returns_error(db_path):
    code, out = run(["show", "9999"], db_path)
    assert code == 1


def test_export_all_produces_markdown(db_path):
    run(["generate", "--count", "2", "--no-ai", "--seed", "1"], db_path)
    code, out = run(["export", "--all"], db_path)
    assert code == 0
    assert "###" in out


def test_export_single_id_produces_markdown(db_path):
    run(["generate", "--count", "1", "--no-ai", "--seed", "1"], db_path)
    code, out = run(["export", "--id", "1"], db_path)
    assert code == 0
    assert "###" in out


def test_export_without_id_or_all_returns_error(db_path):
    run(["generate", "--count", "1", "--no-ai", "--seed", "1"], db_path)
    code, out = run(["export"], db_path)
    assert code == 1


def test_export_to_file_writes_output(db_path, tmp_path):
    run(["generate", "--count", "1", "--no-ai", "--seed", "1"], db_path)
    output_path = str(tmp_path / "out.md")
    code, out = run(["export", "--all", "--output", output_path], db_path)
    assert code == 0
    assert Path(output_path).exists()
    assert "###" in Path(output_path).read_text()


def test_render_writes_html_file(db_path, tmp_path):
    run(["generate", "--count", "2", "--no-ai", "--seed", "1"], db_path)
    output_path = str(tmp_path / "out.html")
    code, out = run(["render", "--output", output_path], db_path)
    assert code == 0
    assert Path(output_path).exists()
    content = Path(output_path).read_text()
    assert "<html" in content


def test_stats_reports_counts(db_path):
    run(["generate", "--count", "3", "--no-ai", "--seed", "1"], db_path)
    code, out = run(["stats"], db_path)
    assert code == 0
    assert "Total analogies: 3" in out


def test_taxonomy_command_lists_concepts_and_domains(db_path):
    out = io.StringIO()
    code = cli.main(["taxonomy"], out=out)
    out = out.getvalue()
    assert code == 0
    assert "Concepts:" in out
    assert "Domains:" in out
    assert "hpa_axis_response" in out


def test_default_db_path_is_inside_build_folder():
    path = cli.default_db_path()
    assert "builds" in path or "data" in path
    assert path.endswith("bridgework.db")
