import pytest

import body


def test_truncate_short_text_unchanged():
    text = "A short pitch."
    assert body.truncate(text, 160) == text


def test_truncate_long_text_cuts_at_word_boundary():
    text = "word " * 60  # far longer than 30 chars, plenty of word boundaries
    result = body.truncate(text.strip(), 30)
    assert result.endswith("…")
    # Never ends with a partial word directly before the ellipsis
    core = result[:-1].rstrip()
    assert text.strip().startswith(core)


def test_truncate_never_exceeds_max_len():
    text = "Supercalifragilisticexpialidocious " * 5
    result = body.truncate(text.strip(), 20)
    assert len(result) <= 20


def test_truncate_handles_text_with_no_spaces_before_limit():
    # A single long word with no space to cut at — falls back to a hard cut.
    text = "a" * 200
    result = body.truncate(text, 50)
    assert len(result) <= 50
    assert result.endswith("…")


def test_build_card_includes_why_line_for_evidence():
    business = {
        "name": "Northern Bloom Skincare",
        "category": "Skincare",
        "description": "Cold-pressed facial oils.",
        "city": "Halifax",
        "province": "Nova Scotia",
        "verified": True,
        "evidence": "Headquartered in Halifax, Nova Scotia.",
    }
    card = body.build_card(business, "consumer")
    assert "Northern Bloom Skincare" in card
    assert "Why it's Canadian: Headquartered in Halifax, Nova Scotia." in card


def test_build_card_verified_without_evidence():
    business = {
        "name": "Prairie Wool Co",
        "category": "Home Goods",
        "description": "Wool blankets.",
        "city": "",
        "province": "",
        "verified": True,
        "evidence": "",
    }
    card = body.build_card(business, "consumer")
    assert "Verified Canadian-owned." in card


def test_build_card_unverified_shows_disclaimer():
    business = {
        "name": "Harbourfront Woodworks",
        "category": "Home Goods",
        "description": "Cutting boards.",
        "city": "",
        "province": "",
        "verified": False,
        "evidence": "",
    }
    card = body.build_card(business, "consumer")
    assert "Unverified" in card
    assert "confirm Canadian ownership" in card


def test_build_card_missing_description_uses_default_pitch():
    business = {
        "name": "No Description Co",
        "category": "Bakery",
        "description": "",
        "city": "",
        "province": "",
        "verified": True,
        "evidence": "",
    }
    card = body.build_card(business, "consumer")
    assert "A Canadian Bakery business." in card


def test_build_body_spotlight_consumer_contains_intro_and_card():
    businesses = [
        {
            "name": "Birchwood Skin Co",
            "category": "Skincare",
            "description": "Small-batch soap.",
            "city": "Guelph",
            "province": "Ontario",
            "verified": True,
            "evidence": "Independently owned in Guelph.",
        }
    ]
    context = {"name": "Birchwood Skin Co", "category": "Skincare", "count": 1, "province": ""}
    text = body.build_body("spotlight", "consumer", "general", businesses, context)
    assert "You're going to want to remember this one." in text
    assert "Birchwood Skin Co" in text
    assert "Support Canadian." in text


def test_build_body_occasion_changes_cta():
    businesses = [
        {
            "name": "Birchwood Skin Co",
            "category": "Skincare",
            "description": "Small-batch soap.",
            "city": "",
            "province": "",
            "verified": True,
            "evidence": "",
        }
    ]
    context = {"name": "Birchwood Skin Co", "category": "Skincare", "count": 1, "province": ""}
    general_text = body.build_body("spotlight", "consumer", "general", businesses, context)
    canada_day_text = body.build_body("spotlight", "consumer", "canada-day", businesses, context)
    assert general_text != canada_day_text
    assert "put your money where the flag is" in canada_day_text
    assert "put your money where the flag is" not in general_text


def test_build_body_social_tone_appends_hashtags():
    businesses = [
        {
            "name": "Birchwood Skin Co",
            "category": "Skincare",
            "description": "Small-batch soap.",
            "city": "",
            "province": "",
            "verified": True,
            "evidence": "",
        }
    ]
    context = {"name": "Birchwood Skin Co", "category": "Skincare", "count": 1, "province": ""}
    text = body.build_body("spotlight", "social", "general", businesses, context)
    assert "#BuyCanadian" in text


def test_build_body_unknown_intro_combo_raises():
    with pytest.raises(ValueError, match="No intro template"):
        body.build_body("local_spotlight", "social", "general", [], {"province": "Ontario", "count": 2})


def test_build_body_unknown_occasion_raises():
    businesses = [
        {
            "name": "Birchwood Skin Co",
            "category": "Skincare",
            "description": "",
            "city": "",
            "province": "",
            "verified": True,
            "evidence": "",
        }
    ]
    context = {"name": "Birchwood Skin Co", "category": "Skincare", "count": 1, "province": ""}
    with pytest.raises(ValueError, match="Unknown occasion"):
        body.build_body("spotlight", "consumer", "black-friday", businesses, context)
