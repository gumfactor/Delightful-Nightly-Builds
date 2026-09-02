from src.pages import format_pages_ama_vancouver, format_pages_full, icmje_truncate, parse_page_range


def test_parse_page_range_hyphen():
    assert parse_page_range("284-287") == ("284", "287")


def test_parse_page_range_en_dash():
    assert parse_page_range("284–287") == ("284", "287")


def test_parse_page_range_single_page():
    assert parse_page_range("284") == ("284", "")


def test_parse_page_range_empty():
    assert parse_page_range("") == ("", "")


def test_icmje_truncate_real_published_example():
    # Halpern SD, Ubel PA, Caplan AL. N Engl J Med. 2002;347:284-7.
    assert icmje_truncate("284", "287") == "284-7"


def test_icmje_truncate_more_examples_from_the_icmje_recommendations():
    assert icmje_truncate("1225", "1231") == "1225-31"
    assert icmje_truncate("101", "106") == "101-6"
    assert icmje_truncate("3242", "3249") == "3242-9"


def test_icmje_truncate_no_shared_leading_digit_stays_full():
    assert icmje_truncate("195", "201") == "195-201"


def test_icmje_truncate_single_page_no_end():
    assert icmje_truncate("284", "") == "284"


def test_icmje_truncate_identical_start_and_end():
    assert icmje_truncate("284", "284") == "284"


def test_icmje_truncate_non_numeric_pages_untouched():
    assert icmje_truncate("e123", "e130") == "e123-e130"


def test_icmje_truncate_end_shorter_than_start_untouched():
    assert icmje_truncate("1200", "5") == "1200-5"


def test_format_pages_ama_vancouver_applies_truncation():
    assert format_pages_ama_vancouver("284-287") == "284-7"


def test_format_pages_ama_vancouver_single_page():
    assert format_pages_ama_vancouver("284") == "284"


def test_format_pages_ama_vancouver_empty():
    assert format_pages_ama_vancouver("") == ""


def test_format_pages_full_uses_en_dash_no_truncation():
    assert format_pages_full("45-60") == "45–60"


def test_format_pages_full_single_page():
    assert format_pages_full("45") == "45"


def test_format_pages_full_empty():
    assert format_pages_full("") == ""
