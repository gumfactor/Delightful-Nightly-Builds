"""Default search topics for the PubMed Research Radar.

Seeded from the research interests described in PROFILE.md: forensic and
affective neuroscience, empathy, psychopathy, and stress/coping.
"""

from typing import NamedTuple


class TopicSeed(NamedTuple):
    name: str
    query: str


DEFAULT_TOPICS: list[TopicSeed] = [
    TopicSeed(
        name="Affective Neuroscience",
        query='"affective neuroscience"[tiab] AND (emotion[tiab] OR affect[tiab])',
    ),
    TopicSeed(
        name="Psychopathy & Antisocial Traits",
        query="psychopathy[tiab] OR psychopathic[tiab]",
    ),
    TopicSeed(
        name="Empathy",
        query="empathy[tiab] AND (neuroscience[tiab] OR neural[tiab] OR brain[tiab])",
    ),
    TopicSeed(
        name="Stress & Coping",
        query='"stress and coping"[tiab] OR (stress[tiab] AND coping[tiab])',
    ),
    TopicSeed(
        name="Forensic Neuroscience",
        query="forensic[tiab] AND (neuroscience[tiab] OR neuroimaging[tiab])",
    ),
]

PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"

DEFAULT_DB_PATH = "data/radar.db"
DEFAULT_FETCH_DAYS = 14
DEFAULT_MAX_PER_TOPIC = 20
