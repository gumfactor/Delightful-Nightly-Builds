"""Default saved topics for GrantScope, seeded from PROFILE.md's named research areas."""

from typing import List, TypedDict


class Topic(TypedDict):
    key: str
    label: str
    search_text: str


DEFAULT_TOPICS: List[Topic] = [
    {
        "key": "empathy",
        "label": "Empathy & Prosocial Neuroscience",
        "search_text": "empathy prosocial neural",
    },
    {
        "key": "psychopathy",
        "label": "Psychopathy & Antisocial Behavior",
        "search_text": "psychopathy antisocial behavior",
    },
    {
        "key": "stress_coping",
        "label": "Stress & Coping Neurobiology",
        "search_text": "stress coping neurobiology",
    },
    {
        "key": "forensic_neuroscience",
        "label": "Forensic Neuroscience & Risk Assessment",
        "search_text": "forensic neuroscience risk assessment",
    },
    {
        "key": "affective_neuroscience",
        "label": "Affective Neuroscience & Emotion",
        "search_text": "affective neuroscience emotion regulation",
    },
]


def get_topic(key: str) -> Topic:
    for topic in DEFAULT_TOPICS:
        if topic["key"] == key:
            return topic
    raise KeyError(f"Unknown topic key: {key}")


def topic_keys() -> List[str]:
    return [topic["key"] for topic in DEFAULT_TOPICS]
