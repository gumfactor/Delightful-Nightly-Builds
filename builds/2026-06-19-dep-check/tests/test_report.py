"""Tests for src/report.py — pure HTML/text generation, no network calls."""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import pytest
from src.models import Requirement, PackageResult, Summary
from src.report import render_html, render_terminal


def _req(name="requests", pinned="2.28.0"):
    return Requirement(
        name=name,
        pinned_version=pinned,
        specifier=f"=={pinned}",
        source_file="requirements.txt",
    )


def _result(name="requests", pinned="2.28.0", latest="2.28.0", status="up-to-date",
            yanked=False, yanked_reason=None, days=None):
    return PackageResult(
        req=_req(name=name, pinned=pinned),
        latest_version=latest,
        pinned_upload_date=None,
        days_since_pinned=days,
        status=status,
        yanked=yanked,
        yanked_reason=yanked_reason,
    )


def _summary(total=1, up_to_date=1, patch=0, minor=0, major=0, unpinned=0, yanked=0, unknown=0):
    return Summary(
        total=total, up_to_date=up_to_date, patch=patch, minor=minor,
        major=major, unpinned=unpinned, yanked=yanked, unknown=unknown,
    )


# ---------------------------------------------------------------------------
# render_html
# ---------------------------------------------------------------------------

class TestRenderHtml:
    def test_html_starts_with_doctype(self):
        html = render_html([_result()], _summary())
        assert html.strip().startswith("<!DOCTYPE html>")

    def test_html_contains_package_name(self):
        html = render_html([_result(name="requests")], _summary())
        assert "requests" in html

    def test_html_xss_escaping_in_package_name(self):
        # Synthetic: ensure < and > are escaped in package names
        req = Requirement(name="<script>", pinned_version="1.0.0", specifier="==1.0.0", source_file="requirements.txt")
        r = PackageResult(req=req, latest_version="1.0.0", pinned_upload_date=None,
                          days_since_pinned=None, status="up-to-date")
        html = render_html([r], _summary())
        assert "<script>" not in html
        assert "&lt;script&gt;" in html

    def test_html_contains_pinned_version(self):
        html = render_html([_result(pinned="2.28.0")], _summary())
        assert "2.28.0" in html

    def test_html_contains_latest_version(self):
        html = render_html([_result(latest="2.30.0", status="minor")], _summary(up_to_date=0, minor=1))
        assert "2.30.0" in html

    def test_html_yanked_flag_present(self):
        html = render_html([_result(yanked=True)], _summary(yanked=1))
        assert "YANKED" in html

    def test_html_yanked_reason_in_title_attr(self):
        html = render_html([_result(yanked=True, yanked_reason="Security issue")], _summary(yanked=1))
        assert "Security issue" in html

    def test_html_summary_total_present(self):
        html = render_html([_result(), _result(name="flask")], _summary(total=2, up_to_date=2))
        assert "2" in html

    def test_html_no_results_shows_no_packages(self):
        html = render_html([], Summary())
        assert "No packages found" in html

    def test_html_custom_title_used(self):
        html = render_html([], Summary(), title="My Project Deps")
        assert "My Project Deps" in html


# ---------------------------------------------------------------------------
# render_terminal
# ---------------------------------------------------------------------------

class TestRenderTerminal:
    def test_terminal_contains_package_name(self):
        out = render_terminal([_result(name="requests")], _summary())
        assert "requests" in out

    def test_terminal_contains_pinned_version(self):
        out = render_terminal([_result(pinned="2.28.0")], _summary())
        assert "2.28.0" in out

    def test_terminal_shows_up_to_date_status(self):
        out = render_terminal([_result(status="up-to-date")], _summary())
        assert "up-to-date" in out

    def test_terminal_shows_yanked_flag(self):
        out = render_terminal([_result(yanked=True)], _summary(yanked=1))
        assert "YANKED" in out

    def test_terminal_empty_results(self):
        out = render_terminal([], Summary())
        assert "No packages found" in out

    def test_terminal_summary_line_present(self):
        out = render_terminal([_result()], _summary(total=1, up_to_date=1))
        assert "1 packages" in out
        assert "up-to-date" in out
