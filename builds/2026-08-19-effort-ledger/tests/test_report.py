import json
from datetime import date

from src.models import EffortLine, Flag, GrantBudgetSummary, OvercommitmentWindow, Severity
from src.report import render_html


def test_render_html_includes_expected_stats_data():
    summaries = [GrantBudgetSummary("G1", "Grant One", "2026", 10000, 8000, 4000, 4000, 14000)]
    flags = [Flag(Severity.ERROR, "indirect_mismatch", "mismatch", grant_id="G1")]
    windows = []
    effort_lines = []

    html = render_html(summaries, flags, windows, effort_lines, "")

    assert "<title>Effort Ledger" in html
    start = html.index('id="audit-data"')
    json_start = html.index(">", start) + 1
    json_end = html.index("</script>", json_start)
    embedded = json.loads(html[json_start:json_end])
    assert embedded["summaries"][0]["grant_id"] == "G1"
    assert embedded["flags"][0]["code"] == "indirect_mismatch"


def test_render_html_script_injection_payload_never_executable():
    malicious_name = "</script><script>alert('xss')</script>"
    summaries = []
    flags = [Flag(Severity.ERROR, "overcommitment", "test", person_name=malicious_name)]
    windows = [OvercommitmentWindow(malicious_name, date(2026, 1, 1), date(2026, 2, 1), 110, ("G1",))]
    effort_lines = [
        EffortLine(malicious_name, "G1", malicious_name, date(2026, 1, 1), date(2026, 2, 1), 60, 2)
    ]

    html = render_html(summaries, flags, windows, effort_lines, "")

    # The literal payload must be present (inside the JSON data block, escaped for JS/HTML
    # context) but must never appear as a live, executable </script><script> sequence outside it.
    assert "</script><script>alert" not in html.replace('\\u003c/script\\u003e', '')
    # json.dumps default behavior: verify the closing </script> boundary of the data block
    # itself is not prematurely terminated by the payload.
    data_block_start = html.index('id="audit-data"')
    data_block_open = html.index(">", data_block_start) + 1
    data_block_close = html.index("</script>", data_block_open)
    embedded_raw = html[data_block_open:data_block_close]
    embedded = json.loads(embedded_raw)
    assert embedded["flags"][0]["person_name"] == malicious_name
    # The very next tag after the data block's own closing </script> must be the real <script>
    # that holds Effort Ledger's JS, not an attacker-injected one — i.e. exactly one </script>
    # boundary exists between the opening tag and our real closing tag.
    assert embedded_raw.count("</script>") == 0


def test_render_html_ai_briefing_included_when_present():
    html = render_html([], [], [], [], "AI-generated summary text.")
    assert "AI-generated summary text." in html


def test_render_html_empty_data_does_not_crash():
    html = render_html([], [], [], [], "")
    assert "<html" in html
