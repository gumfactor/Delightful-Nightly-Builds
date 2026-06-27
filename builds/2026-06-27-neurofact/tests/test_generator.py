"""pytest tests for src/generator.py — covers scoring, validation, and data assembly."""

import sys
import os
import json
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from generator import (
    compute_grade,
    compute_streak,
    validate_question,
    assemble_game_data,
    build_prompt,
    QUESTIONS_SEED,
)


# --- Grade computation ---

def test_grade_90_is_A():
    assert compute_grade(27, 30) == "A"


def test_grade_100_is_A():
    assert compute_grade(30, 30) == "A"


def test_grade_80_is_B():
    assert compute_grade(24, 30) == "B"


def test_grade_70_is_C():
    assert compute_grade(21, 30) == "C"


def test_grade_60_is_D():
    assert compute_grade(18, 30) == "D"


def test_grade_below_60_is_F():
    assert compute_grade(17, 30) == "F"


def test_grade_zero_score_is_F():
    assert compute_grade(0, 30) == "F"


def test_grade_zero_total_is_F():
    assert compute_grade(0, 0) == "F"


# --- Streak computation ---

def test_streak_all_correct():
    assert compute_streak([True] * 10) == 10


def test_streak_all_wrong():
    assert compute_streak([False] * 10) == 0


def test_streak_empty():
    assert compute_streak([]) == 0


def test_streak_mixed_picks_best():
    answers = [True, True, False, True, True, True, False, True]
    assert compute_streak(answers) == 3


def test_streak_single_correct():
    assert compute_streak([True]) == 1


def test_streak_resets_on_wrong():
    assert compute_streak([True, True, True, False, True, True]) == 3


# --- Question validation ---

def test_validate_valid_real_question():
    q = {
        "id": 1,
        "statement": "The hippocampus contains place cells.",
        "answer": "real",
        "category": "Memory",
        "difficulty": "Advanced",
        "explanation": "Correct — O'Keefe discovered place cells.",
    }
    assert validate_question(q) == []


def test_validate_valid_fake_question():
    q = {
        "id": 2,
        "statement": "The anterior commissure carries Broca-Wernicke signals.",
        "answer": "fake",
        "category": "Neuroanatomy",
        "difficulty": "Expert",
        "explanation": "Incorrect — the corpus callosum handles this.",
    }
    assert validate_question(q) == []


def test_validate_missing_statement():
    q = {"id": 1, "answer": "real", "category": "Memory",
         "difficulty": "Advanced", "explanation": "OK"}
    errors = validate_question(q)
    assert any("statement" in e for e in errors)


def test_validate_invalid_answer():
    q = {"id": 1, "statement": "Some claim.", "answer": "maybe",
         "category": "Memory", "difficulty": "Advanced", "explanation": "OK"}
    errors = validate_question(q)
    assert any("answer" in e for e in errors)


def test_validate_empty_statement():
    q = {"id": 1, "statement": "  ", "answer": "real",
         "category": "Memory", "difficulty": "Advanced", "explanation": "OK"}
    errors = validate_question(q)
    assert any("Empty statement" in e for e in errors)


def test_validate_missing_explanation():
    q = {"id": 1, "statement": "Claim.", "answer": "real",
         "category": "Memory", "difficulty": "Advanced"}
    errors = validate_question(q)
    assert any("explanation" in e for e in errors)


# --- Data assembly ---

def make_real(n=15):
    return [{"statement": f"Real claim {i}.", "category": "Memory",
              "difficulty": "Advanced", "explanation": f"Correct {i}."}
            for i in range(n)]


def make_fake(n=15):
    return [{"statement": f"Fake claim {i}.", "category": "Stress",
              "difficulty": "Expert", "explanation": f"Wrong because {i}."}
            for i in range(n)]


def test_assemble_returns_30_questions():
    q = assemble_game_data(make_real(15), make_fake(15))
    assert len(q) == 30


def test_assemble_15_real_15_fake():
    q = assemble_game_data(make_real(15), make_fake(15))
    reals = [x for x in q if x["answer"] == "real"]
    fakes = [x for x in q if x["answer"] == "fake"]
    assert len(reals) == 15
    assert len(fakes) == 15


def test_assemble_ids_are_sequential():
    q = assemble_game_data(make_real(5), make_fake(5))
    ids = [x["id"] for x in q]
    assert sorted(ids) == list(range(1, 11))


def test_assemble_all_have_required_fields():
    q = assemble_game_data(make_real(5), make_fake(5))
    for item in q:
        for field in ("id", "statement", "answer", "category", "difficulty", "explanation"):
            assert field in item


def test_assemble_different_seeds_produce_different_order():
    random.seed(42)
    order_a = [x["statement"] for x in assemble_game_data(make_real(15), make_fake(15))]
    random.seed(99)
    order_b = [x["statement"] for x in assemble_game_data(make_real(15), make_fake(15))]
    assert order_a != order_b


# --- Prompt structure ---

def test_build_prompt_contains_task_a():
    abstracts = [{"title": "T1", "abstract": "A1"}, {"title": "T2", "abstract": "A2"}]
    prompt = build_prompt(abstracts, n_fake=5)
    assert "TASK A" in prompt


def test_build_prompt_contains_task_b():
    abstracts = [{"title": "T1", "abstract": "A1"}]
    prompt = build_prompt(abstracts, n_fake=5)
    assert "TASK B" in prompt


def test_build_prompt_includes_abstract_text():
    abstracts = [{"title": "Hippocampal Place Cells", "abstract": "Neurons fire at locations."}]
    prompt = build_prompt(abstracts, n_fake=5)
    assert "Hippocampal Place Cells" in prompt
    assert "Neurons fire at locations" in prompt


def test_build_prompt_specifies_n_fake():
    abstracts = [{"title": "T", "abstract": "A"}]
    prompt = build_prompt(abstracts, n_fake=7)
    assert "7" in prompt


# --- Seed data ---

def test_seed_data_has_30_questions():
    assert len(QUESTIONS_SEED) == 30


def test_seed_data_has_15_real():
    reals = [q for q in QUESTIONS_SEED if q["answer"] == "real"]
    assert len(reals) == 15


def test_seed_data_has_15_fake():
    fakes = [q for q in QUESTIONS_SEED if q["answer"] == "fake"]
    assert len(fakes) == 15


def test_seed_data_all_valid():
    for q in QUESTIONS_SEED:
        errors = validate_question(q)
        assert errors == [], f"Question {q.get('id')} has errors: {errors}"


def test_seed_data_unique_statements():
    statements = [q["statement"] for q in QUESTIONS_SEED]
    assert len(set(statements)) == len(statements)


def test_seed_data_spans_multiple_categories():
    cats = {q["category"] for q in QUESTIONS_SEED}
    assert len(cats) >= 5


def test_seed_data_has_all_difficulty_levels():
    difficulties = {q["difficulty"] for q in QUESTIONS_SEED}
    assert "Foundational" in difficulties
    assert "Advanced" in difficulties
    assert "Expert" in difficulties
