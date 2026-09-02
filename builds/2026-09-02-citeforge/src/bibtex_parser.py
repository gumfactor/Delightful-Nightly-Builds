"""A from-scratch BibTeX (.bib) parser — stdlib only, no external bibtex library.

Handles @article/@book/@inbook/@misc/@online/@incollection/@inproceedings/
@phdthesis/@techreport entries, {}- and ""-delimited field values (including
nested braces), and "and"-separated author lists in both "Last, First" and
"First Last" forms. A malformed entry is skipped with a warning rather than
aborting the whole file.
"""

from __future__ import annotations

import re

from .models import Author, Reference

RECOGNIZED_TYPES = {
    "article", "book", "inbook", "misc", "online", "incollection",
    "inproceedings", "phdthesis", "techreport",
}

TYPE_MAP = {
    "article": "journal-article",
    "book": "book",
    "inbook": "book",
    "misc": "webpage",
    "online": "webpage",
}


class BibTexError(Exception):
    pass


def _find_top_level(text: str, char: str, start: int = 0) -> int:
    depth = 0
    in_quotes = False
    i = start
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"' and (i == 0 or text[i - 1] != "\\"):
            in_quotes = not in_quotes
        elif c == "{" and not in_quotes:
            depth += 1
        elif c == "}" and not in_quotes:
            depth -= 1
        elif c == char and depth == 0 and not in_quotes:
            return i
        i += 1
    return -1


def _find_matching_brace(text: str, open_idx: int) -> int:
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise BibTexError("unbalanced braces in field value")


def _find_matching_quote(text: str, open_idx: int) -> int:
    i = open_idx + 1
    n = len(text)
    while i < n:
        if text[i] == '"' and text[i - 1] != "\\":
            return i
        i += 1
    raise BibTexError("unterminated quoted field value")


def _clean_value(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return value.replace("{", "").replace("}", "")


def _parse_entry_body(body: str) -> tuple[str, dict[str, str]]:
    body = body.strip()
    comma_idx = _find_top_level(body, ",")
    if comma_idx == -1:
        raise BibTexError("no cite key/fields separator found")
    key = body[:comma_idx].strip()
    if not key:
        raise BibTexError("empty cite key")
    rest = body[comma_idx + 1 :]
    fields: dict[str, str] = {}
    pos = 0
    n = len(rest)
    while pos < n:
        while pos < n and rest[pos] in " \t\r\n,":
            pos += 1
        if pos >= n:
            break
        eq_idx = rest.find("=", pos)
        if eq_idx == -1:
            break
        field_name = rest[pos:eq_idx].strip().lower()
        pos = eq_idx + 1
        while pos < n and rest[pos] in " \t\r\n":
            pos += 1
        if pos >= n:
            raise BibTexError(f"field '{field_name}' has no value")
        if rest[pos] == "{":
            end = _find_matching_brace(rest, pos)
            value = rest[pos + 1 : end]
            pos = end + 1
        elif rest[pos] == '"':
            end = _find_matching_quote(rest, pos)
            value = rest[pos + 1 : end]
            pos = end + 1
        else:
            end = _find_top_level(rest, ",", start=pos)
            if end == -1:
                end = n
            value = rest[pos:end].strip()
            pos = end
        fields[field_name] = _clean_value(value)
    return key, fields


def parse_bibtex(text: str) -> tuple[list[dict], list[str]]:
    """Returns (entries, warnings). Each entry: {'type', 'key', 'fields'}."""
    entries: list[dict] = []
    warnings: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        at = text.find("@", i)
        if at == -1:
            break
        brace = text.find("{", at)
        if brace == -1:
            warnings.append(f"Malformed entry near position {at}: missing '{{' after '@'")
            i = at + 1
            continue
        entry_type = text[at + 1 : brace].strip().lower()
        depth = 0
        in_quotes = False
        j = brace
        while j < n:
            c = text[j]
            if c == '"' and text[j - 1] != "\\":
                in_quotes = not in_quotes
            elif c == "{" and not in_quotes:
                depth += 1
            elif c == "}" and not in_quotes:
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if j >= n:
            warnings.append(f"Malformed '{entry_type}' entry starting at {at}: unbalanced braces")
            i = at + 1
            continue
        body = text[brace + 1 : j]
        i = j + 1
        try:
            key, fields = _parse_entry_body(body)
        except BibTexError as exc:
            warnings.append(f"Skipped malformed '@{entry_type}' entry near position {at}: {exc}")
            continue
        if entry_type not in RECOGNIZED_TYPES:
            warnings.append(f"Entry '{key}' has unrecognized type '@{entry_type}', mapped to 'other'")
        entries.append({"type": entry_type, "key": key, "fields": fields})
    return entries, warnings


def _split_authors(author_field: str) -> list[Author]:
    if not author_field:
        return []
    raw_authors = re.split(r"\s+\band\b\s+", author_field, flags=re.IGNORECASE)
    authors = []
    for raw in raw_authors:
        raw = raw.strip()
        if not raw:
            continue
        if "," in raw:
            family, given = raw.split(",", 1)
            authors.append(Author(family=family.strip(), given=given.strip()))
        else:
            tokens = raw.split()
            if len(tokens) == 1:
                authors.append(Author(family=tokens[0], given=""))
            else:
                authors.append(Author(family=tokens[-1], given=" ".join(tokens[:-1])))
    return authors


def _entry_to_reference(entry: dict) -> Reference:
    fields = entry["fields"]
    ref_type = TYPE_MAP.get(entry["type"], "other")
    pages = fields.get("pages", "").replace("--", "-")
    container = (
        fields.get("journal")
        or fields.get("publisher")
        or fields.get("booktitle")
        or fields.get("organization")
        or fields.get("school")
        or ""
    )
    return Reference(
        ref_type=ref_type,
        authors=_split_authors(fields.get("author", "")),
        year=fields.get("year", ""),
        title=fields.get("title", ""),
        container_title=container,
        volume=fields.get("volume", ""),
        issue=fields.get("number", ""),
        pages=pages,
        doi=fields.get("doi", ""),
        url=fields.get("url", ""),
        source="bibtex",
    )


def parse_bibtex_to_references(text: str) -> tuple[list[Reference], list[str]]:
    entries, warnings = parse_bibtex(text)
    references = []
    for entry in entries:
        if not entry["fields"].get("title"):
            warnings.append(f"Skipped entry '{entry['key']}': missing required 'title' field")
            continue
        references.append(_entry_to_reference(entry))
    return references, warnings
