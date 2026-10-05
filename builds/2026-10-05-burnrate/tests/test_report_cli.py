import json
import re

from burnrate.cli import main
from burnrate.report import embed_json, html_report, text_summary
from burnrate.analyze import analyze
from burnrate.parse import load_sessions
from burnrate.pricing import PriceTable

from conftest import assistant


def make_result(write_transcript, **kwargs):
    sessions, stats = load_sessions(write_transcript([assistant(**kwargs)]))
    return analyze(sessions, stats, PriceTable.load())


def test_embedded_json_cannot_break_out_of_script_tag(write_transcript):
    res = make_result(write_transcript, cwd="/w/x<!--<script><img onerror=alert(1)>")
    html = html_report(res)
    assert "<!--<script>" not in html and "<img onerror" not in html
    payload = re.search(r'id="data" type="application/json">(.*?)</script>', html, re.S).group(1)
    assert json.loads(payload)["by_project"][0]["project"].startswith("x<!--<script>")


def test_embed_json_escapes_angle_brackets():
    assert "<" not in embed_json({"a": "<b>&"})


def test_text_summary_mentions_estimates_and_totals(write_transcript):
    text = text_summary(make_result(write_transcript))
    assert "1 sessions" in text and "not invoices" in text


def test_demo_command_writes_dashboard(tmp_path, capsys):
    out = tmp_path / "demo.html"
    assert main(["demo", "--out", str(out)]) == 0
    html = out.read_text()
    assert "retry_loop" in html and "claude-future-9" in html
    assert "Findings" in capsys.readouterr().out


def test_report_command_on_custom_root(write_transcript, tmp_path):
    root = write_transcript([assistant()])
    out = tmp_path / "r.html"
    assert main(["report", "--root", str(root), "--out", str(out)]) == 0 and out.exists()


def test_missing_root_exits_2(tmp_path, capsys):
    assert main(["summary", "--root", str(tmp_path / "none")]) == 2
    assert "not found" in capsys.readouterr().err


def test_doctor_fails_when_no_turns(tmp_path):
    (tmp_path / "x.jsonl").write_text("garbage\n")
    assert main(["doctor", "--root", str(tmp_path)]) == 1


def test_bad_timezone_exits_2(write_transcript, capsys):
    assert main(["summary", "--root", str(write_transcript([assistant()])), "--tz", "Mars/Base"]) == 2


def test_json_command_outputs_valid_json(write_transcript, capsys):
    main(["json", "--root", str(write_transcript([assistant()]))])
    assert json.loads(capsys.readouterr().out)["totals"]["turns"] == 1
