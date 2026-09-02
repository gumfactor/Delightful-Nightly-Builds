from src.models import Author, Reference
from src.styles import chicago


def test_chicago_journal_article_worked_example():
    ref = Reference(
        ref_type="journal-article",
        authors=[Author("Smith", "Jane"), Author("Jones", "Alice")],
        year="2020",
        title="the effects of sleep on memory: a randomized trial",
        container_title="journal of cognitive science",
        volume="12",
        issue="3",
        pages="45-60",
        doi="10.1000/xyz123",
    )
    expected = (
        'Smith, Jane, and Alice Jones. 2020. "The Effects of Sleep on Memory: '
        'A Randomized Trial." *Journal of Cognitive Science* 12, no. 3: 45–60. '
        "https://doi.org/10.1000/xyz123"
    )
    assert chicago.format_reference(ref) == expected


def test_chicago_book_worked_example():
    ref = Reference(
        ref_type="book",
        authors=[Author("Kahneman", "Daniel")],
        year="2011",
        title="thinking, fast and slow",
        container_title="Farrar, Straus and Giroux",
    )
    assert chicago.format_reference(ref) == (
        "Kahneman, Daniel. 2011. *Thinking, Fast and Slow*. Farrar, Straus and Giroux."
    )


def test_chicago_webpage_wraps_title_in_quotes():
    ref = Reference(
        ref_type="webpage",
        authors=[Author("Smith", "Jane")],
        year="2023",
        title="how sleep affects memory formation",
        container_title="Sleep Foundation",
        url="https://example.org/sleep-memory",
    )
    result = chicago.format_reference(ref)
    assert '"How Sleep Affects Memory Formation."' in result
    assert "*Sleep Foundation*" in result


def test_chicago_et_al_threshold_eleven_authors():
    authors = [Author(family=f"Family{i}", given=f"G{i}") for i in range(11)]
    ref = Reference(ref_type="journal-article", authors=authors, year="2020", title="x", container_title="J")
    result = chicago.format_reference(ref)
    assert result.startswith("Family0, G0, ")
    assert "et al." in result


def test_chicago_in_text_one_author():
    ref = Reference(ref_type="journal-article", authors=[Author("Smith", "Jane")], year="2020", title="x")
    assert chicago.format_in_text(ref, 1) == "(Smith 2020)"


def test_chicago_in_text_two_authors():
    ref = Reference(
        ref_type="journal-article",
        authors=[Author("Smith", "Jane"), Author("Jones", "Alice")],
        year="2020",
        title="x",
    )
    assert chicago.format_in_text(ref, 1) == "(Smith and Jones 2020)"


def test_chicago_in_text_four_plus_authors_uses_et_al():
    authors = [Author(family=f"Family{i}", given=f"G{i}") for i in range(4)]
    ref = Reference(ref_type="journal-article", authors=authors, year="2020", title="x")
    assert chicago.format_in_text(ref, 1) == "(Family0 et al. 2020)"
