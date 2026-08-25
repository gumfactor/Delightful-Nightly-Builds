from src.classifier import SECTION_TYPES, classify_section


def test_heading_specific_aims():
    chunk = "Specific Aims\nThis project will test whether X predicts Y."
    assert classify_section(chunk) == "Specific Aims"


def test_heading_significance():
    chunk = "Significance\nThis work matters for the field."
    assert classify_section(chunk) == "Significance"


def test_heading_innovation():
    chunk = "Innovation\nThis differs from all prior methods."
    assert classify_section(chunk) == "Innovation"


def test_heading_approach_word():
    chunk = "Approach\nParticipants will complete two sessions."
    assert classify_section(chunk) == "Approach"


def test_heading_research_strategy_maps_to_approach():
    chunk = "Research Strategy\nWe describe the study design below."
    assert classify_section(chunk) == "Approach"


def test_heading_broader_impacts():
    chunk = "Broader Impacts\nThis reaches underserved communities."
    assert classify_section(chunk) == "Broader Impacts"


def test_heading_data_management_plan():
    chunk = "Data Management Plan\nAll data will be archived."
    assert classify_section(chunk) == "Data Management Plan"


def test_heading_budget_justification():
    chunk = "Budget Justification\nFunds will cover personnel."
    assert classify_section(chunk) == "Budget Justification"


def test_keyword_fallback_specific_aims_without_heading():
    chunk = "We hypothesize that the central hypothesis will hold across two conditions and describe Aim 1 in detail below."
    assert classify_section(chunk) == "Specific Aims"


def test_keyword_fallback_approach_without_heading():
    chunk = "We will recruit participants using a standard procedure and record all measures during the experimental design phase."
    assert classify_section(chunk) == "Approach"


def test_keyword_fallback_data_management_without_heading():
    chunk = "All de-identified data will be deposited in a public repository consistent with our data management commitments."
    assert classify_section(chunk) == "Data Management Plan"


def test_ambiguous_text_returns_other():
    chunk = "The weather that afternoon was unremarkable and nothing else happened."
    assert classify_section(chunk) == "Other"


def test_empty_chunk_returns_other():
    assert classify_section("") == "Other"
    assert classify_section("   ") == "Other"


def test_all_declared_section_types_are_reachable():
    # Sanity check that every non-Other type in SECTION_TYPES has at least
    # one heading pattern wired up, so the constant and the classifier
    # can't silently drift apart.
    from src.classifier import _HEADING_PATTERNS

    for section in SECTION_TYPES:
        if section == "Other":
            continue
        assert section in _HEADING_PATTERNS
