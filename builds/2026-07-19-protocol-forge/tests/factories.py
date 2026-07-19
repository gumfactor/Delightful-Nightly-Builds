"""Shared study-dict factory for tests. Not itself a test file."""
from __future__ import annotations

from typing import Any


def make_study_dict(**overrides: Any) -> dict:
    """A fully compliant study dict (passes every checklist rule cleanly).
    Individual tests override specific fields to trigger specific findings.
    """
    base = {
        "title": "Effects of Time Pressure on Empathic Accuracy",
        "pi": "Dr. Example",
        "study_type": "new",
        "population": {
            "description": "Adults 18-65 recruited via campus mailing list",
            "vulnerable_groups": ["none"],
        },
        "procedures": "Participants complete a 30-minute computerized empathy-accuracy task.",
        "deception": False,
        "deception_debrief": "",
        "data_collected": ["survey_responses", "reaction_time_data"],
        "data_identifiable": False,
        "data_storage_plan": "Data is de-identified at collection and stored on an encrypted, password-protected drive with restricted access.",
        "data_retention_years": 5,
        "compensation": "$10 gift card",
        "risks": [
            {
                "description": "Minor psychological discomfort from self-reflective questions",
                "likelihood": "low",
                "mitigation": "Participants may skip any question or withdraw at any time",
            }
        ],
        "recruitment_method": "Flyers and campus-wide email list",
        "consent_process": "Participants review and sign an informed consent form before beginning; they are told they may withdraw at any time without losing compensation already earned.",
    }
    base.update(overrides)
    return base
