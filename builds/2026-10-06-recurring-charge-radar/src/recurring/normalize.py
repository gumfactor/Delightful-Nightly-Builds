"""Turn noisy bank descriptions into a stable merchant key and display name."""
from __future__ import annotations

import re

_PREFIXES = re.compile(
    r"^(?:(?:pos|visa|debit|purchase|pre-?authorized|preauth(?:orized)?|pap|recurring|"
    r"online|e-?commerce|interac|contactless|payment to|payment)\s+)+",
    re.I,
)
_PROCESSORS = re.compile(r"^(?:sq|tst|pp|paypal|sp|cko|stripe|google|gog|amzn mktp|apl|dnh)\s*\*\s*", re.I)
_DOMAIN = re.compile(r"\b(?:www\.)?([a-z0-9-]+)\.(?:com|ca|net|org|io|ai|co)\b", re.I)
_PHONE = re.compile(r"\b(?:\d{3}[-. ])?\d{3}[-. ]\d{4}\b")
_CODE_TOKEN = re.compile(r"\b(?=[A-Za-z0-9]*\d)(?=[A-Za-z0-9]*[A-Za-z])[A-Za-z0-9]{5,}\b")
_CITIES = (
    "toronto|ottawa|vancouver|montreal|calgary|edmonton|winnipeg|halifax|mississauga|waterloo|"
    "san francisco|mountain view|palo alto|seattle|new york|austin|phoenix|dublin|london|stockholm|"
    "cupertino|menlo park|redwood city|wilmington|brooklyn|chicago|boston"
)
_CITY_TAIL = re.compile(r"\s+(?:" + _CITIES + r")\s*$", re.I)
_PROVINCES = r"(?:ON|QC|BC|AB|MB|SK|NS|NB|NL|PE|PEI|YT|NT|NU|CA|US|NY|WA|DE|TX|IE|GB)"
_PROVINCE_ONLY = re.compile(r"\s+" + _PROVINCES + r"\s*$")
_LOCATION_TAIL = re.compile(r"\s+[A-Za-z .'-]{2,20}\s+" + _PROVINCES + r"\s*$")
_REF_NUMBERS = re.compile(r"(?:#|\bno\.?\s*|\bref\s*:?\s*)?\b[\dA-Z]*\d[\dA-Z]*\b\s*$")
_TRAILING_JUNK = re.compile(r"[\s*#\-_.,:/]+$")


def clean_description(raw: str) -> str:
    """Strip prefixes, processor tags, reference numbers and location tails."""
    text = " ".join(raw.split())
    text = _PREFIXES.sub("", text)
    text = _PROCESSORS.sub("", text)
    text = re.sub(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b", " ", text)
    text = _PHONE.sub(" ", text)
    text = _CODE_TOKEN.sub(" ", text)
    text = _DOMAIN.sub(r"\1", text).replace("*", " ")
    for _ in range(3):
        stripped = _LOCATION_TAIL.sub("", text)
        stripped = _CITY_TAIL.sub("", stripped)
        stripped = _PROVINCE_ONLY.sub("", stripped)
        stripped = _REF_NUMBERS.sub("", stripped)
        stripped = _TRAILING_JUNK.sub("", stripped)
        if stripped == text:
            break
        text = stripped
    return " ".join(text.split())


def merchant_key(raw: str) -> str:
    """Lowercase alphanumeric key used to group charges from one merchant."""
    cleaned = clean_description(raw)
    key = re.sub(r"[^a-z0-9 ]+", " ", cleaned.lower())
    return " ".join(key.split())


def display_name(raw: str) -> str:
    """Human readable merchant name from a raw description."""
    cleaned = clean_description(raw)
    if not cleaned:
        return raw.strip() or "Unknown"
    if cleaned.isupper() or cleaned.islower():
        return cleaned.title()
    return cleaned
