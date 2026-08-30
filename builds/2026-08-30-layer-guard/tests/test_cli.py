import json
from unittest.mock import patch

import pytest

from src.cli import analyze, run


def _write(root, rel_path, content):
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _clean_project(tmp_path):
    _write(tmp_path, "core.py", "")
    _write(tmp_path, "ui.py", "import core\n")
    return tmp_path


def _cyclic_project(tmp_path):
    _write(tmp_path, "a.py", "import b\n")
    _write(tmp_path, "b.py", "import a\n")
    return tmp_path


def test_analyze_detects_cycle_end_to_end(tmp_path):
    _cyclic_project(tmp_path)
    result = analyze(str(tmp_path))
    assert len(result.cycles) == 1
    assert set(result.cycles[0].modules) == {"a", "b"}


def test_analyze_clean_project_has_no_cycles(tmp_path):
    _clean_project(tmp_path)
    result = analyze(str(tmp_path))
    assert result.cycles == []


def test_analyze_with_layers_reports_violation(tmp_path):
    _write(tmp_path, "core.py", "import ui\n")  # core reaching up into ui: a violation
    _write(tmp_path, "ui.py", "")
    layers_path = tmp_path / "layers.json"
    layers_path.write_text(json.dumps({"order": ["core", "ui"], "modules": {"core": ["core"], "ui": ["ui"]}}))

    result = analyze(str(tmp_path), layers_path=str(layers_path))
    assert len(result.violations) == 1
    assert result.violations[0].importer == "core"


def test_run_returns_1_for_missing_root(tmp_path, capsys):
    code = run([str(tmp_path / "nope")])
    captured = capsys.readouterr()
    assert code == 1
    assert "Error" in captured.err


def test_run_returns_1_for_malformed_layers_config(tmp_path, capsys):
    _clean_project(tmp_path)
    bad_layers = tmp_path / "bad.json"
    bad_layers.write_text("{not json")
    code = run([str(tmp_path), "--layers", str(bad_layers)])
    captured = capsys.readouterr()
    assert code == 1
    assert "Error" in captured.err


def test_run_json_output_is_valid_json(tmp_path, capsys):
    _clean_project(tmp_path)
    code = run([str(tmp_path), "--json"])
    captured = capsys.readouterr()
    assert code == 0
    data = json.loads(captured.out)
    assert "modules" in data


def test_run_writes_html_report(tmp_path):
    _clean_project(tmp_path)
    out_path = tmp_path / "report.html"
    code = run([str(tmp_path), "--html", str(out_path)])
    assert code == 0
    assert out_path.exists()
    assert "<title>Layer Guard Report</title>" in out_path.read_text()


def test_run_exit_code_2_when_cycles_found(tmp_path):
    _cyclic_project(tmp_path)
    code = run([str(tmp_path)])
    assert code == 2


def test_run_exit_code_0_when_clean(tmp_path):
    _clean_project(tmp_path)
    code = run([str(tmp_path)])
    assert code == 0


def test_run_makes_zero_network_calls_without_api_key(tmp_path, monkeypatch):
    _clean_project(tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def _explode(*args, **kwargs):
        raise AssertionError("urlopen should never be called without an API key")

    with patch("urllib.request.urlopen", side_effect=_explode):
        code = run([str(tmp_path)])
    assert code == 0
