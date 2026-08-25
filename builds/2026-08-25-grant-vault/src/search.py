"""Ranked search over stored grant chunks."""

import re
import sqlite3

from src import store

_TOKEN_RE = re.compile(r"[a-z0-9']+")


def search(
    conn: sqlite3.Connection,
    query: str = "",
    section: str | None = None,
    tag: str | None = None,
    min_reuse: int | None = None,
) -> list[dict]:
    """Return chunks matching the filters, ranked by relevance to query.

    An empty query returns all matching chunks ranked by reuse_score.
    """
    chunks = store.get_all_chunks(conn)

    if section:
        chunks = [c for c in chunks if c["section_type"] == section]
    if tag:
        lowered_tag = tag.lower()
        chunks = [c for c in chunks if lowered_tag in [t.lower() for t in c["tags"]]]
    if min_reuse is not None:
        chunks = [c for c in chunks if c["reuse_score"] >= min_reuse]

    if not query or not query.strip():
        return sorted(
            chunks,
            key=lambda c: (-c["reuse_score"], c["document_path"], c["chunk_index"]),
        )

    query_tokens = _TOKEN_RE.findall(query.lower())
    if not query_tokens:
        return []

    scored = []
    for chunk in chunks:
        text_lower = chunk["text"].lower()
        match_count = sum(text_lower.count(token) for token in query_tokens)
        if match_count > 0:
            scored.append((match_count, chunk))

    scored.sort(
        key=lambda pair: (
            -pair[0],
            -pair[1]["reuse_score"],
            pair[1]["document_path"],
            pair[1]["chunk_index"],
        )
    )
    return [chunk for _, chunk in scored]
