"""BibTeX generation from paper dicts."""

import re

ESCAPE_MAP = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
}
_ESCAPE_PATTERN = re.compile("|".join(re.escape(c) for c in ESCAPE_MAP))


def escape_bibtex(text: str) -> str:
    if not text:
        return ""
    return _ESCAPE_PATTERN.sub(lambda m: ESCAPE_MAP[m.group(0)], text)


def _last_name(author: str) -> str:
    parts = author.strip().split()
    return parts[-1] if parts else "unknown"


def _base_key(paper: dict) -> str:
    authors = paper.get("authors") or []
    first_author_last = _last_name(authors[0]) if authors else "anon"
    year = paper.get("year") or "nd"
    slug = re.sub(r"[^a-z0-9]", "", first_author_last.lower())
    return f"{slug or 'anon'}{year}"


def generate_keys(papers: list) -> dict:
    """Returns {paper_id: citation_key}, disambiguating collisions with a/b/c suffixes."""
    counts = {}
    keys = {}
    for paper in papers:
        base = _base_key(paper)
        n = counts.get(base, 0)
        suffix = "" if n == 0 else chr(ord("a") + n - 1)
        keys[paper["id"]] = f"{base}{suffix}"
        counts[base] = n + 1
    return keys


def paper_to_entry(paper: dict, key: str) -> str:
    authors = paper.get("authors") or []
    author_field = " and ".join(escape_bibtex(a) for a in authors) or "Unknown"
    lines = [f"@article{{{key},"]
    lines.append(f"  title = {{{escape_bibtex(paper.get('title') or '')}}},")
    lines.append(f"  author = {{{author_field}}},")
    if paper.get("year"):
        lines.append(f"  year = {{{paper['year']}}},")
    if paper.get("journal"):
        lines.append(f"  journal = {{{escape_bibtex(paper['journal'])}}},")
    if paper.get("doi"):
        lines.append(f"  doi = {{{paper['doi']}}},")
    lines.append("}")
    return "\n".join(lines)


def generate_bibtex(papers: list) -> str:
    if not papers:
        return ""
    keys = generate_keys(papers)
    entries = [paper_to_entry(p, keys[p["id"]]) for p in papers]
    return "\n\n".join(entries) + "\n"
