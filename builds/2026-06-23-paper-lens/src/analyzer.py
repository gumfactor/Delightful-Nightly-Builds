"""Anthropic API integration — batched relevance analysis for fetched papers."""
import json
import os
import urllib.request
import urllib.error

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"
ABSTRACT_TRUNCATE = 500  # characters

_RESEARCH_CONTEXT = (
    "You are helping a neuroscience professor and AI researcher keep up with literature.\n"
    "Their research areas:\n"
    "- Affective neuroscience (empathy, psychopathy, emotional regulation, social cognition)\n"
    "- Forensic neuroscience (psychopathy, criminal behavior, neurobiological correlates)\n"
    "- Stress research (cortisol, HPA axis, allostatic load, stress and coping)\n"
    "- Neuroimaging methods (fMRI, EEG, eye tracking, behavioral experiments)\n"
    "- AI/ML systems (agentic AI, LLMs, autonomous agents, human-AI collaboration)\n"
    "- Research methodology (statistics, open science, study design)"
)


def build_analysis_prompt(papers: list) -> str:
    entries = []
    for p in papers:
        abstract = p.get("abstract", "")
        if len(abstract) > ABSTRACT_TRUNCATE:
            abstract = abstract[:ABSTRACT_TRUNCATE] + "..."
        entries.append(
            f"ID: {p['arxiv_id']}\n"
            f"Title: {p['title']}\n"
            f"Abstract: {abstract}"
        )
    papers_block = "\n\n---\n\n".join(entries)
    return (
        f"{_RESEARCH_CONTEXT}\n\n"
        "Rate each paper's relevance and summarise it for this researcher.\n\n"
        f"Papers:\n\n{papers_block}\n\n"
        "Respond with a JSON array only (no other text). Each element:\n"
        '{"arxiv_id":"...","relevance":<1-10>,"summary":"<2 plain-English sentences>",'
        '"methodology":"<fMRI|behavioral|computational|review|ML|theory|other>",'
        '"topic":"<3-5 word label>"}'
    )


def analyze_papers(papers: list, api_key: str = "") -> dict:
    """Returns dict mapping arxiv_id → analysis dict. Falls back to defaults on any error."""
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if not papers:
        return {}

    if not api_key:
        return {p["arxiv_id"]: _default_analysis(p) for p in papers}

    prompt = build_analysis_prompt(papers)
    try:
        response_text = _call_anthropic(prompt, api_key)
        return _parse_analysis_response(response_text, papers)
    except Exception:
        return {p["arxiv_id"]: _default_analysis(p) for p in papers}


def _call_anthropic(prompt: str, api_key: str) -> str:
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        result = json.loads(resp.read())
    return result["content"][0]["text"]


def _parse_analysis_response(text: str, papers: list) -> dict:
    """Parse JSON array from response; fill defaults for any missing/malformed entries."""
    defaults = {p["arxiv_id"]: _default_analysis(p) for p in papers}

    text = text.strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return defaults

    try:
        items = json.loads(text[start : end + 1])
    except (json.JSONDecodeError, ValueError):
        return defaults

    results = dict(defaults)
    for item in items:
        arxiv_id = str(item.get("arxiv_id", ""))
        if arxiv_id not in results:
            continue
        try:
            relevance = int(item.get("relevance", 5))
            relevance = max(1, min(10, relevance))
        except (TypeError, ValueError):
            relevance = 5

        results[arxiv_id] = {
            "relevance_score": relevance,
            "summary": str(item.get("summary", ""))[:600],
            "methodology": str(item.get("methodology", "other"))[:50],
            "topic_label": str(item.get("topic", ""))[:100],
        }
    return results


def _default_analysis(paper: dict) -> dict:
    abstract = paper.get("abstract", "")
    summary = abstract[:200] + ("..." if len(abstract) > 200 else "")
    return {
        "relevance_score": 5,
        "summary": summary,
        "methodology": "other",
        "topic_label": "",
    }
