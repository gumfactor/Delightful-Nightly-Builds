import json

import main as cli
from canpulse import render, store

PTS = [["2024-01-01", 1.0], ["2024-02-01", 2.0]]


def test_cache_round_trip(tmp_path):
    p = tmp_path / "c.json"
    store.save_cache({"a": {"points": PTS}}, {"b": "err"}, p)
    doc = store.load_cache(p)
    assert doc["series"]["a"]["points"] == PTS and doc["errors"] == {"b": "err"} and doc["sample"] is False


def test_load_cache_handles_missing_and_corrupt(tmp_path):
    assert store.load_cache(tmp_path / "none.json") is None
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    assert store.load_cache(bad) is None


def test_merge_with_cache_fills_failed_series_only():
    cached = {"sample": False, "series": {"a": {"points": PTS}, "c": {"points": PTS}}}
    merged, _ = store.merge_with_cache({"z": {"points": PTS}}, {"a": "fail"}, cached)
    assert set(merged) == {"z", "a"} and merged["a"]["from_cache"] is True


def test_merge_ignores_sample_cache():
    cached = {"sample": True, "series": {"a": {"points": PTS}}}
    merged, _ = store.merge_with_cache({}, {"a": "fail"}, cached)
    assert merged == {}


def test_safe_json_escapes_script_breakers():
    out = render.safe_json({"x": "</script><b>&"})
    assert "</script>" not in out and "<" not in out and "&" not in out
    assert json.loads(out)["x"] == "</script><b>&"


def test_sample_data_renders_full_page():
    doc = store.load_cache(store.SAMPLE_PATH)
    html = cli.build(doc["series"], {}, {"fetched_at": doc["fetched_at"], "sample": True}, use_ai=False)
    assert "/*__DATA__*/" not in html and "__CHART_JS_URL__" not in html
    assert "chart.js@4.4.4" in html and '"real_rate"' in html and '"curve"' in html


def test_payload_lists_failed_indicators_not_in_series():
    payload = render.build_payload({}, {}, {"unemployment": "HTTP 403"}, {"source": "rules", "lines": [], "error": None}, {})
    assert payload["failed"][0]["label"] == "Unemployment rate"


def test_cli_offline_writes_file(tmp_path):
    out = tmp_path / "d.html"
    assert cli.main(["--offline", "--no-ai", "--out", str(out)]) == 0
    assert out.read_text().startswith("<!doctype html>")
