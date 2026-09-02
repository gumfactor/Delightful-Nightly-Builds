from src.models import Author
from src.names import (
    format_authors_ama,
    format_authors_apa,
    format_authors_chicago,
    format_authors_vancouver,
    get_initials,
    get_initials_compact,
)


def _authors(n):
    return [Author(family=f"Family{i}", given=f"Given{i}") for i in range(n)]


def test_get_initials_two_names():
    assert get_initials("Jane Marie") == "J. M."


def test_get_initials_already_initial():
    assert get_initials("J.") == "J."


def test_get_initials_hyphenated_name():
    assert get_initials("Jean-Paul") == "J.-P."


def test_get_initials_empty():
    assert get_initials("") == ""


def test_get_initials_compact():
    assert get_initials_compact("Jane Marie") == "JM"


def test_get_initials_compact_hyphenated():
    assert get_initials_compact("Jean-Paul") == "JP"


def test_format_authors_apa_one_author():
    result = format_authors_apa([Author(family="Smith", given="Jane Marie")])
    assert result == "Smith, J. M."


def test_format_authors_apa_two_authors_uses_ampersand():
    result = format_authors_apa([Author(family="Smith", given="Jane"), Author(family="Jones", given="Alice")])
    assert result == "Smith, J., & Jones, A."


def test_format_authors_apa_twenty_authors_lists_all():
    result = format_authors_apa(_authors(20))
    assert result.count(",") >= 19
    assert result.endswith("Family19, G.")
    assert "..." not in result


def test_format_authors_apa_twenty_one_authors_uses_ellipsis():
    result = format_authors_apa(_authors(21))
    assert ", ... " in result
    assert result.endswith("Family20, G.")


def test_format_authors_ama_six_authors_lists_all_no_et_al():
    result = format_authors_ama(_authors(6))
    assert "et al." not in result
    assert result.count(",") == 5


def test_format_authors_ama_seven_authors_uses_et_al_after_three():
    # get_initials_compact takes the first letter of each whitespace/hyphen-
    # separated token in the given name; "GivenN" has no separator, so the
    # compact initial for every author here is just "G".
    result = format_authors_ama(_authors(7))
    assert result == "Family0 G, Family1 G, Family2 G, et al."


def test_format_authors_vancouver_six_authors_lists_all():
    result = format_authors_vancouver(_authors(6))
    assert "et al." not in result


def test_format_authors_vancouver_seven_authors_uses_et_al_after_six():
    result = format_authors_vancouver(_authors(7))
    parts = result.split(", ")
    assert parts[-1] == "et al."
    assert len(parts) == 7  # 6 names + "et al."


def test_format_authors_chicago_worked_example_two_authors():
    authors = [Author(family="Smith", given="Jane"), Author(family="Jones", given="Alice")]
    assert format_authors_chicago(authors) == "Smith, Jane, and Alice Jones"


def test_format_authors_chicago_ten_authors_lists_all():
    result = format_authors_chicago(_authors(10))
    assert "et al." not in result
    assert result.startswith("Family0, Given0, ")
    assert result.endswith("and Given9 Family9")


def test_format_authors_chicago_eleven_authors_uses_et_al_after_seven():
    result = format_authors_chicago(_authors(11))
    assert result.endswith("et al.")
    # 7 authors listed: 1 comma inside the inverted first name, 6 join
    # commas between the 7 parts, 1 more before "et al." = 8 total.
    assert result.count(",") == 8


def test_format_authors_empty_list_all_styles():
    assert format_authors_apa([]) == ""
    assert format_authors_ama([]) == ""
    assert format_authors_vancouver([]) == ""
    assert format_authors_chicago([]) == ""
