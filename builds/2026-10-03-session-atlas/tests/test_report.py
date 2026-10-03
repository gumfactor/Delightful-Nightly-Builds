import json
import re

from conftest import user, write_jsonl
from atlas.demo import generate_demo_logs
from atlas.pricing import DEFAULT_PRICES
from atlas.report import build_payload, render_html, script_safe_json
from atlas.store import Store


def test_script_safe_json_cannot_close_script_tag():
    out = script_safe_json({"x": "</script><script>alert(1)</script> & \u2028"})
    assert "</" not in out and "<script" not in out and json.loads(out)["x"].startswith("</script>")


def test_report_round_trips_payload_and_hostile_prompt_is_inert(tmp_path):
    write_jsonl(tmp_path / "l" / "a.jsonl", [user("2026-09-01T10:00:00Z", "</script><img src=x onerror=alert(1)>")])
    store = Store(tmp_path / "t.db")
    store.index_directory(tmp_path / "l", DEFAULT_PRICES)
    html = render_html(build_payload(store))
    assert "<img src=x" not in html
    blob = re.search(r'<script type="application/json" id="atlas-data">(.*?)</script>', html, re.S).group(1)
    assert json.loads(blob)["sessions"][0]["first"].startswith("</script>")
    store.close()


def test_demo_generator_is_deterministic_and_indexable(tmp_path):
    first = generate_demo_logs(tmp_path / "a", days=10, seed=1)
    second = generate_demo_logs(tmp_path / "b", days=10, seed=1)
    assert first == second > 0
    store = Store(tmp_path / "t.db")
    assert store.index_directory(tmp_path / "a", DEFAULT_PRICES)["parsed"] == first
    payload = build_payload(store, tz_offset_hours=-4)
    assert payload["stats"]["totals"]["sessions"] == first and payload["sessions"][0]["resume"]
    store.close()


def test_cli_end_to_end_writes_report(tmp_path, capsys):
    import main
    out = tmp_path / "out.html"
    code = main.main(["--demo", "--db", str(tmp_path / "x.db"), "--out", str(out)])
    assert code == 0 and out.exists() and "Session Atlas" in out.read_text(encoding="utf-8")


def test_cli_search_and_missing_dir(tmp_path, capsys):
    import main
    assert main.main(["--logs", str(tmp_path / "nope"), "--db", str(tmp_path / "x.db")]) == 2
    main.main(["search", "Bayesian", "--demo", "--db", str(tmp_path / "x.db")])
    assert "Bayesian" in capsys.readouterr().out
