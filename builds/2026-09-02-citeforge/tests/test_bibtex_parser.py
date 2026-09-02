from src.bibtex_parser import parse_bibtex, parse_bibtex_to_references

SAMPLE_BIB = """
@article{smith2020,
  author = {Smith, Jane Marie and Jones, Alice B.},
  title = {The effects of sleep on memory: a randomized trial},
  journal = {Journal of Cognitive Science},
  year = {2020},
  volume = {12},
  number = {3},
  pages = {45--60},
  doi = {10.1000/xyz123}
}

@book{kahneman2011,
  author = {Kahneman, Daniel},
  title = "Thinking, fast and slow",
  publisher = {Farrar, Straus and Giroux},
  year = {2011}
}

@misc{smith2023,
  author = {Smith, Jane},
  title = {How sleep affects memory formation},
  organization = {Sleep Foundation},
  year = {2023},
  url = {https://example.org/sleep-memory}
}
"""


def test_parse_bibtex_finds_all_entries():
    entries, warnings = parse_bibtex(SAMPLE_BIB)
    assert len(entries) == 3
    assert warnings == []


def test_parse_bibtex_extracts_field_values():
    entries, _ = parse_bibtex(SAMPLE_BIB)
    article = entries[0]
    assert article["type"] == "article"
    assert article["key"] == "smith2020"
    assert article["fields"]["journal"] == "Journal of Cognitive Science"
    assert article["fields"]["volume"] == "12"


def test_parse_bibtex_handles_quoted_field_values():
    entries, _ = parse_bibtex(SAMPLE_BIB)
    book = entries[1]
    assert book["fields"]["title"] == "Thinking, fast and slow"


def test_parse_bibtex_to_references_maps_types_correctly():
    references, warnings = parse_bibtex_to_references(SAMPLE_BIB)
    assert warnings == []
    assert [r.ref_type for r in references] == ["journal-article", "book", "webpage"]


def test_parse_bibtex_to_references_splits_authors():
    references, _ = parse_bibtex_to_references(SAMPLE_BIB)
    article = references[0]
    assert len(article.authors) == 2
    assert article.authors[0].family == "Smith"
    assert article.authors[0].given == "Jane Marie"
    assert article.authors[1].family == "Jones"


def test_parse_bibtex_double_hyphen_pages_normalized():
    references, _ = parse_bibtex_to_references(SAMPLE_BIB)
    assert references[0].pages == "45-60"


def test_parse_bibtex_skips_entry_missing_title():
    text = "@article{noTitle, author = {Doe, Jane}, year = {2020}}"
    references, warnings = parse_bibtex_to_references(text)
    assert references == []
    assert len(warnings) == 1
    assert "missing required 'title'" in warnings[0]


def test_parse_bibtex_malformed_entry_does_not_crash_batch():
    text = SAMPLE_BIB + "\n@article{broken, title = {unbalanced"
    references, warnings = parse_bibtex_to_references(text)
    # the 3 well-formed entries still parse; the broken one is reported
    assert len(references) == 3
    assert any("unbalanced braces" in w for w in warnings)


def test_parse_bibtex_malformed_entry_in_the_middle_does_not_lose_later_entries():
    text = (
        "@article{broken, title = {unbalanced\n\n"
        "@book{kahneman2011, author = {Kahneman, Daniel}, "
        "title = {Thinking, fast and slow}, publisher = {Farrar}, year = {2011}}"
    )
    references, warnings = parse_bibtex_to_references(text)
    assert any("unbalanced braces" in w for w in warnings)
    assert len(references) == 1
    assert references[0].authors[0].family == "Kahneman"


def test_parse_bibtex_unrecognized_type_maps_to_other_with_warning():
    text = '@dataset{ds1, title = {A dataset}, author = {Doe, Jane}, year = {2021}}'
    references, warnings = parse_bibtex_to_references(text)
    assert len(references) == 1
    assert references[0].ref_type == "other"
    assert any("unrecognized type" in w for w in warnings)


def test_parse_bibtex_empty_text_returns_nothing():
    entries, warnings = parse_bibtex("")
    assert entries == []
    assert warnings == []


def test_parse_bibtex_single_author_no_given_name():
    text = '@misc{org1, title = {Report}, author = {UNICEF}, year = {2019}}'
    references, _ = parse_bibtex_to_references(text)
    assert references[0].authors[0].family == "UNICEF"
    assert references[0].authors[0].given == ""
