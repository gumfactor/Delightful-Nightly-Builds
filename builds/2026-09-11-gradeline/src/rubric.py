"""Rubric loading and validation.

A rubric is an instructor-authored JSON file describing document-level
requirements (word count range, required section headings, a minimum
citation count) plus a list of scored criteria. Each criterion is either
keyword-coverage-scored (deterministic) or explicitly `manual_only`
(reserved for the instructor's own holistic judgment — never auto-scored).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field


class RubricError(ValueError):
    """Raised when a rubric file is missing required fields or malformed."""


@dataclass
class Criterion:
    id: str
    name: str
    description: str
    max_points: float
    keywords: list[str] = field(default_factory=list)
    min_keyword_hits: int = 0
    manual_only: bool = False


@dataclass
class Rubric:
    name: str
    min_words: int | None
    max_words: int | None
    min_citations: int
    required_sections: list[str]
    criteria: list[Criterion]

    def auto_scored_criteria(self) -> list[Criterion]:
        return [c for c in self.criteria if not c.manual_only]

    def manual_criteria(self) -> list[Criterion]:
        return [c for c in self.criteria if c.manual_only]


REQUIRED_RUBRIC_KEYS = ("name", "criteria")
REQUIRED_CRITERION_KEYS = ("id", "name", "max_points")


def _validate_criterion(raw: dict, index: int) -> Criterion:
    for key in REQUIRED_CRITERION_KEYS:
        if key not in raw:
            raise RubricError(f"Criterion #{index} is missing required key '{key}'")
    manual_only = bool(raw.get("manual_only", False))
    keywords = list(raw.get("keywords", []))
    min_hits = int(raw.get("min_keyword_hits", 0))
    if not manual_only and min_hits <= 0:
        raise RubricError(
            f"Criterion '{raw['id']}' is not manual_only but has no positive "
            "min_keyword_hits — it can never be scored. Set manual_only: true "
            "or give it keywords and a min_keyword_hits >= 1."
        )
    if not manual_only and not keywords:
        raise RubricError(
            f"Criterion '{raw['id']}' is not manual_only but has no keywords — "
            "it can never be scored. Set manual_only: true or give it keywords."
        )
    max_points = float(raw["max_points"])
    if max_points <= 0:
        raise RubricError(f"Criterion '{raw['id']}' max_points must be positive")
    return Criterion(
        id=str(raw["id"]),
        name=str(raw["name"]),
        description=str(raw.get("description", "")),
        max_points=max_points,
        keywords=keywords,
        min_keyword_hits=min_hits,
        manual_only=manual_only,
    )


def load_rubric_dict(data: dict) -> Rubric:
    for key in REQUIRED_RUBRIC_KEYS:
        if key not in data:
            raise RubricError(f"Rubric is missing required key '{key}'")
    raw_criteria = data["criteria"]
    if not raw_criteria:
        raise RubricError("Rubric must define at least one criterion")
    seen_ids: set[str] = set()
    criteria = []
    for i, raw in enumerate(raw_criteria):
        criterion = _validate_criterion(raw, i)
        if criterion.id in seen_ids:
            raise RubricError(f"Duplicate criterion id '{criterion.id}'")
        seen_ids.add(criterion.id)
        criteria.append(criterion)

    min_words = data.get("min_words")
    max_words = data.get("max_words")
    if min_words is not None and max_words is not None and int(min_words) > int(max_words):
        raise RubricError("min_words cannot be greater than max_words")

    return Rubric(
        name=str(data["name"]),
        min_words=int(min_words) if min_words is not None else None,
        max_words=int(max_words) if max_words is not None else None,
        min_citations=int(data.get("min_citations", 0)),
        required_sections=list(data.get("required_sections", [])),
        criteria=criteria,
    )


def load_rubric(path: str) -> Rubric:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return load_rubric_dict(data)


STARTER_RUBRIC = {
    "name": "Example Rubric — replace with your own",
    "min_words": 800,
    "max_words": 1500,
    "min_citations": 3,
    "required_sections": ["Introduction", "Discussion", "Conclusion"],
    "criteria": [
        {
            "id": "thesis",
            "name": "Clear Thesis",
            "description": "States a clear, arguable thesis in the introduction.",
            "max_points": 10,
            "keywords": ["thesis", "argue", "claim", "argument"],
            "min_keyword_hits": 1,
            "manual_only": False,
        },
        {
            "id": "evidence",
            "name": "Use of Evidence",
            "description": "Supports claims with cited evidence from course material.",
            "max_points": 15,
            "keywords": ["study", "research", "evidence", "finding", "data"],
            "min_keyword_hits": 3,
            "manual_only": False,
        },
        {
            "id": "argument_quality",
            "name": "Argument Quality",
            "description": (
                "Depth, coherence, and originality of the overall argument. "
                "Requires the instructor's own judgment."
            ),
            "max_points": 20,
            "keywords": [],
            "min_keyword_hits": 0,
            "manual_only": True,
        },
    ],
}


def write_starter_rubric(path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(STARTER_RUBRIC, f, indent=2)
        f.write("\n")
