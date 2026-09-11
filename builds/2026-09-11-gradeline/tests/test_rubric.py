import json

import pytest

from src.rubric import (
    RubricError,
    load_rubric,
    load_rubric_dict,
    write_starter_rubric,
)

VALID_RUBRIC = {
    "name": "Test Rubric",
    "min_words": 100,
    "max_words": 500,
    "min_citations": 1,
    "required_sections": ["Introduction"],
    "criteria": [
        {
            "id": "c1",
            "name": "Criterion One",
            "description": "desc",
            "max_points": 10,
            "keywords": ["alpha", "beta"],
            "min_keyword_hits": 1,
            "manual_only": False,
        },
        {
            "id": "c2",
            "name": "Manual Criterion",
            "max_points": 20,
            "manual_only": True,
        },
    ],
}


def test_load_valid_rubric_from_dict():
    rubric = load_rubric_dict(VALID_RUBRIC)
    assert rubric.name == "Test Rubric"
    assert rubric.min_words == 100
    assert rubric.max_words == 500
    assert len(rubric.criteria) == 2


def test_auto_scored_and_manual_criteria_split():
    rubric = load_rubric_dict(VALID_RUBRIC)
    assert [c.id for c in rubric.auto_scored_criteria()] == ["c1"]
    assert [c.id for c in rubric.manual_criteria()] == ["c2"]


def test_missing_required_key_raises():
    bad = {"name": "No criteria"}
    with pytest.raises(RubricError, match="criteria"):
        load_rubric_dict(bad)


def test_criterion_missing_required_key_raises():
    bad = dict(VALID_RUBRIC)
    bad["criteria"] = [{"id": "x"}]
    with pytest.raises(RubricError, match="missing required key"):
        load_rubric_dict(bad)


def test_non_manual_without_min_hits_raises():
    bad = dict(VALID_RUBRIC)
    bad["criteria"] = [
        {"id": "c1", "name": "C1", "max_points": 10, "keywords": ["x"], "min_keyword_hits": 0}
    ]
    with pytest.raises(RubricError, match="min_keyword_hits"):
        load_rubric_dict(bad)


def test_non_manual_without_keywords_raises():
    bad = dict(VALID_RUBRIC)
    bad["criteria"] = [
        {"id": "c1", "name": "C1", "max_points": 10, "keywords": [], "min_keyword_hits": 2}
    ]
    with pytest.raises(RubricError, match="keywords"):
        load_rubric_dict(bad)


def test_manual_only_criterion_allows_empty_keywords():
    data = dict(VALID_RUBRIC)
    data["criteria"] = [{"id": "m1", "name": "Manual", "max_points": 5, "manual_only": True}]
    rubric = load_rubric_dict(data)
    assert rubric.criteria[0].manual_only is True
    assert rubric.criteria[0].keywords == []


def test_duplicate_criterion_id_raises():
    bad = dict(VALID_RUBRIC)
    bad["criteria"] = [
        {"id": "dup", "name": "A", "max_points": 5, "keywords": ["x"], "min_keyword_hits": 1},
        {"id": "dup", "name": "B", "max_points": 5, "keywords": ["y"], "min_keyword_hits": 1},
    ]
    with pytest.raises(RubricError, match="Duplicate"):
        load_rubric_dict(bad)


def test_min_words_greater_than_max_words_raises():
    bad = dict(VALID_RUBRIC)
    bad["min_words"] = 500
    bad["max_words"] = 100
    with pytest.raises(RubricError, match="min_words"):
        load_rubric_dict(bad)


def test_zero_criteria_raises():
    bad = dict(VALID_RUBRIC)
    bad["criteria"] = []
    with pytest.raises(RubricError, match="at least one criterion"):
        load_rubric_dict(bad)


def test_load_rubric_from_file(tmp_path):
    path = tmp_path / "rubric.json"
    path.write_text(json.dumps(VALID_RUBRIC))
    rubric = load_rubric(str(path))
    assert rubric.name == "Test Rubric"


def test_write_starter_rubric_is_valid(tmp_path):
    path = tmp_path / "starter.json"
    write_starter_rubric(str(path))
    rubric = load_rubric(str(path))
    assert len(rubric.criteria) >= 1
    assert any(c.manual_only for c in rubric.criteria)
    assert any(not c.manual_only for c in rubric.criteria)
