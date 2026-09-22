from src import narrative
from src.openmeteo import WindowAggregate


def make_window(**overrides) -> WindowAggregate:
    defaults = dict(
        date="2026-10-04",
        window="afternoon",
        wind_knots=9.5,
        gust_knots=12.0,
        temp_c=21.0,
        precip_probability=10.0,
        cloud_cover=30.0,
        daylight_hours=6.0,
        beaufort_number=3,
        beaufort_name="Gentle Breeze",
        score=78.5,
    )
    defaults.update(overrides)
    return WindowAggregate(**defaults)


def test_build_facts_contains_expected_keys_and_values():
    window = make_window()
    facts = narrative.build_facts(window, "Stony Lake")
    assert facts["location_name"] == "Stony Lake"
    assert facts["date"] == "2026-10-04"
    assert facts["wind_knots"] == "9.5"
    assert facts["beaufort_name"] == "Gentle Breeze"
    assert facts["precip_probability"] == "10.0%"


def test_generated_narrative_contains_every_fact_verbatim():
    window = make_window()
    result = narrative.generate_narrative(window, "Stony Lake")
    facts = narrative.build_facts(window, "Stony Lake")
    assert narrative.verify_facts_present(result.text, facts)


def test_generated_narrative_selects_from_correct_bucket_for_calm_dry():
    window = make_window(beaufort_number=0, beaufort_name="Calm", precip_probability=5.0)
    result = narrative.generate_narrative(window, "Stony Lake")
    assert "Calm" in result.text


def test_generated_narrative_selects_from_correct_bucket_for_fresh_showery():
    window = make_window(beaufort_number=6, beaufort_name="Strong Breeze", precip_probability=80.0)
    result = narrative.generate_narrative(window, "Stony Lake")
    assert "Strong Breeze" in result.text
    assert "80.0%" in result.text


def test_novelty_scoring_avoids_a_recently_used_template():
    window = make_window()
    first = narrative.generate_narrative(window, "Stony Lake", history=[])
    # Feed the first result back in as "history" -- a second identical
    # generation should not repeat the same template.
    second = narrative.generate_narrative(window, "Stony Lake", history=[first.text])
    assert second.template_index != first.template_index


def test_novelty_scoring_is_deterministic_with_no_history():
    window = make_window()
    first = narrative.generate_narrative(window, "Stony Lake", history=[])
    second = narrative.generate_narrative(window, "Stony Lake", history=[])
    assert first.template_index == second.template_index
    assert first.text == second.text


def test_novelty_scoring_cycles_through_all_three_templates():
    window = make_window()
    history = []
    seen_indices = set()
    for _ in range(3):
        result = narrative.generate_narrative(window, "Stony Lake", history=history)
        seen_indices.add(result.template_index)
        history.append(result.text)
    assert seen_indices == {0, 1, 2}


def test_script_injection_in_location_name_is_not_html_but_is_present_verbatim():
    """narrative.py itself does no HTML escaping (that's render.py's job) --
    but confirm the raw text pipeline doesn't mangle or drop a hostile-looking
    location name, since render.py needs the exact original string to escape."""
    payload = "</script><script>alert(1)</script>"
    window = make_window()
    result = narrative.generate_narrative(window, payload)
    assert payload in result.text


def test_verify_facts_present_fails_when_a_fact_is_missing():
    facts = {"a": "9.5", "b": "Gentle Breeze"}
    assert narrative.verify_facts_present("wind was 9.5 knots", facts) is False


def test_verify_facts_present_true_when_all_present():
    facts = {"a": "9.5", "b": "Gentle Breeze"}
    assert narrative.verify_facts_present("9.5 knots of Gentle Breeze today", facts) is True
