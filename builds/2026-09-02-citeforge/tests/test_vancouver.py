from src.models import Author, Reference
from src.styles import vancouver


def test_vancouver_matches_real_published_icmje_sample_citation():
    # Official ICMJE sample reference:
    # "Halpern SD, Ubel PA, Caplan AL. Solid-organ transplantation in
    #  HIV-infected patients. N Engl J Med. 2002;347:284-7."
    ref = Reference(
        ref_type="journal-article",
        authors=[
            Author("Halpern", "Steven D"),
            Author("Ubel", "Peter A"),
            Author("Caplan", "Arthur L"),
        ],
        year="2002",
        title="Solid-organ transplantation in HIV-infected patients",
        container_title="N Engl J Med",
        volume="347",
        pages="284-287",
    )
    expected = (
        "Halpern SD, Ubel PA, Caplan AL. Solid-organ transplantation in "
        "HIV-infected patients. N Engl J Med. 2002;347:284-7."
    )
    assert vancouver.format_reference(ref) == expected


def test_vancouver_et_al_threshold_seven_authors():
    authors = [Author(family=f"Family{i}", given=f"G{i}") for i in range(7)]
    ref = Reference(ref_type="journal-article", authors=authors, year="2020", title="x", container_title="J")
    result = vancouver.format_reference(ref)
    assert result.startswith(
        "Family0 G, Family1 G, Family2 G, Family3 G, Family4 G, Family5 G, et al."
    )
    assert "Family5" in result  # sixth author (index 5) still listed
    assert "Family6" not in result  # seventh author is not


def test_vancouver_six_authors_lists_all_no_et_al():
    authors = [Author(family=f"Family{i}", given=f"G{i}") for i in range(6)]
    ref = Reference(ref_type="journal-article", authors=authors, year="2020", title="x", container_title="J")
    result = vancouver.format_reference(ref)
    assert "et al." not in result
    assert "Family5" in result


def test_vancouver_in_text_is_numbered():
    ref = Reference(ref_type="journal-article", authors=[Author("Smith", "Jane")], year="2020", title="x")
    assert vancouver.format_in_text(ref, 12) == "[12]"


def test_vancouver_book_worked_example():
    ref = Reference(
        ref_type="book",
        authors=[Author("Kahneman", "Daniel")],
        year="2011",
        title="thinking, fast and slow",
        container_title="Farrar, Straus and Giroux",
    )
    assert vancouver.format_reference(ref) == (
        "Kahneman D. Thinking, fast and slow. Farrar, Straus and Giroux; 2011."
    )
