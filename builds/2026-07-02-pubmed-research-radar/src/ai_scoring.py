"""Relevance scoring and summarization for fetched articles.

Two paths:
  - AI path (used when ANTHROPIC_API_KEY is set): Claude Haiku scores relevance
    1-10 against the topic, writes a 2-3 sentence plain-English summary, and
    tags the methodology.
  - Fallback path (always available, no key required): keyword-overlap scoring
    against the topic's own query terms, no AI summary.

The tool is fully usable on the fallback path alone - the AI path is an
enhancement, never a requirement.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

import requests

from src.config import ANTHROPIC_MESSAGES_URL, ANTHROPIC_MODEL

REQUEST_TIMEOUT_SECONDS = 30
_WORD_RE = re.compile(r"[a-z]{3,}")


@dataclass
class ScoringResult:
    relevance_score: float
    ai_summary: str | None
    methodology_tag: str | None
    scoring_method: str  # "ai" or "fallback"


def score_article(topic_name: str, topic_query: str, article: dict) -> ScoringResult:
    """Score one article, using the AI path if a key is configured, else fallback."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            return _score_with_ai(api_key, topic_name, article)
        except Exception:
            # Any AI failure (network, parsing, rate limit) degrades to the
            # deterministic fallback rather than blocking the pipeline.
            return _score_with_fallback(topic_query, article)
    return _score_with_fallback(topic_query, article)


def _score_with_fallback(topic_query: str, article: dict) -> ScoringResult:
    query_terms = set(_WORD_RE.findall(topic_query.lower()))
    text = f"{article.get('title', '')} {article.get('abstract', '')}".lower()
    text_words = set(_WORD_RE.findall(text))
    if not query_terms:
        overlap_ratio = 0.0
    else:
        overlap_ratio = len(query_terms & text_words) / len(query_terms)
    score = round(1 + overlap_ratio * 9, 1)  # map 0..1 overlap to 1..10
    return ScoringResult(
        relevance_score=score,
        ai_summary=None,
        methodology_tag=None,
        scoring_method="fallback",
    )


def _score_with_ai(api_key: str, topic_name: str, article: dict) -> ScoringResult:
    prompt = (
        f"You are triaging biomedical literature for a researcher whose saved topic is "
        f'"{topic_name}".\n\n'
        f"Article title: {article.get('title', '')}\n"
        f"Abstract: {article.get('abstract', '') or '(no abstract available)'}\n\n"
        "Respond with ONLY a JSON object with exactly these keys:\n"
        '  "relevance_score": integer 1-10, how relevant this article is to the topic\n'
        '  "summary": a plain-English 2-3 sentence summary of the key finding and why it matters\n'
        '  "methodology_tag": one short tag such as "fMRI", "behavioral", "review", '
        '"meta-analysis", "EEG", "animal model", or "theoretical"\n'
        "No prose outside the JSON object."
    )
    response = requests.post(
        ANTHROPIC_MESSAGES_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": ANTHROPIC_MODEL,
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    raw_text = payload["content"][0]["text"]
    parsed = _extract_json_object(raw_text)

    score = float(parsed["relevance_score"])
    score = max(1.0, min(10.0, score))
    return ScoringResult(
        relevance_score=score,
        ai_summary=str(parsed["summary"]).strip(),
        methodology_tag=str(parsed.get("methodology_tag", "")).strip() or None,
        scoring_method="ai",
    )


def _extract_json_object(text: str) -> dict:
    """Pull the first {...} JSON object out of a model response, tolerating stray text."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON object found in AI response: {text!r}")
    return json.loads(text[start : end + 1])
