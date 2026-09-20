from src.parser import Comment
from src.report import render_html, render_markdown, render_plaintext
from src.response_matcher import match


def build_sample():
    comments = [
        Comment(1, 1, "Clarify construct X."),
        Comment(1, 2, "Add a power analysis."),
        Comment(2, 1, "Fix Figure 3 labels."),
    ]
    polished = {
        "R1C1": "We clarified construct X in Section 2.1.",
        "R2C1": "Figure 3 has been redrawn.",
    }
    report = match(comments, {"R1C1": "x", "R2C1": "y"})
    return comments, polished, report


def test_markdown_includes_all_comments_and_responses():
    comments, polished, report = build_sample()
    markdown = render_markdown(comments, polished, report)
    assert "Reviewer 1" in markdown
    assert "Reviewer 2" in markdown
    assert "Clarify construct X." in markdown
    assert "We clarified construct X in Section 2.1." in markdown
    assert "Fix Figure 3 labels." in markdown


def test_markdown_flags_missing_comment():
    comments, polished, report = build_sample()
    markdown = render_markdown(comments, polished, report)
    assert "MISSING" in markdown
    assert "Add a power analysis." in markdown


def test_markdown_includes_completeness_summary():
    comments, polished, report = build_sample()
    markdown = render_markdown(comments, polished, report)
    assert "2/3 comments addressed" in markdown


def test_plaintext_has_no_markdown_artifacts():
    comments, polished, report = build_sample()
    text = render_plaintext(comments, polished, report)
    assert "**" not in text
    assert ">" not in text
    assert "Reviewer 1" in text
    assert "We clarified construct X in Section 2.1." in text


def test_html_escapes_script_tag_in_comment_text():
    comments = [Comment(1, 1, "<script>alert('xss')</script>")]
    polished = {"R1C1": "Handled safely."}
    report = match(comments, {"R1C1": "x"})
    html = render_html(comments, polished, report)
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


def test_html_escapes_script_tag_in_response_text():
    comments = [Comment(1, 1, "A normal comment.")]
    polished = {"R1C1": "<img src=x onerror=alert(1)>"}
    report = match(comments, {"R1C1": "x"})
    html = render_html(comments, polished, report)
    assert "<img src=x" not in html
    assert "&lt;img" in html


def test_html_flags_missing_comment_visually():
    comments, polished, report = build_sample()
    html = render_html(comments, polished, report)
    assert 'class="comment-block missing"' in html
    assert "MISSING" in html


def test_html_includes_completeness_dashboard():
    comments, polished, report = build_sample()
    html = render_html(comments, polished, report)
    assert "67%" in html  # round(2/3*100)
