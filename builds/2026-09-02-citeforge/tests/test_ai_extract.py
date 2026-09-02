import json

from src.ai_extract import ai_extract_reference, extract_reference, regex_extract


def test_regex_extract_finds_year_and_quoted_title():
    ref = regex_extract('Smith, J. (2020). "The effects of sleep on memory." Journal X.')
    assert ref.year == "2020"
    assert ref.title == "The effects of sleep on memory."
    assert not ref.needs_review


def test_regex_extract_finds_doi():
    ref = regex_extract('Smith J. (2020). "A study." 10.1000/xyz123')
    assert ref.doi == "10.1000/xyz123"


def test_regex_extract_parses_author_prefix():
    # "Last First and Last First" (no internal commas) is unambiguous for the
    # deterministic splitter, which treats the leading token as the family
    # name; a comma-separated "Last, First" multi-author prefix is genuinely
    # ambiguous (comma both joins authors and separates family/given) and is
    # exactly the case the optional AI fallback exists for.
    ref = regex_extract('Smith Jane and Jones Alice (2020). "A study."')
    assert len(ref.authors) == 2
    assert ref.authors[0].family == "Smith"
    assert ref.authors[1].family == "Jones"


def test_regex_extract_no_year_or_title_flagged_needs_review():
    ref = regex_extract("just some unstructured text with no clear fields")
    assert ref.needs_review


def test_regex_extract_empty_line_returns_none():
    assert regex_extract("") is None
    assert regex_extract("   ") is None


def test_regex_extract_no_authors_flagged_needs_review_even_with_year_and_title():
    ref = regex_extract('(2020) "A study with no author prefix."')
    assert ref.year == "2020"
    assert ref.title == "A study with no author prefix."
    assert ref.needs_review  # no authors parsed


def _fake_ai_transport(response_text: str, calls: list):
    def transport(url: str, payload: dict) -> bytes:
        calls.append((url, payload))
        return json.dumps({"content": [{"text": response_text}]}).encode("utf-8")

    return transport


def test_ai_extract_reference_parses_structured_response():
    calls = []
    response = json.dumps(
        {
            "family_names": ["Smith"],
            "given_names": ["Jane"],
            "year": "2020",
            "title": "A messy reference finally structured",
            "container_title": "Journal X",
            "volume": "1",
            "issue": "",
            "pages": "",
            "doi": "",
        }
    )
    ref = ai_extract_reference("some messy line", "fake-key", transport=_fake_ai_transport(response, calls))
    assert ref is not None
    assert ref.title == "A messy reference finally structured"
    assert ref.authors[0].family == "Smith"
    assert ref.source == "ai-extract"
    assert len(calls) == 1


def test_ai_extract_reference_no_api_key_makes_no_call():
    calls = []

    def transport(url, payload):
        calls.append(1)
        raise AssertionError("should never be called with no api key")

    result = ai_extract_reference("some line", "", transport=transport)
    assert result is None
    assert calls == []


def test_ai_extract_reference_malformed_response_returns_none():
    calls = []
    transport = _fake_ai_transport("not valid json", calls)
    result = ai_extract_reference("some line", "fake-key", transport=transport)
    assert result is None


def test_ai_extract_reference_missing_title_returns_none():
    calls = []
    response = json.dumps({"family_names": ["Smith"], "given_names": ["Jane"], "title": ""})
    result = ai_extract_reference("some line", "fake-key", transport=_fake_ai_transport(response, calls))
    assert result is None


def test_extract_reference_uses_regex_result_without_ai_when_confident():
    calls = []

    def transport(url, payload):
        calls.append(1)
        raise AssertionError("AI should not be called when regex is confident")

    ref = extract_reference(
        'Smith, J. (2020). "A well formed reference."', use_ai=True, api_key="fake-key", ai_transport=transport
    )
    assert ref.source == "text-regex"
    assert calls == []


def test_extract_reference_falls_back_to_ai_when_regex_not_confident_and_ai_enabled():
    calls = []
    response = json.dumps(
        {"family_names": ["Doe"], "given_names": ["Jane"], "year": "2021", "title": "Recovered by AI"}
    )
    ref = extract_reference(
        "a messy unstructured line with no clear year or title",
        use_ai=True,
        api_key="fake-key",
        ai_transport=_fake_ai_transport(response, calls),
    )
    assert ref.source == "ai-extract"
    assert len(calls) == 1


def test_extract_reference_no_ai_flag_never_calls_transport():
    calls = []

    def transport(url, payload):
        calls.append(1)
        raise AssertionError("should not be called when use_ai=False")

    ref = extract_reference("a messy unstructured line", use_ai=False, api_key="fake-key", ai_transport=transport)
    assert ref.needs_review
    assert calls == []


def test_extract_reference_completely_unparsable_flags_needs_review():
    ref = extract_reference("", use_ai=False, api_key="", ai_transport=lambda u, p: b"")
    assert ref.needs_review
    assert ref.source in ("text-unparsed", "text-regex")
