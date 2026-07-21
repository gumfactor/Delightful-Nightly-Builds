import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import taxonomy


def test_all_concept_ids_unique():
    ids = [c.id for c in taxonomy.CONCEPTS]
    assert len(ids) == len(set(ids))


def test_all_domain_ids_unique():
    ids = [d.id for d in taxonomy.DOMAINS]
    assert len(ids) == len(set(ids))


def test_every_concept_has_valid_subdomain_and_mechanism_type():
    for concept in taxonomy.CONCEPTS:
        assert concept.subdomain in taxonomy.SUBDOMAINS
        assert concept.mechanism_type in taxonomy.MECHANISM_TYPES


def test_every_domain_has_valid_nonempty_mechanism_types():
    for domain in taxonomy.DOMAINS:
        assert domain.mechanism_types
        assert set(domain.mechanism_types).issubset(set(taxonomy.MECHANISM_TYPES))


def test_no_orphan_concepts():
    for concept in taxonomy.CONCEPTS:
        assert any(taxonomy.is_compatible(concept, d) for d in taxonomy.DOMAINS), (
            f"Concept '{concept.id}' has no compatible domain"
        )


def test_no_orphan_domains():
    for domain in taxonomy.DOMAINS:
        assert any(taxonomy.is_compatible(c, domain) for c in taxonomy.CONCEPTS), (
            f"Domain '{domain.id}' has no compatible concept"
        )


def test_is_compatible_true_when_mechanism_type_matches():
    concept = taxonomy.get_concept("hpa_axis_response")
    domain = taxonomy.get_domain("kitchen")
    assert concept.mechanism_type in domain.mechanism_types
    assert taxonomy.is_compatible(concept, domain) is True


def test_is_compatible_false_when_mechanism_type_does_not_match():
    concept = taxonomy.get_concept("learned_helplessness")  # learned_pattern
    domain = taxonomy.get_domain("thermostat")  # feedback_loop, calibration_regulation
    assert taxonomy.is_compatible(concept, domain) is False


def test_valid_pairs_only_returns_compatible_pairs():
    pairs = taxonomy.valid_pairs()
    assert len(pairs) > 0
    for concept, domain in pairs:
        assert taxonomy.is_compatible(concept, domain)


def test_valid_pairs_filtered_by_concept():
    concept_id = "allostatic_load"
    pairs = taxonomy.valid_pairs(concept_id=concept_id)
    assert len(pairs) > 0
    assert all(c.id == concept_id for c, _ in pairs)


def test_valid_pairs_filtered_by_domain():
    domain_id = "garden"
    pairs = taxonomy.valid_pairs(domain_id=domain_id)
    assert len(pairs) > 0
    assert all(d.id == domain_id for _, d in pairs)


def test_valid_triples_multiply_pairs_by_audiences():
    pairs = taxonomy.valid_pairs()
    triples = taxonomy.valid_triples()
    assert len(triples) == len(pairs) * len(taxonomy.AUDIENCES)


def test_valid_triples_filtered_by_audience():
    triples = taxonomy.valid_triples(audience="public_talk")
    assert len(triples) > 0
    assert all(a == "public_talk" for _, _, a in triples)


def test_get_concept_and_get_domain_return_none_for_unknown_id():
    assert taxonomy.get_concept("not_a_real_concept") is None
    assert taxonomy.get_domain("not_a_real_domain") is None


def test_get_concept_and_get_domain_return_expected_object():
    concept = taxonomy.get_concept("empathy_fatigue")
    assert concept is not None
    assert concept.name == "Empathy (Compassion) Fatigue"
    domain = taxonomy.get_domain("phone_battery")
    assert domain is not None
    assert domain.name == "A Phone Battery"


def test_concept_rejects_invalid_subdomain():
    import pytest

    with pytest.raises(ValueError):
        taxonomy.Concept(
            id="x", name="X", subdomain="not_real", mechanism_type="threshold_trigger",
            trigger="t", mechanism="m", consequence="c", caveat="cv", description="d",
        )


def test_domain_rejects_invalid_mechanism_type():
    import pytest

    with pytest.raises(ValueError):
        taxonomy.Domain(
            id="x", name="X", mechanism_types=("not_real",),
            trigger_word="t", process_word="p", outcome_word="o", description="d",
        )
