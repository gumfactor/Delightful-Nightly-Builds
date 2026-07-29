import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import bibtex


def test_escape_special_characters():
    assert bibtex.escape_bibtex("A & B") == r"A \& B"
    assert bibtex.escape_bibtex("100% sure") == r"100\% sure"
    assert bibtex.escape_bibtex("under_score") == r"under\_score"
    assert bibtex.escape_bibtex("") == ""


def test_generate_keys_no_collision():
    papers = [
        {"id": 1, "authors": ["Jane Doe"], "year": 2020},
        {"id": 2, "authors": ["John Smith"], "year": 2021},
    ]
    keys = bibtex.generate_keys(papers)
    assert keys[1] == "doe2020"
    assert keys[2] == "smith2021"


def test_generate_keys_collision_disambiguated():
    papers = [
        {"id": 1, "authors": ["Jane Doe"], "year": 2020},
        {"id": 2, "authors": ["Amy Doe"], "year": 2020},
        {"id": 3, "authors": ["Zed Doe"], "year": 2020},
    ]
    keys = bibtex.generate_keys(papers)
    assert keys[1] == "doe2020"
    assert keys[2] == "doe2020a"
    assert keys[3] == "doe2020b"


def test_generate_keys_no_authors_uses_anon():
    papers = [{"id": 1, "authors": [], "year": 2020}]
    keys = bibtex.generate_keys(papers)
    assert keys[1] == "anon2020"


def test_generate_keys_no_year_uses_nd():
    papers = [{"id": 1, "authors": ["Jane Doe"], "year": None}]
    keys = bibtex.generate_keys(papers)
    assert keys[1] == "doend"


def test_paper_to_entry_contains_required_fields():
    paper = {
        "title": "A Study of Stress",
        "authors": ["Jane Doe", "John Smith"],
        "year": 2020,
        "journal": "Journal of Psychology",
        "doi": "10.1/abc",
    }
    entry = bibtex.paper_to_entry(paper, "doe2020")
    assert "@article{doe2020," in entry
    assert "title = {A Study of Stress}" in entry
    assert "author = {Jane Doe and John Smith}" in entry
    assert "year = {2020}" in entry
    assert "journal = {Journal of Psychology}" in entry
    assert "doi = {10.1/abc}" in entry


def test_paper_to_entry_escapes_title():
    paper = {"title": "Stress & Cortisol", "authors": [], "year": 2020}
    entry = bibtex.paper_to_entry(paper, "key2020")
    assert r"Stress \& Cortisol" in entry


def test_generate_bibtex_empty_list():
    assert bibtex.generate_bibtex([]) == ""


def test_generate_bibtex_multiple_entries_separated():
    papers = [
        {"id": 1, "title": "Paper One", "authors": ["Jane Doe"], "year": 2020},
        {"id": 2, "title": "Paper Two", "authors": ["John Smith"], "year": 2021},
    ]
    output = bibtex.generate_bibtex(papers)
    assert output.count("@article{") == 2
    assert "Paper One" in output
    assert "Paper Two" in output
