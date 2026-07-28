import json

from src import heuristics, report, scoring


def _build(text):
    analysis = heuristics.analyze_text(text)
    score_result = scoring.compute_score(analysis)
    return analysis, score_result


def test_render_terminal_includes_score_and_word_count():
    analysis, score_result = _build("A short and clean sentence about the weather.")
    output = report.render_terminal("draft.md", analysis, score_result, use_color=False)
    assert "draft.md" in output
    assert f"Human Voice Score: {score_result['score']}/100" in output
    assert f"Words: {analysis['word_count']}" in output


def test_render_terminal_lists_ai_tell_phrase_hits():
    analysis, score_result = _build("We should delve into this seamless synergy.")
    output = report.render_terminal("draft.md", analysis, score_result, use_color=False)
    assert "delve into" in output
    assert "AI-tell phrases (" in output


def test_render_terminal_no_color_codes_when_disabled():
    analysis, score_result = _build("Plain text with no special patterns at all here.")
    output = report.render_terminal("draft.md", analysis, score_result, use_color=False)
    assert "\033[" not in output


def test_render_terminal_includes_review_section_when_present():
    analysis, score_result = _build("Plain text with no special patterns at all here.")
    review = {"source": "fallback", "items": [{"paragraph": "x", "diagnosis": "sample diagnosis", "rewrite": "sample rewrite"}]}
    output = report.render_terminal("draft.md", analysis, score_result, review, use_color=False)
    assert "sample diagnosis" in output
    assert "sample rewrite" in output


def test_render_json_is_valid_and_round_trips():
    analysis, score_result = _build("We should delve into this seamless synergy today.")
    raw = report.render_json("draft.md", analysis, score_result)
    parsed = json.loads(raw)
    assert parsed["file_path"] == "draft.md"
    assert parsed["score"] == score_result["score"]
    assert parsed["ai_tell_hits"][0]["phrase"] in {"delve into", "seamless", "synergy"}


def test_render_html_escapes_script_injection_in_excerpt():
    malicious_line = "This is fine but <script>alert(1)</script> and also delve into trouble."
    analysis, score_result = _build(malicious_line)
    html_output = report.render_html("draft.md", analysis, score_result)
    assert "<script>alert(1)</script>" not in html_output
    assert "&lt;script&gt;" in html_output


def test_render_html_escapes_malicious_file_path():
    analysis, score_result = _build("Some clean text here.")
    html_output = report.render_html("<img src=x onerror=alert(1)>.md", analysis, score_result)
    assert "<img src=x onerror=alert(1)>" not in html_output


def test_render_html_includes_score_and_is_well_formed():
    analysis, score_result = _build("Some clean text here about the lab.")
    html_output = report.render_html("draft.md", analysis, score_result)
    assert "<!doctype html>" in html_output
    assert f">{score_result['score']}<" in html_output


def test_render_html_shows_history_table_rows():
    analysis, score_result = _build("Some clean text here about the lab.")
    history = [
        {"id": 1, "file_path": "draft.md", "run_at": "2026-07-27T08:00:00+00:00", "word_count": 100, "score": 70.0, "flag_count": 3, "details": {}},
        {"id": 2, "file_path": "draft.md", "run_at": "2026-07-28T08:00:00+00:00", "word_count": 105, "score": 85.0, "flag_count": 1, "details": {}},
    ]
    html_output = report.render_html("draft.md", analysis, score_result, history=history)
    assert "2026-07-27T08:00:00+00:00" in html_output
    assert "2026-07-28T08:00:00+00:00" in html_output


def test_render_html_handles_no_history_gracefully():
    analysis, score_result = _build("Some clean text here about the lab.")
    html_output = report.render_html("draft.md", analysis, score_result, history=[])
    assert "No prior runs recorded" in html_output
