"""CSV intake: header aliasing, encoding tolerance, and the Record model."""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from pathlib import Path

from . import normalize as nz

CANONICAL = ["name", "website", "phone", "email", "address", "city", "province", "postal_code", "category",
             "description", "updated_at"]
ALIASES = {
    "name": ["name", "business_name", "business", "company", "company_name", "title", "brand"],
    "website": ["website", "url", "web", "site", "homepage", "domain", "web_address"],
    "phone": ["phone", "tel", "telephone", "phone_number", "phone_no", "mobile"],
    "email": ["email", "e-mail", "email_address", "contact_email"],
    "address": ["address", "street", "street_address", "address1", "address_1", "addr"],
    "city": ["city", "town", "municipality"],
    "province": ["province", "prov", "state", "province_state", "region"],
    "postal_code": ["postal_code", "postal", "postalcode", "postcode", "zip", "zip_code"],
    "category": ["category", "categories", "industry", "type", "tags"],
    "description": ["description", "about", "summary", "notes", "blurb"],
    "updated_at": ["updated_at", "updated", "last_updated", "modified", "last_modified", "date"],
}
ID_HEADERS = ["id", "record_id", "listing_id", "uid", "business_id"]


class IntakeError(ValueError):
    pass


@dataclass
class Record:
    id: str
    source: str
    fields: dict[str, str]
    extra: dict[str, str] = field(default_factory=dict)
    # normalized comparison forms
    name_tokens: list[str] = field(default_factory=list)
    name_key: str = ""
    domain: str = ""
    phone: str = ""
    email: str = ""
    postal: str = ""
    street: str = ""
    unit: str = ""
    province: str = ""
    city_key: str = ""

    @classmethod
    def build(cls, rid: str, source: str, fields: dict[str, str], extra: dict[str, str]) -> "Record":
        rec = cls(id=rid, source=source, fields=fields, extra=extra)
        rec.name_tokens = nz.name_tokens(fields.get("name", ""))
        rec.name_key = " ".join(rec.name_tokens)
        rec.domain = nz.registered_domain(fields.get("website", "")) or ""
        rec.phone = nz.phone_digits(fields.get("phone", ""))
        rec.email = nz.normalize_email(fields.get("email", ""))
        rec.postal = nz.postal_code(fields.get("postal_code", ""))
        rec.street, rec.unit = nz.street_parts(fields.get("address", ""))
        rec.province = nz.province_code(fields.get("province", ""))
        rec.city_key = " ".join(nz._words(fields.get("city", "")))
        return rec


def decode_bytes(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1")


def map_headers(headers: list[str]) -> tuple[dict[str, str], str | None, list[str]]:
    """Return ({canonical: actual header}, id header, extra headers)."""
    lowered = {h.strip().lower().replace(" ", "_"): h for h in headers if h}
    mapping: dict[str, str] = {}
    for canon, names in ALIASES.items():
        for alias in names:
            if alias in lowered and lowered[alias] not in mapping.values():
                mapping[canon] = lowered[alias]
                break
    id_header = next((lowered[a] for a in ID_HEADERS if a in lowered), None)
    used = set(mapping.values()) | ({id_header} if id_header else set())
    extra = [h for h in headers if h and h not in used]
    return mapping, id_header, extra


def read_records(path: Path, source: str = "batch") -> tuple[list[Record], list[str], list[str]]:
    """Read a CSV into Records. Returns (records, original headers, warnings)."""
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise IntakeError(f"cannot read {path}: {exc}") from exc
    return parse_records(decode_bytes(raw), source)


def parse_records(text: str, source: str = "batch") -> tuple[list[Record], list[str], list[str]]:
    reader = csv.DictReader(io.StringIO(text, newline=""))
    headers = reader.fieldnames or []
    if not headers:
        raise IntakeError("CSV is empty or has no header row")
    mapping, id_header, extra_headers = map_headers(headers)
    if "name" not in mapping:
        raise IntakeError("no business-name column found (looked for: " + ", ".join(ALIASES["name"]) + ")")
    warnings: list[str] = []
    for canon in ("website", "phone", "address", "postal_code"):
        if canon not in mapping:
            warnings.append(f"no '{canon}' column — matching will rely on fewer signals")
    records: list[Record] = []
    seen_ids: set[str] = set()
    for line_no, row in enumerate(reader, start=2):
        fields = {canon: (row.get(actual) or "").strip() for canon, actual in mapping.items()}
        if not any(fields.values()):
            continue
        if not fields.get("name"):
            warnings.append(f"row {line_no - 1}: no business name; skipped")
            continue
        rid = (row.get(id_header) or "").strip() if id_header else ""
        rid = rid or str(line_no - 1)
        if source != "batch":
            rid = f"{source}:{rid}"
        if rid in seen_ids:
            warnings.append(f"row {line_no - 1}: duplicate id {rid!r}; renumbered")
            rid = f"{rid}#{line_no - 1}"
        seen_ids.add(rid)
        extra = {h: (row.get(h) or "").strip() for h in extra_headers}
        records.append(Record.build(rid, source, fields, extra))
    return records, headers, warnings
