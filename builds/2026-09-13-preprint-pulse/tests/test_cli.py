"""End-to-end CLI tests with the arXiv network layer mocked out."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

import main as main_module
from arxiv_client import ArxivClientError, Paper


def _fake_papers() -> list[Paper]:
    return [
        Paper(
            arxiv_id="2609.00001v1",
            title="A Study of Empathy Training",
            authors=["A. Author"],
            abstract="N = 40 participants (p = 0.02).",
            published=date(2026, 9, 1),
            categories=["q-bio.NC"],
            pdf_url="http://arxiv.org/pdf/2609.00001v1",
        ),
        Paper(
            arxiv_id="2604.00002v1",
            title="Earlier Related Work",
            authors=["B. Author"],
            abstract="No statistics reported.",
            published=date(2026, 4, 1),
            categories=["q-bio.NC"],
            pdf_url="http://arxiv.org/pdf/2604.00002v1",
        ),
    ]


def test_digest_command_writes_markdown_and_html(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(main_module, "fetch_papers", lambda **kwargs: _fake_papers())
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    exit_code = main_module.main(
        ["digest", "--topic", "Empathy Training", "--out", str(tmp_path), "--months", "6"]
    )
    assert exit_code == 0

    md_path = tmp_path / "empathy-training.md"
    html_path = tmp_path / "empathy-training.html"
    assert md_path.exists()
    assert html_path.exists()

    md_text = md_path.read_text(encoding="utf-8")
    assert "A Study of Empathy Training" in md_text
    assert "## Trend" in md_text

    html_text = html_path.read_text(encoding="utf-8")
    assert "<html" in html_text
    assert "A Study of Empathy Training" in html_text


def test_digest_command_reports_template_source_without_api_key(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(main_module, "fetch_papers", lambda **kwargs: _fake_papers())
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    main_module.main(["digest", "--topic", "empathy", "--out", str(tmp_path), "--ai"])
    out = capsys.readouterr().out
    assert "draft source: template" in out


def test_trend_command_prints_summary_without_writing_files(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(main_module, "fetch_papers", lambda **kwargs: _fake_papers())

    main_module.main(["trend", "--topic", "empathy", "--out", str(tmp_path), "--months", "6"])
    out = capsys.readouterr().out
    assert "Direction:" in out
    assert "Rising keywords:" in out
    assert not list(tmp_path.glob("*.md"))
    assert not list(tmp_path.glob("*.html"))


def test_digest_exits_nonzero_on_arxiv_client_error(tmp_path, monkeypatch, capsys):
    def raise_error(**kwargs):
        raise ArxivClientError("simulated network failure")

    monkeypatch.setattr(main_module, "fetch_papers", raise_error)

    with pytest.raises(SystemExit) as exc_info:
        main_module.main(["digest", "--topic", "empathy", "--out", str(tmp_path)])
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "could not fetch from arXiv" in err


def test_digest_topic_slug_is_path_safe_even_with_hostile_topic(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "fetch_papers", lambda **kwargs: _fake_papers())
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    main_module.main(["digest", "--topic", "../../etc/passwd", "--out", str(tmp_path)])
    produced = list(tmp_path.glob("*.md"))
    assert len(produced) == 1
    assert produced[0].parent == tmp_path  # never escaped the output directory
