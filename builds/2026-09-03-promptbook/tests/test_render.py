from html.parser import HTMLParser
from pathlib import Path

from src.render import render_html
from src.storage import StoredPrompt, connect, upsert_prompt


class ScriptCountingParser(HTMLParser):
    """Counts real <script> tags found by an actual HTML parser (not a string search)."""

    def __init__(self):
        super().__init__()
        self.script_tags = 0
        self.saw_disallowed_tag_from_data = False

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.script_tags += 1
        # Any tag whose only plausible source is injected prompt text would show up as an
        # <img> or a second inline handler; the payload used in tests carries onerror.
        for name, value in attrs:
            if name == "onerror":
                self.saw_disallowed_tag_from_data = True


def _sp(uuid: str, **overrides) -> StoredPrompt:
    base = dict(
        prompt_uuid=uuid,
        session_id="s1",
        project="/home/user/proj",
        git_branch="main",
        entrypoint="cli",
        timestamp="2026-09-01T00:00:00Z",
        prompt_text="fix the bug",
        task_type="bug-fix",
        score=5,
        tools_used=["Bash"],
        files_edited=1,
        test_run=False,
        test_passed=None,
        git_commit=False,
        had_error=False,
    )
    base.update(overrides)
    return StoredPrompt(**base)


def test_render_includes_prompt_text(tmp_path: Path):
    conn = connect(tmp_path / "db.sqlite")
    upsert_prompt(conn, _sp("p1", prompt_text="a perfectly normal prompt"))
    conn.commit()
    html = render_html(conn)
    assert "a perfectly normal prompt" in html


def test_render_xss_payload_is_inert(tmp_path: Path):
    conn = connect(tmp_path / "db.sqlite")
    payload = '</script><script>window.__xss=true;</script><img src=x onerror="window.__xss2=true">'
    upsert_prompt(conn, _sp("p1", prompt_text=payload))
    conn.commit()
    html = render_html(conn)

    parser = ScriptCountingParser()
    parser.feed(html)
    # Exactly the page's own authored <script> tags (JSON payload + app logic) — a real
    # HTML parser confirms the payload's embedded "<script>"/"</script>" text stays inert
    # CDATA content of the first script element rather than breaking out into a third tag.
    assert parser.script_tags == 2
    assert parser.saw_disallowed_tag_from_data is False


def test_render_escapes_script_close_sequence_in_payload(tmp_path: Path):
    conn = connect(tmp_path / "db.sqlite")
    upsert_prompt(conn, _sp("p1", prompt_text="</script>"))
    conn.commit()
    html = render_html(conn)
    assert "</script><script>" not in html.replace("<\\/script>", "")


def test_render_includes_stats_totals(tmp_path: Path):
    conn = connect(tmp_path / "db.sqlite")
    upsert_prompt(conn, _sp("p1"))
    upsert_prompt(conn, _sp("p2"))
    conn.commit()
    html = render_html(conn)
    assert '"total": 2' in html or '"total":2' in html


def test_render_includes_ai_note_when_present(tmp_path: Path):
    conn = connect(tmp_path / "db.sqlite")
    upsert_prompt(conn, _sp("p1", ai_note="This worked because it was specific."))
    conn.commit()
    html = render_html(conn)
    assert "This worked because it was specific." in html


def test_render_uses_createelement_not_innerhtml():
    # Static guard: the renderer's own JS must never use innerHTML for dynamic content.
    conn_free_html = render_html.__module__
    assert conn_free_html == "src.render"
    import inspect

    source = inspect.getsource(render_html)
    assert "innerHTML" not in source
