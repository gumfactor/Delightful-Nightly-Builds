from src.parser import parse_document


def test_extract_headings_basic():
    doc = parse_document("## Goal\n\nDo the thing.\n")
    assert len(doc.headings) == 1
    assert doc.headings[0].text == "Goal"
    assert doc.headings[0].level == 2
    assert doc.headings[0].slug == "goal"


def test_slugify_heading_handles_duplicates():
    doc = parse_document("## Testing\n\ntext\n\n## Testing\n\nmore text\n")
    slugs = [h.slug for h in doc.headings]
    assert slugs == ["testing", "testing-1"]


def test_extract_file_references_from_backticks():
    doc = parse_document("Config lives in `data.json`.\n")
    paths = [ref.text for ref in doc.code_spans]
    assert "data.json" in paths


def test_extract_file_references_ignores_non_path_code_spans():
    doc = parse_document("Run `git status` then call `foo()`.\n")
    paths = [ref.text for ref in doc.code_spans]
    assert paths == []


def test_extract_markdown_links_separates_internal_external():
    content = (
        "[a](#anchor) and [b](rel/path.md) and [c](https://example.com)\n"
    )
    doc = parse_document(content)
    kinds = {link.target: link.kind for link in doc.links}
    assert kinds["#anchor"] == "anchor"
    assert kinds["rel/path.md"] == "relative"
    assert kinds["https://example.com"] == "external"


def test_heading_line_numbers_are_one_indexed():
    doc = parse_document("intro line\n\n## First Heading\n")
    assert doc.headings[0].line == 3
