"""Tests for src/report.py — HTML rendering, escaping, sorting, empty states."""

import pytest

from src import db
from src.report import render_report, write_report

XSS_ARTICLE = {
    "pmid": "99999999",
    "title": "<script>alert('xss')</script> Findings on empathy & the brain",
    "authors": "Doe J",
    "journal": "J Test",
    "pub_date": "2026 Jan",
    "abstract": "An abstract with <b>markup</b> & special chars.",
    "url": "https://pubmed.ncbi.nlm.nih.gov/99999999/",
}


@pytest.fixture
def conn(tmp_path):
    connection = db.connect(str(tmp_path / "report_test.db"))
    yield connection
    connection.close()


class TestRenderReport:
    def test_report_with_no_topics_renders_without_error(self, conn):
        html_out = render_report(conn)
        assert "No topics configured yet" in html_out
        assert "<html" in html_out.lower()

    def test_topic_with_zero_articles_shows_empty_state(self, conn):
        db.add_topic(conn, "Empathy", "empathy[tiab]")
        html_out = render_report(conn)
        assert "No articles yet for this topic" in html_out

    def test_report_includes_one_tab_per_topic(self, conn):
        db.add_topic(conn, "Empathy", "empathy[tiab]")
        db.add_topic(conn, "Stress", "stress[tiab]")
        html_out = render_report(conn)
        assert "Empathy (0)" in html_out
        assert "Stress (0)" in html_out

    def test_articles_sorted_by_relevance_descending(self, conn):
        topic_id = db.add_topic(conn, "Empathy", "empathy[tiab]")
        low_article = dict(XSS_ARTICLE, pmid="11111111", title="Low relevance article")
        high_article = dict(XSS_ARTICLE, pmid="22222222", title="High relevance article")
        db.upsert_article(conn, topic_id, low_article)
        db.upsert_article(conn, topic_id, high_article)
        db.set_scoring(conn, "11111111", 2.0, None, None, "fallback")
        db.set_scoring(conn, "22222222", 9.0, None, None, "fallback")

        html_out = render_report(conn)

        assert html_out.index("High relevance article") < html_out.index("Low relevance article")

    def test_external_title_and_abstract_are_html_escaped(self, conn):
        topic_id = db.add_topic(conn, "Empathy", "empathy[tiab]")
        db.upsert_article(conn, topic_id, XSS_ARTICLE)
        db.set_scoring(conn, "99999999", 5.0, None, None, "fallback")

        html_out = render_report(conn)

        assert "<script>alert" not in html_out
        assert "&lt;script&gt;" in html_out
        assert "&amp;" in html_out

    def test_ai_summary_preferred_over_raw_abstract_when_present(self, conn):
        topic_id = db.add_topic(conn, "Empathy", "empathy[tiab]")
        db.upsert_article(conn, topic_id, XSS_ARTICLE)
        db.set_scoring(conn, "99999999", 8.0, "A clean AI-written summary.", "fMRI", "ai")

        html_out = render_report(conn)

        assert "A clean AI-written summary." in html_out
        assert "fMRI" in html_out


class TestWriteReport:
    def test_write_report_creates_readable_html_file(self, conn, tmp_path):
        db.add_topic(conn, "Empathy", "empathy[tiab]")
        output_path = tmp_path / "out.html"

        write_report(conn, str(output_path))

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "PubMed Research Radar" in content
