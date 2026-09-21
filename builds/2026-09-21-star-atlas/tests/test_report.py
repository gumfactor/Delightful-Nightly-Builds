import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import report  # noqa: E402


def make_repo(id_, full_name, description="A repo.", tag="Other", topics=None):
    return {
        "id": id_,
        "full_name": full_name,
        "description": description,
        "html_url": f"https://github.com/{full_name}",
        "language": "Python",
        "topics": topics or [],
        "stargazers_count": 5,
        "starred_at": "2026-09-01T00:00:00Z",
        "tag": tag,
        "note": description or "",
        "source": "rule",
    }


def make_stats(repos):
    return {
        "total": len(repos),
        "by_tag": {},
        "by_language": {},
        "latest_starred_at": "2026-09-01T00:00:00Z",
    }


def test_render_html_includes_repo_data():
    repos = [make_repo(1, "acme/toolkit")]
    html = report.render_html(repos, make_stats(repos))
    assert "acme/toolkit" in html
    assert "<!DOCTYPE html>" in html


def test_render_html_escapes_hostile_description():
    hostile = "</script><script>window.__xss=true;</script>"
    repos = [make_repo(1, "hostile/repo", description=hostile)]
    html = report.render_html(repos, make_stats(repos))
    assert "</script><script>window.__xss=true;</script>" not in html


def test_render_html_embeds_valid_json():
    repos = [make_repo(1, "acme/toolkit", topics=["llm"])]
    html = report.render_html(repos, make_stats(repos))
    start = html.index('id="star-atlas-data">') + len('id="star-atlas-data">')
    end = html.index("</script>", start)
    embedded = html[start:end]
    parsed = json.loads(embedded)
    assert parsed["repos"][0]["full_name"] == "acme/toolkit"
    assert parsed["repos"][0]["topics"] == ["llm"]


def test_render_html_never_uses_innerHTML():
    repos = [make_repo(1, "acme/toolkit")]
    html = report.render_html(repos, make_stats(repos))
    assert "innerHTML" not in html


def test_render_html_handles_empty_repo_list():
    html = report.render_html([], make_stats([]))
    assert '"repos": []' in html or '"repos":[]' in html
    assert "<!DOCTYPE html>" in html


def test_render_html_escapes_html_comment_markers():
    repos = [make_repo(1, "a/b", description="<!-- comment injection -->")]
    html = report.render_html(repos, make_stats(repos))
    start = html.index('id="star-atlas-data">') + len('id="star-atlas-data">')
    end = html.index("</script>", start)
    embedded = html[start:end]
    assert "<!--" not in embedded
