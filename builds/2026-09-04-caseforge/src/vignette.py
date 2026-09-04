"""Deterministic case vignette assembly, plus an optional AI-polish path
guarded by a fact-presence safety net.

The deterministic assembler always produces valid, complete text from
whatever facts extraction.py actually found — it never needs an API key
and never makes a network call. The optional AI-polish path may only
replace that text if every numeric/statistical fact the deterministic
extractor found is still present, verbatim, in the AI's output; otherwise
it silently falls back to the deterministic text. This makes it
structurally impossible for the AI path to invent or drop a number.
"""
from typing import Callable, List, Optional, Tuple

from .extraction import Facts, indefinite_article

AiCall = Callable[[str], Optional[str]]


def assemble_deterministic_vignette(
    title: str, journal: Optional[str], pub_year: Optional[int], facts: Facts
) -> str:
    """Build a complete teaching-case paragraph purely from real, extracted
    facts and article metadata. Always returns non-empty text."""
    citation_bit = f'"{title}"'
    if journal:
        citation_bit += f", published in {journal}"
    if pub_year:
        citation_bit += f" ({pub_year})"
    parts = [f"A research team published {citation_bit}."]

    method_bits = []
    methodology = facts.get("methodology")
    population = facts.get("population")
    sample_size = facts.get("sample_size")
    if methodology:
        method_bits.append(f"used a {methodology} design")
    if population:
        method_bits.append(f"studying {indefinite_article(population)} {population}")
    if sample_size:
        method_bits.append(f"with a reported sample size of N={sample_size}")
    if method_bits:
        parts.append("The study " + ", ".join(method_bits) + ".")

    stat_bits = []
    effect_size = facts.get("effect_size_text")
    p_value = facts.get("p_value_text")
    if effect_size:
        stat_bits.append(f"an effect size of {effect_size}")
    if p_value:
        stat_bits.append(f"a reported significance of {p_value}")
    if stat_bits:
        parts.append("Key reported statistics include " + " and ".join(stat_bits) + ".")
    else:
        parts.append(
            "No specific effect size or p-value could be extracted directly "
            "from the abstract text."
        )

    return " ".join(parts)


def required_fact_strings(facts: Facts) -> List[str]:
    """Every fact substring that must survive verbatim in any AI-polished
    text for that text to be accepted."""
    required: List[str] = []
    sample_size = facts.get("sample_size")
    if sample_size:
        required.append(str(sample_size))
    for key in ("effect_size_text", "p_value_text"):
        value = facts.get(key)
        if value:
            required.append(str(value))
    return required


def build_polish_prompt(deterministic_text: str, title: str, register: str) -> str:
    return (
        f"Rewrite the following research summary into a smoother, engaging "
        f"teaching-case paragraph for a {register} audience. Do not invent, "
        f"round, or omit any number, statistic, or fact that appears in the "
        f"source text below — every one must appear in your rewrite "
        f"exactly as written.\n\n"
        f"Title: {title}\n\n"
        f"Source text: {deterministic_text}"
    )


def polish_with_ai(
    deterministic_text: str,
    title: str,
    facts: Facts,
    register: str,
    ai_call: AiCall,
) -> Tuple[str, str]:
    """Attempt to polish the vignette via ai_call(prompt) -> text|None.

    Returns (text, source) where source is 'ai' only if the AI response
    preserved every required fact string verbatim; otherwise returns the
    original deterministic text with source 'deterministic'."""
    required = required_fact_strings(facts)
    prompt = build_polish_prompt(deterministic_text, title, register)
    try:
        result = ai_call(prompt)
    except Exception:
        result = None

    if result and all(fact in result for fact in required):
        return result.strip(), "ai"
    return deterministic_text, "deterministic"
