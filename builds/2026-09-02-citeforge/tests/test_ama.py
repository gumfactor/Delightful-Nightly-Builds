from src.models import Author, Reference
from src.styles import ama


def test_ama_journal_article_worked_example():
    ref = Reference(
        ref_type="journal-article",
        authors=[Author("Smith", "Jane Marie"), Author("Jones", "Alice B")],
        year="2020",
        title="the effects of sleep on memory: a randomized trial",
        container_title="Journal of Cognitive Science",
        volume="12",
        issue="3",
        pages="45-60",
        doi="10.1000/xyz123",
    )
    expected = (
        "Smith JM, Jones AB. The effects of sleep on memory: A randomized trial. "
        "Journal of Cognitive Science. 2020;12(3):45-60. doi:10.1000/xyz123"
    )
    assert ama.format_reference(ref) == expected


def test_ama_book_worked_example():
    ref = Reference(
        ref_type="book",
        authors=[Author("Kahneman", "Daniel")],
        year="2011",
        title="thinking, fast and slow",
        container_title="Farrar, Straus and Giroux",
    )
    assert ama.format_reference(ref) == "Kahneman D. Thinking, fast and slow. Farrar, Straus and Giroux; 2011."


def test_ama_webpage_worked_example():
    ref = Reference(
        ref_type="webpage",
        authors=[Author("Smith", "Jane")],
        year="2023",
        title="how sleep affects memory formation",
        container_title="Sleep Foundation",
        url="https://example.org/sleep-memory",
    )
    assert ama.format_reference(ref) == (
        "Smith J. How sleep affects memory formation. Sleep Foundation. 2023. "
        "https://example.org/sleep-memory"
    )


def test_ama_et_al_threshold_seven_authors():
    authors = [Author(family=f"Family{i}", given=f"G{i}") for i in range(7)]
    ref = Reference(ref_type="journal-article", authors=authors, year="2020", title="x", container_title="J")
    result = ama.format_reference(ref)
    assert "et al." in result
    assert "Family3" not in result  # only first 3 authors listed


def test_ama_applies_icmje_page_truncation():
    ref = Reference(
        ref_type="journal-article",
        authors=[Author("Halpern", "Steven D")],
        year="2002",
        title="a study",
        container_title="J",
        volume="347",
        pages="284-287",
    )
    assert ":284-7" in ama.format_reference(ref)


def test_ama_in_text_is_numbered():
    ref = Reference(ref_type="journal-article", authors=[Author("Smith", "Jane")], year="2020", title="x")
    assert ama.format_in_text(ref, 5) == "[5]"
