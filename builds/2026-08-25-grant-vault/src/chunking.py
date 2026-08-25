"""Splits raw grant document text into paragraph-level chunks."""

import re


def split_into_chunks(text: str) -> list[str]:
    """Split text into paragraph chunks separated by one or more blank lines.

    Each returned chunk has internal whitespace normalized (trailing
    whitespace stripped per line, no leading/trailing blank lines) but
    single newlines within a paragraph are preserved. Chunks that are
    empty after normalization are dropped.
    """
    if not text or not text.strip():
        return []

    raw_paragraphs = re.split(r"\n\s*\n+", text)

    chunks = []
    for raw in raw_paragraphs:
        lines = [line.strip() for line in raw.splitlines()]
        lines = [line for line in lines if line]
        if not lines:
            continue
        chunks.append("\n".join(lines))
    return chunks
