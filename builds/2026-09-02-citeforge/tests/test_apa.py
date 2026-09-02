from src.models import Author, Reference
from src.styles import apa


def test_apa_journal_article_worked_example():
    ref = Reference(
        ref_type="journal-article",
        authors=[Author("Smith", "Jane Marie"), Author("Jones", "Alice B")],
        year="2020",
        title="the effects of sleep on memory: a randomized trial",
        container_title="journal of cognitive science",
        volume="12",
        issue="3",
        pages="45-60",
        doi="10.1000/xyz123",
    )
    expected = (
        "Smith, J. M., & Jones, A. B. (2020). The effects of sleep on memory: "
        "A randomized trial. *Journal of Cognitive Science*, *12*(3), 45–60. "
        "https://doi.org/10.1000/xyz123"
    )
    assert apa.format_reference(ref) == expected


def test_apa_book_worked_example():
    ref = Reference(
        ref_type="book",
        authors=[Author("Kahneman", "Daniel")],
        year="2011",
        title="thinking, fast and slow",
        container_title="Farrar, Straus and Giroux",
    )
    assert apa.format_reference(ref) == (
        "Kahneman, D. (2011). *Thinking, fast and slow*. Farrar, Straus and Giroux."
    )


def test_apa_webpage_worked_example():
    ref = Reference(
        ref_type="webpage",
        authors=[Author("Smith", "Jane")],
        year="2023",
        title="how sleep affects memory formation",
        container_title="Sleep Foundation",
        url="https://example.org/sleep-memory",
    )
    assert apa.format_reference(ref) == (
        "Smith, J. (2023). How sleep affects memory formation. "
        "*Sleep Foundation*. https://example.org/sleep-memory"
    )


def test_apa_no_doi_no_url_omits_link():
    ref = Reference(ref_type="book", authors=[Author("Doe", "Jane")], year="2020", title="a study")
    result = apa.format_reference(ref)
    assert "http" not in result
    assert result == "Doe, J. (2020). *A study*."


def test_apa_missing_year_uses_nd():
    ref = Reference(ref_type="book", authors=[Author("Doe", "Jane")], year="", title="a study")
    assert "(n.d.)" in apa.format_reference(ref)


def test_apa_in_text_one_author():
    ref = Reference(ref_type="journal-article", authors=[Author("Smith", "Jane")], year="2020", title="x")
    assert apa.format_in_text(ref, 1) == "(Smith, 2020)"


def test_apa_in_text_two_authors():
    ref = Reference(
        ref_type="journal-article",
        authors=[Author("Smith", "Jane"), Author("Jones", "Alice")],
        year="2020",
        title="x",
    )
    assert apa.format_in_text(ref, 1) == "(Smith & Jones, 2020)"


def test_apa_in_text_three_plus_authors_uses_et_al():
    ref = Reference(
        ref_type="journal-article",
        authors=[Author("Smith", "Jane"), Author("Jones", "Alice"), Author("Lee", "Kim")],
        year="2020",
        title="x",
    )
    assert apa.format_in_text(ref, 1) == "(Smith et al., 2020)"
