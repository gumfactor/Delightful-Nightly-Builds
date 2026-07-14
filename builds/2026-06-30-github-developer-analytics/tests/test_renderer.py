"""Tests for HTML dashboard rendering."""

import sys
import os
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from renderer import render_dashboard
from analytics import aggregate


def _minimal_payload() -> dict:
    from datetime import datetime, timezone
    commits = {}
    langs = {}
    return aggregate(commits, langs, generated_at="2026-06-30T00:00:00Z")


def _rich_payload() -> dict:
    from datetime import datetime, timezone
    def _dt(y, m, d, h=12):
        return datetime(y, m, d, h, tzinfo=timezone.utc)
    commits = {
        "repo-alpha": [_dt(2026, 6, 1), _dt(2026, 5, 15), _dt(2026, 4, 10)],
        "repo-beta": [_dt(2026, 6, 20), _dt(2026, 6, 21)],
        "repo-gamma": [_dt(2026, 3, 5)],
    }
    langs = {
        "repo-alpha": {"Python": 10000, "Shell": 500},
        "repo-beta": {"JavaScript": 8000},
        "repo-gamma": {"Python": 2000, "CSS": 300},
    }
    return aggregate(commits, langs, generated_at="2026-06-30T12:00:00Z")


class TestRenderDashboard:
    def test_output_file_is_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "dashboard.html")
            render_dashboard(_minimal_payload(), out)
            assert os.path.exists(out)

    def test_output_file_is_non_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "dashboard.html")
            render_dashboard(_minimal_payload(), out)
            assert os.path.getsize(out) > 0

    def test_html_contains_doctype(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "dashboard.html")
            render_dashboard(_minimal_payload(), out)
            content = Path(out).read_text()
            assert "<!DOCTYPE html>" in content

    def test_html_contains_chartjs_cdn(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "dashboard.html")
            render_dashboard(_minimal_payload(), out)
            content = Path(out).read_text()
            assert "chart.js@4.4.4" in content

    def test_html_embeds_data_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "dashboard.html")
            payload = _minimal_payload()
            render_dashboard(payload, out)
            content = Path(out).read_text()
            assert "const DATA =" in content

    def test_embedded_json_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "dashboard.html")
            render_dashboard(_minimal_payload(), out)
            content = Path(out).read_text()
            # Extract the DATA JSON
            start = content.index("const DATA =") + len("const DATA =")
            end = content.index(";\nconst LANG_COLORS")
            extracted = content[start:end].strip()
            parsed = json.loads(extracted)
            assert "total_commits" in parsed

    def test_html_has_four_tab_buttons(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "dashboard.html")
            render_dashboard(_minimal_payload(), out)
            content = Path(out).read_text()
            assert 'data-panel="overview"' in content
            assert 'data-panel="timeline"' in content
            assert 'data-panel="rhythm"' in content
            assert 'data-panel="languages"' in content

    def test_html_has_four_panel_divs(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "dashboard.html")
            render_dashboard(_minimal_payload(), out)
            content = Path(out).read_text()
            assert 'id="panel-overview"' in content
            assert 'id="panel-timeline"' in content
            assert 'id="panel-rhythm"' in content
            assert 'id="panel-languages"' in content

    def test_rich_payload_embeds_repo_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "dashboard.html")
            render_dashboard(_rich_payload(), out)
            content = Path(out).read_text()
            assert "repo-alpha" in content

    def test_rich_payload_embeds_language_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "dashboard.html")
            render_dashboard(_rich_payload(), out)
            content = Path(out).read_text()
            assert "Python" in content

    def test_output_path_parent_created_if_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "subdir", "nested", "dashboard.html")
            render_dashboard(_minimal_payload(), out)
            assert os.path.exists(out)

    def test_html_contains_heatmap_element(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "dashboard.html")
            render_dashboard(_minimal_payload(), out)
            content = Path(out).read_text()
            assert "heatmap-table" in content

    def test_html_contains_canvas_elements(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "dashboard.html")
            render_dashboard(_minimal_payload(), out)
            content = Path(out).read_text()
            assert 'id="chart-hour"' in content
            assert 'id="chart-weekday"' in content
            assert 'id="chart-languages"' in content

    def test_generated_date_appears_in_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "dashboard.html")
            render_dashboard(_minimal_payload(), out)
            content = Path(out).read_text()
            assert "2026-06-30" in content

    def test_html_is_utf8_encoded(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "dashboard.html")
            render_dashboard(_minimal_payload(), out)
            # Should not raise on UTF-8 read
            content = Path(out).read_text(encoding="utf-8")
            assert len(content) > 0
