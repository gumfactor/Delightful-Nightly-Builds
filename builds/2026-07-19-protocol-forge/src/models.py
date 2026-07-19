"""Study data model: parsing and validating the user-authored study JSON."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

VALID_STUDY_TYPES = {"new", "renewal", "amendment"}
VALID_VULNERABLE_GROUPS = {
    "minors",
    "prisoners",
    "cognitively_impaired",
    "pregnant",
    "students_as_subjects",
    "none",
}

REQUIRED_TOP_LEVEL_KEYS = (
    "title",
    "study_type",
    "population",
    "procedures",
    "data_collected",
    "data_storage_plan",
    "recruitment_method",
    "consent_process",
)


@dataclass
class Risk:
    description: str
    likelihood: str = ""
    mitigation: str = ""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Risk":
        return Risk(
            description=str(data.get("description", "")).strip(),
            likelihood=str(data.get("likelihood", "")).strip(),
            mitigation=str(data.get("mitigation", "")).strip(),
        )


@dataclass
class Study:
    title: str
    study_type: str
    population_description: str
    vulnerable_groups: list[str]
    procedures: str
    data_collected: list[str]
    data_storage_plan: str
    recruitment_method: str
    consent_process: str
    pi: str = ""
    deception: bool = False
    deception_debrief: str = ""
    data_identifiable: bool = False
    data_retention_years: float = 0
    compensation: str = ""
    risks: list[Risk] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Study":
        if not isinstance(data, dict):
            raise ValueError("Study definition must be a JSON object.")

        missing = [key for key in REQUIRED_TOP_LEVEL_KEYS if not data.get(key)]
        if missing:
            raise ValueError(
                "Study definition is missing required field(s): " + ", ".join(missing)
            )

        study_type = str(data["study_type"]).strip().lower()
        if study_type not in VALID_STUDY_TYPES:
            raise ValueError(
                f"study_type must be one of {sorted(VALID_STUDY_TYPES)}, got {study_type!r}"
            )

        population = data["population"]
        if not isinstance(population, dict) or not population.get("description"):
            raise ValueError("population.description is required.")

        vulnerable_groups = [
            str(g).strip().lower() for g in population.get("vulnerable_groups", []) or []
        ]
        unknown = set(vulnerable_groups) - VALID_VULNERABLE_GROUPS
        if unknown:
            raise ValueError(
                f"Unknown vulnerable_groups value(s): {sorted(unknown)}. "
                f"Valid values are {sorted(VALID_VULNERABLE_GROUPS)}."
            )

        data_collected = [str(d).strip() for d in data.get("data_collected", []) or []]
        risks = [Risk.from_dict(r) for r in data.get("risks", []) or []]

        return Study(
            title=str(data["title"]).strip(),
            study_type=study_type,
            population_description=str(population["description"]).strip(),
            vulnerable_groups=vulnerable_groups,
            procedures=str(data["procedures"]).strip(),
            data_collected=data_collected,
            data_storage_plan=str(data["data_storage_plan"]).strip(),
            recruitment_method=str(data["recruitment_method"]).strip(),
            consent_process=str(data["consent_process"]).strip(),
            pi=str(data.get("pi", "")).strip(),
            deception=bool(data.get("deception", False)),
            deception_debrief=str(data.get("deception_debrief", "")).strip(),
            data_identifiable=bool(data.get("data_identifiable", False)),
            data_retention_years=float(data.get("data_retention_years", 0) or 0),
            compensation=str(data.get("compensation", "")).strip(),
            risks=risks,
        )

    @staticmethod
    def from_file(path: str | Path) -> "Study":
        file_path = Path(path)
        if not file_path.is_file():
            raise FileNotFoundError(f"Study file not found: {file_path}")
        try:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Study file is not valid JSON: {exc}") from exc
        return Study.from_dict(raw)

    def has_real_vulnerable_groups(self) -> bool:
        return any(g != "none" for g in self.vulnerable_groups)

    def tag_set(self) -> set[str]:
        """Deterministic tag set used for boilerplate similarity matching."""
        tags = {f"vg:{g}" for g in self.vulnerable_groups if g != "none"}
        tags.add(f"identifiable:{self.data_identifiable}")
        tags.add(f"deception:{self.deception}")
        tags.add(f"study_type:{self.study_type}")
        return tags

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "study_type": self.study_type,
            "pi": self.pi,
            "population": {
                "description": self.population_description,
                "vulnerable_groups": self.vulnerable_groups,
            },
            "procedures": self.procedures,
            "deception": self.deception,
            "deception_debrief": self.deception_debrief,
            "data_collected": self.data_collected,
            "data_identifiable": self.data_identifiable,
            "data_storage_plan": self.data_storage_plan,
            "data_retention_years": self.data_retention_years,
            "compensation": self.compensation,
            "risks": [
                {
                    "description": r.description,
                    "likelihood": r.likelihood,
                    "mitigation": r.mitigation,
                }
                for r in self.risks
            ],
            "recruitment_method": self.recruitment_method,
            "consent_process": self.consent_process,
        }


TEMPLATE_STUDY: dict[str, Any] = {
    "title": "REPLACE: short study title",
    "pi": "REPLACE: principal investigator name (optional)",
    "study_type": "new",
    "population": {
        "description": "REPLACE: who will participate (e.g. adults 18-65 recruited via campus mailing list)",
        "vulnerable_groups": ["none"],
    },
    "procedures": "REPLACE: step-by-step description of what participants will do",
    "deception": False,
    "deception_debrief": "",
    "data_collected": ["REPLACE: e.g. survey_responses"],
    "data_identifiable": False,
    "data_storage_plan": "REPLACE: where/how data is stored and who has access",
    "data_retention_years": 3,
    "compensation": "",
    "risks": [
        {
            "description": "REPLACE: e.g. minor psychological discomfort from survey questions",
            "likelihood": "REPLACE: e.g. low",
            "mitigation": "REPLACE: e.g. participants may skip any question or withdraw at any time",
        }
    ],
    "recruitment_method": "REPLACE: how participants will be recruited",
    "consent_process": "REPLACE: how informed consent will be obtained",
}
