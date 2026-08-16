from src import parser


def test_normalize_name_lowercases_strips_punctuation_and_singularizes():
    assert parser.normalize_name("HPA Axis") == "hpa axi"
    assert parser.normalize_name("Working Memory") == "working memory"
    assert parser.normalize_name("  Extra   Spaces  ") == "extra space"


def test_normalize_name_does_not_mangle_ss_endings():
    assert parser.normalize_name("Stress") == "stress"


def test_extract_markers_finds_all_bracketed_concepts():
    text = "We discuss [[HPA axis]] and later [[Allostatic Load]] in depth."
    assert parser.extract_markers(text) == ["HPA axis", "Allostatic Load"]


def test_extract_markers_ignores_unmarked_text():
    assert parser.extract_markers("No markers here at all.") == []


def test_extract_headings_markdown_with_named_prefix():
    text = "## Week 3: Stress and the HPA Axis\nBody text."
    assert parser.extract_headings(text) == ["Stress and the HPA Axis"]


def test_extract_headings_plain_named_prefix_no_markdown():
    text = "Session 1: Foundations of Affective Neuroscience\nBody."
    assert parser.extract_headings(text) == ["Foundations of Affective Neuroscience"]


def test_extract_headings_generic_markdown_with_colon():
    text = "## Neurotransmitters: Dopamine and Serotonin\nBody."
    assert parser.extract_headings(text) == ["Dopamine and Serotonin"]


def test_extract_headings_without_separator_produces_no_concept():
    text = "# Introduction\nJust an intro, no colon in the heading."
    assert parser.extract_headings(text) == []


def test_extract_headings_ignores_non_heading_lines():
    text = "This is a normal sentence: not a heading at all."
    assert parser.extract_headings(text) == []


def test_extract_headings_skips_h1_document_title_line():
    text = "# Stress and Coping — Fall 2026\n## Week 3: Stress and the HPA Axis\nBody."
    concepts = parser.extract_headings(text)
    assert "Fall 2026" not in concepts
    assert "Stress and the HPA Axis" in concepts


def test_extract_headings_h1_with_named_prefix_still_extracts():
    text = "# Week 1: Course Overview and Goals"
    assert parser.extract_headings(text) == ["Course Overview and Goals"]


def test_extract_heuristic_phrases_finds_multiword_capitalized_runs():
    text = "The Amygdala plays a role. We also cover Working Memory tasks."
    phrases = parser.extract_heuristic_phrases(text)
    assert "Working Memory" in phrases


def test_extract_heuristic_phrases_skips_single_capitalized_words():
    text = "Stress is a common topic. Coping matters too."
    assert parser.extract_heuristic_phrases(text) == []


def test_extract_heuristic_phrases_filters_runs_of_only_common_words():
    text = "This Is optional reading for this unit."
    phrases = parser.extract_heuristic_phrases(text)
    assert "This Is" not in phrases


def test_extract_objectives_students_will_pattern():
    text = "Students will explain the HPA axis in the stress response."
    objs = parser.extract_objectives(text)
    assert len(objs) == 1
    assert objs[0].text == "explain the HPA axis in the stress response"


def test_extract_objectives_by_the_end_of_pattern():
    text = "By the end of this session, students will be able to distinguish empathy from contagion."
    objs = parser.extract_objectives(text)
    assert len(objs) == 1
    assert objs[0].text.startswith("students will be able to distinguish")


def test_extract_objectives_numbered_objective_pattern():
    text = "Objective 1: Students will identify two risks of using large language models."
    objs = parser.extract_objectives(text)
    assert len(objs) == 1
    assert "identify two risks" in objs[0].text


def test_extract_objectives_deduplicates_case_insensitively():
    text = "Students will explain X.\nstudents will explain X."
    objs = parser.extract_objectives(text)
    assert len(objs) == 1


def test_extract_objectives_returns_empty_for_plain_text():
    assert parser.extract_objectives("Just a plain paragraph with no objectives.") == []


def test_extract_objectives_joins_a_soft_wrapped_line_within_one_paragraph():
    text = (
        "Objective 1: Students will identify at least two risks of using large\n"
        "language models in a clinical workflow.\n\n"
        "Objective 2: A separate, unrelated objective."
    )
    objs = parser.extract_objectives(text)
    assert len(objs) == 2
    assert objs[0].text == (
        "Students will identify at least two risks of using large "
        "language models in a clinical workflow"
    )


def test_extract_objectives_blank_line_still_separates_distinct_objectives():
    text = "Students will explain X.\n\nStudents will explain Y."
    objs = parser.extract_objectives(text)
    assert [o.text for o in objs] == ["explain X", "explain Y"]


def test_parse_document_dedups_marker_and_heuristic_by_normalized_name():
    text = (
        "## Week 3: Stress and the HPA Axis\n\n"
        "We discuss the [[HPA Axis]] and later reference HPA Axis again in prose."
    )
    parsed = parser.parse_document(text)
    matches = [c for c in parsed.concepts if c.normalized_name == parser.normalize_name("HPA Axis")]
    assert len(matches) == 1
    assert matches[0].source == "marker"


def test_parse_document_empty_text_returns_empty_lists():
    parsed = parser.parse_document("")
    assert parsed.concepts == []
    assert parsed.objectives == []


def test_parse_document_full_fixture_has_expected_shape():
    with open("tests/fixtures/stress_coping_w3.md", encoding="utf-8") as f:
        text = f.read()
    parsed = parser.parse_document(text)
    names = {c.normalized_name for c in parsed.concepts}
    assert parser.normalize_name("HPA axis") in names
    assert len(parsed.objectives) == 2
