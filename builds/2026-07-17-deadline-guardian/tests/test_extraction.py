from datetime import date

import pytest

from src import ai_client, extraction


def test_fallback_extract_iso_date():
    fields = extraction.fallback_extract("IRB renewal is due 2027-03-15 for the empathy study.")
    assert fields["due_date"] == date(2027, 3, 15)


def test_fallback_extract_slash_date():
    fields = extraction.fallback_extract("Grant progress report due 3/15/2027.")
    assert fields["due_date"] == date(2027, 3, 15)


def test_fallback_extract_month_day_year():
    fields = extraction.fallback_extract("Please submit your abstract by March 15, 2027.")
    assert fields["due_date"] == date(2027, 3, 15)


def test_fallback_extract_day_month_year():
    fields = extraction.fallback_extract("Submission deadline: 15 March 2027.")
    assert fields["due_date"] == date(2027, 3, 15)


def test_fallback_extract_category_irb():
    fields = extraction.fallback_extract("Your IRB protocol renewal is due 2027-03-15.")
    assert fields["category"] == "IRB/Ethics"


def test_fallback_extract_category_grant():
    fields = extraction.fallback_extract("NIH grant progress report due 2027-03-15.")
    assert fields["category"] == "Grant"


def test_fallback_extract_category_conference():
    fields = extraction.fallback_extract("Conference abstract deadline is 2027-03-15.")
    assert fields["category"] == "Conference"


def test_fallback_extract_category_default_other():
    fields = extraction.fallback_extract("Please take care of this by 2027-03-15.")
    assert fields["category"] == "Other"


def test_fallback_extract_recurrence_annual():
    fields = extraction.fallback_extract("This annual ethics renewal is due 2027-03-15.")
    assert fields["recurrence"] == "annual"


def test_fallback_extract_recurrence_every_n_months():
    fields = extraction.fallback_extract("Report due every 4 months, first one 2027-03-15.")
    assert fields["recurrence"] == "every_N_months"
    assert fields["recurrence_months"] == 4


def test_fallback_extract_no_date_raises():
    with pytest.raises(extraction.NoDateFoundError):
        extraction.fallback_extract("There is no date anywhere in this message at all.")


def test_fallback_extract_empty_text_raises():
    with pytest.raises(extraction.NoDateFoundError):
        extraction.fallback_extract("   ")


def test_fallback_extract_title_truncated():
    long_line = "A" * 200 + "\ndue 2027-03-15"
    fields = extraction.fallback_extract(long_line)
    assert len(fields["title"]) <= extraction.MAX_TITLE_LENGTH
    assert fields["title"].endswith("…")


def test_extract_deadline_no_api_key_uses_fallback():
    fields, method = extraction.extract_deadline("IRB renewal due 2027-03-15.", api_key=None)
    assert method == "fallback"
    assert fields["due_date"] == date(2027, 3, 15)


def test_extract_deadline_with_api_key_uses_ai(monkeypatch):
    canned_reply = (
        '{"title": "IRB Renewal", "category": "IRB/Ethics", "due_date": "2027-03-15", '
        '"recurrence": "annual", "recurrence_months": null, "notes": "Renew via the portal."}'
    )
    monkeypatch.setattr(ai_client, "call_claude", lambda prompt, api_key, **kw: canned_reply)
    fields, method = extraction.extract_deadline("some email text", api_key="fake-key")
    assert method == "ai"
    assert fields["due_date"] == date(2027, 3, 15)
    assert fields["category"] == "IRB/Ethics"
    assert fields["recurrence"] == "annual"


def test_extract_deadline_ai_failure_falls_back(monkeypatch):
    def raise_error(prompt, api_key, **kw):
        raise ai_client.AnthropicAPIError("simulated network failure")

    monkeypatch.setattr(ai_client, "call_claude", raise_error)
    fields, method = extraction.extract_deadline("IRB renewal due 2027-03-15.", api_key="fake-key")
    assert method == "fallback"
    assert fields["due_date"] == date(2027, 3, 15)


def test_ai_extract_invalid_category_defaults_to_other(monkeypatch):
    canned_reply = (
        '{"title": "Something", "category": "Not A Real Category", "due_date": "2027-03-15", '
        '"recurrence": "none", "recurrence_months": null, "notes": null}'
    )
    monkeypatch.setattr(ai_client, "call_claude", lambda prompt, api_key, **kw: canned_reply)
    fields = extraction.ai_extract("text", api_key="fake-key")
    assert fields["category"] == "Other"


def test_ai_extract_no_date_raises(monkeypatch):
    canned_reply = (
        '{"title": "Something", "category": "Other", "due_date": null, '
        '"recurrence": "none", "recurrence_months": null, "notes": null}'
    )
    monkeypatch.setattr(ai_client, "call_claude", lambda prompt, api_key, **kw: canned_reply)
    with pytest.raises(extraction.NoDateFoundError):
        extraction.ai_extract("text", api_key="fake-key")


def test_ai_extract_strips_markdown_code_fence(monkeypatch):
    canned_reply = (
        "```json\n"
        '{"title": "Fenced", "category": "Other", "due_date": "2027-03-15", '
        '"recurrence": "none", "recurrence_months": null, "notes": null}\n'
        "```"
    )
    monkeypatch.setattr(ai_client, "call_claude", lambda prompt, api_key, **kw: canned_reply)
    fields = extraction.ai_extract("text", api_key="fake-key")
    assert fields["due_date"] == date(2027, 3, 15)
