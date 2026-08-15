from src.rules import CANADA_QID, classify, empty_resolution

FOREIGN_QID = "Q30"  # United States, used as a stand-in foreign country in fixtures


def test_empty_resolution_has_all_none_fields():
    resolved = empty_resolution()
    assert resolved == {
        "own_country": None,
        "headquarters_country": None,
        "parent_country": None,
        "owner_country": None,
    }


def test_direct_canadian_country_high_confidence():
    resolved = empty_resolution()
    resolved["own_country"] = CANADA_QID
    verdict, confidence, evidence = classify(resolved)
    assert verdict == "canadian"
    assert confidence >= 0.9
    assert "Canada" in evidence


def test_direct_foreign_country_high_confidence():
    resolved = empty_resolution()
    resolved["own_country"] = FOREIGN_QID
    verdict, confidence, evidence = classify(resolved)
    assert verdict == "foreign"
    assert confidence >= 0.85
    assert FOREIGN_QID in evidence


def test_conflicting_country_and_headquarters_is_uncertain():
    resolved = empty_resolution()
    resolved["own_country"] = CANADA_QID
    resolved["headquarters_country"] = FOREIGN_QID
    verdict, confidence, evidence = classify(resolved)
    assert verdict == "uncertain"
    assert 0 < confidence < 0.9
    assert "conflicting" in evidence.lower()


def test_canadian_country_with_foreign_parent_is_uncertain():
    resolved = empty_resolution()
    resolved["own_country"] = CANADA_QID
    resolved["parent_country"] = FOREIGN_QID
    verdict, confidence, evidence = classify(resolved)
    assert verdict == "uncertain"
    assert "parent" in evidence.lower()


def test_canadian_country_with_foreign_owner_is_uncertain():
    resolved = empty_resolution()
    resolved["own_country"] = CANADA_QID
    resolved["owner_country"] = FOREIGN_QID
    verdict, confidence, evidence = classify(resolved)
    assert verdict == "uncertain"
    assert "owned" in evidence.lower()


def test_headquarters_only_canadian_lower_confidence_than_direct():
    resolved = empty_resolution()
    resolved["headquarters_country"] = CANADA_QID
    verdict, confidence, evidence = classify(resolved)
    assert verdict == "canadian"
    assert confidence < 0.9  # one-hop, so strictly less confident than a direct P17 match

    direct_resolved = empty_resolution()
    direct_resolved["own_country"] = CANADA_QID
    _, direct_confidence, _ = classify(direct_resolved)
    assert confidence < direct_confidence


def test_headquarters_only_foreign():
    resolved = empty_resolution()
    resolved["headquarters_country"] = FOREIGN_QID
    verdict, confidence, evidence = classify(resolved)
    assert verdict == "foreign"
    assert confidence > 0


def test_parent_only_canadian_lowest_tier_confidence():
    resolved = empty_resolution()
    resolved["parent_country"] = CANADA_QID
    verdict, confidence, evidence = classify(resolved)
    assert verdict == "canadian"
    assert 0 < confidence <= 0.6


def test_owner_only_foreign():
    resolved = empty_resolution()
    resolved["owner_country"] = FOREIGN_QID
    verdict, confidence, evidence = classify(resolved)
    assert verdict == "foreign"
    assert confidence > 0


def test_zero_claims_resolved_is_uncertain_with_zero_confidence():
    resolved = empty_resolution()
    verdict, confidence, evidence = classify(resolved)
    assert verdict == "uncertain"
    assert confidence == 0.0
    assert "no country" in evidence.lower()


def test_confidence_is_always_between_zero_and_one():
    scenarios = [
        {"own_country": CANADA_QID},
        {"own_country": FOREIGN_QID},
        {"own_country": CANADA_QID, "headquarters_country": FOREIGN_QID},
        {"headquarters_country": CANADA_QID},
        {"parent_country": CANADA_QID},
        {"owner_country": FOREIGN_QID},
        {},
    ]
    for overrides in scenarios:
        resolved = empty_resolution()
        resolved.update(overrides)
        _, confidence, _ = classify(resolved)
        assert 0.0 <= confidence <= 1.0
