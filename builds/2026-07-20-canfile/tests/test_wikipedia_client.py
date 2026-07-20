import urllib.error
from unittest.mock import patch

import wikipedia_client as wp


def test_get_summary_success():
    fake_response = {
        "title": "Tim Hortons",
        "extract": "Tim Hortons is a Canadian multinational fast food restaurant chain.",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Tim_Hortons"}},
    }
    with patch.object(wp, "_api_get", return_value=fake_response):
        summary = wp.get_summary("Tim Hortons")
    assert summary["title"] == "Tim Hortons"
    assert "Canadian" in summary["extract"]
    assert summary["url"] == "https://en.wikipedia.org/wiki/Tim_Hortons"


def test_get_summary_missing_page_returns_none():
    with patch.object(wp, "_api_get", return_value=None):
        summary = wp.get_summary("Totally Fictional Page Xyz")
    assert summary is None


def test_get_summary_builds_fallback_url_when_missing():
    fake_response = {"title": "Some Company", "extract": "A description."}
    with patch.object(wp, "_api_get", return_value=fake_response):
        summary = wp.get_summary("Some Company")
    assert summary["url"] == "https://en.wikipedia.org/wiki/Some_Company"


def test_api_get_returns_none_on_404():
    http_error = urllib.error.HTTPError("url", 404, "Not Found", None, None)
    with patch("urllib.request.urlopen", side_effect=http_error):
        result = wp._api_get("Nonexistent Page")
    assert result is None


def test_api_get_raises_on_other_http_errors():
    http_error = urllib.error.HTTPError("url", 503, "Service Unavailable", None, None)
    with patch("urllib.request.urlopen", side_effect=http_error):
        try:
            wp._api_get("Some Page")
            assert False, "expected WikipediaError"
        except wp.WikipediaError:
            pass
