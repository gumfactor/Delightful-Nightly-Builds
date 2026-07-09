import pipeline_stats as ps
import report_html


def make_status(title="Sample", merged=True, branch=None, backlog_days=None, rating=None):
    return {
        "date": "2026-07-01",
        "category": "A",
        "complexity": "ambitious",
        "title": title,
        "description": "desc",
        "tech": "Python",
        "status": "complete",
        "rating": rating,
        "notes": "",
        "folder": "2026-07-01-sample",
        "merged": merged,
        "branch": branch,
        "backlog_days": backlog_days,
    }


def test_render_escapes_script_tags_in_title():
    statuses = [make_status(title="<script>alert(1)</script>")]
    summary = ps.summarize(statuses)
    html = report_html.render(statuses, summary, "brief text", "owner", "repo", "main")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_render_includes_hero_numbers():
    statuses = [make_status(merged=True), make_status(title="Two", merged=False, branch="origin/b", backlog_days=5)]
    summary = ps.summarize(statuses)
    html = report_html.render(statuses, summary, "brief text", "owner", "repo", "main")
    assert ">2<" in html  # total builds tile
    assert "backlog · 5d" in html


def test_render_needs_attention_empty_state():
    statuses = [make_status(merged=True)]
    summary = ps.summarize(statuses)
    html = report_html.render(statuses, summary, "brief", "owner", "repo", "main")
    assert "Nothing in the backlog" in html


def test_render_compare_link_uses_owner_repo_and_branch():
    statuses = [make_status(title="Stuck", merged=False, branch="origin/claude/xyz", backlog_days=3)]
    summary = ps.summarize(statuses)
    html = report_html.render(statuses, summary, "brief", "acme", "widgets", "main")
    assert "https://github.com/acme/widgets/compare/main...claude/xyz" in html


def test_render_shows_closed_badge_for_discarded_unmerged_build():
    statuses = [make_status(title="Discarded Thing", merged=False, branch=None, backlog_days=30)]
    statuses[0]["status"] = "discarded"
    summary = ps.summarize(statuses)
    html = report_html.render(statuses, summary, "brief", "owner", "repo", "main")
    assert '<span class="badge badge-closed">closed</span>' in html
    assert "backlog · 30d" not in html


def test_render_handles_empty_catalog_without_crashing():
    summary = ps.summarize([])
    html = report_html.render([], summary, "no data", None, None, "main")
    assert "<html" in html
    assert "Nothing in the backlog" in html
