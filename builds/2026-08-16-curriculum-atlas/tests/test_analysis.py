from src import analysis


def test_tokenize_lowercases_and_drops_stopwords():
    tokens = analysis.tokenize("The HPA Axis and the Stress Response")
    assert "the" not in tokens
    assert "and" not in tokens
    assert "hpa" in tokens
    assert "axis" in tokens
    assert "stress" in tokens


def test_jaccard_identical_sets_is_one():
    a = {"hpa", "axis"}
    assert analysis.jaccard(a, a) == 1.0


def test_jaccard_disjoint_sets_is_zero():
    assert analysis.jaccard({"hpa", "axis"}, {"empathy", "concern"}) == 0.0


def test_jaccard_empty_sets_is_zero_not_error():
    assert analysis.jaccard(set(), set()) == 0.0
    assert analysis.jaccard({"a"}, set()) == 0.0


def test_find_gaps_hand_computed_reference_example():
    objectives = [{"text": "explain the role of the HPA axis in stress regulation"}]
    concepts = [{"display_name": "HPA Axis"}, {"display_name": "Allostatic Load"}]
    # obj tokens (stopwords/short words dropped): explain, role, hpa, axis, stress, regulation (6)
    # concept "HPA Axis" tokens: hpa, axis (2) -> intersection {hpa, axis} = 2, union = 6
    expected = 2 / 6
    results = analysis.find_gaps(objectives, concepts, threshold=0.15)
    assert results[0]["best_score"] == round(expected, 4)
    assert results[0]["best_concept"] == "HPA Axis"
    assert results[0]["flagged"] is False  # 0.333 > 0.15


def test_find_gaps_flags_objective_with_no_matching_concept():
    objectives = [{"text": "explain saliency map interpretability methods for transformers"}]
    concepts = [{"display_name": "HPA Axis"}, {"display_name": "Empathic Concern"}]
    results = analysis.find_gaps(objectives, concepts, threshold=0.15)
    assert results[0]["flagged"] is True
    assert results[0]["best_score"] == 0.0


def test_find_gaps_with_no_concepts_flags_everything():
    objectives = [{"text": "explain the HPA axis"}]
    results = analysis.find_gaps(objectives, [], threshold=0.15)
    assert results[0]["flagged"] is True
    assert results[0]["best_score"] == 0.0
    assert results[0]["best_concept"] is None


def test_find_gaps_preserves_objective_order():
    objectives = [{"text": "first objective text"}, {"text": "second objective text"}]
    results = analysis.find_gaps(objectives, [], threshold=0.15)
    assert results[0]["objective_text"] == "first objective text"
    assert results[1]["objective_text"] == "second objective text"


def _row(course_id, course_name, term, display_name, normalized_name, source_path="doc.md"):
    return {
        "course_id": course_id,
        "course_name": course_name,
        "term": term,
        "display_name": display_name,
        "normalized_name": normalized_name,
        "source": "marker",
        "source_path": source_path,
    }


def test_find_overlap_detects_concept_shared_across_two_courses():
    rows = [
        _row(1, "Stress and Coping", "Fall 2026", "HPA Axis", "hpa axi"),
        _row(2, "Social Affective Neuroscience", "Fall 2026", "HPA Axis", "hpa axi"),
        _row(1, "Stress and Coping", "Fall 2026", "Allostatic Load", "allostatic load"),
    ]
    results = analysis.find_overlap(rows)
    assert len(results) == 1
    assert results[0]["normalized_name"] == "hpa axi"
    assert results[0]["course_count"] == 2
    course_names = {loc["course_name"] for loc in results[0]["locations"]}
    assert course_names == {"Stress and Coping", "Social Affective Neuroscience"}


def test_find_overlap_excludes_concepts_unique_to_one_course():
    rows = [_row(1, "Course A", "Fall 2026", "Solo Concept", "solo concept")]
    assert analysis.find_overlap(rows) == []


def test_find_overlap_same_course_repeated_term_does_not_count_as_overlap():
    rows = [
        _row(1, "Course A", "Fall 2026", "Repeated", "repeated"),
        _row(1, "Course A", "Spring 2027", "Repeated", "repeated"),
    ]
    assert analysis.find_overlap(rows) == []


def test_diff_terms_reports_added_removed_kept():
    concepts_a = [
        {"normalized_name": "hpa axi", "display_name": "HPA Axis"},
        {"normalized_name": "coping", "display_name": "Coping"},
    ]
    concepts_b = [
        {"normalized_name": "hpa axi", "display_name": "HPA Axis"},
        {"normalized_name": "resilience", "display_name": "Resilience"},
    ]
    result = analysis.diff_terms(concepts_a, concepts_b)
    assert result["added"] == ["Resilience"]
    assert result["removed"] == ["Coping"]
    assert result["kept"] == ["HPA Axis"]


def test_diff_terms_empty_courses_returns_empty_lists():
    result = analysis.diff_terms([], [])
    assert result == {"added": [], "removed": [], "kept": []}
