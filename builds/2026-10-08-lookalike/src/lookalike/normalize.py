"""Field normalizers. Each returns a canonical comparison form ('' when the input is unusable)."""
from __future__ import annotations

import re
import unicodedata
from urllib.parse import urlsplit

LEGAL_SUFFIXES = {
    "inc", "incorporated", "ltd", "limited", "ltee", "ltée", "corp", "corporation", "co", "company", "llc", "lp",
    "llp", "enr", "senc", "sencrl", "sarl", "cie", "compagnie", "incorporee", "limitee",
}
LEADING_ARTICLES = {"the", "le", "la", "les", "l"}
SOCIAL_OR_MARKETPLACE = {
    "facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com", "tiktok.com", "youtube.com",
    "etsy.com", "amazon.ca", "amazon.com", "ebay.ca", "ebay.com", "shopify.com", "myshopify.com", "wixsite.com",
    "square.site", "business.site", "linktr.ee", "yelp.ca", "yelp.com", "google.com", "wordpress.com",
    "squarespace.com", "godaddysites.com", "weebly.com", "pinterest.com", "kijiji.ca",
}
SECOND_LEVEL = {"co", "com", "org", "net", "gov", "ac", "on", "qc", "bc", "ab", "mb", "sk", "ns", "nb", "nl", "pe"}
PROVINCES = {
    "alberta": "AB", "ab": "AB", "british columbia": "BC", "bc": "BC", "manitoba": "MB", "mb": "MB",
    "new brunswick": "NB", "nb": "NB", "newfoundland and labrador": "NL", "newfoundland": "NL", "nl": "NL",
    "nova scotia": "NS", "ns": "NS", "northwest territories": "NT", "nt": "NT", "nunavut": "NU", "nu": "NU",
    "ontario": "ON", "on": "ON", "ont": "ON", "prince edward island": "PE", "pei": "PE", "pe": "PE",
    "quebec": "QC", "québec": "QC", "qc": "QC", "que": "QC", "saskatchewan": "SK", "sk": "SK",
    "yukon": "YT", "yt": "YT",
}
STREET_ABBREV = {
    "st": "street", "str": "street", "rue": "street", "ave": "avenue", "av": "avenue", "blvd": "boulevard",
    "boul": "boulevard", "bd": "boulevard", "rd": "road", "dr": "drive", "ln": "lane", "ct": "court",
    "cres": "crescent", "cr": "crescent", "hwy": "highway", "pkwy": "parkway", "pl": "place", "sq": "square",
    "terr": "terrace", "cir": "circle", "n": "north", "s": "south", "e": "east", "w": "west",
    "ne": "northeast", "nw": "northwest", "se": "southeast", "sw": "southwest",
}
UNIT_RE = re.compile(r"(?:\b(?:suite|ste|unit|apt|apartment|bureau|local|#)\s*#?\s*([a-z0-9-]+))", re.I)
POSTAL_RE = re.compile(r"^([A-Za-z]\d[A-Za-z])\s?-?\s?(\d[A-Za-z]\d)$")


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def _words(text: str) -> list[str]:
    text = strip_accents(text).lower().replace("&", " and ")
    text = re.sub(r"['’`]", "", text)
    return re.findall(r"[a-z0-9]+", text)


def name_tokens(name: str) -> list[str]:
    """Significant tokens: legal suffixes and leading articles dropped, 'and' kept out of comparisons."""
    words = _words(name)
    while words and words[0] in LEADING_ARTICLES and len(words) > 1:
        words.pop(0)
    while len(words) > 1 and words[-1] in LEGAL_SUFFIXES:
        words.pop()
    return [w for w in words if w != "and"] or words


def name_key(name: str) -> str:
    return " ".join(name_tokens(name))


def registered_domain(url_or_domain: str) -> str:
    """'https://www.shop.maple.co.uk/x' -> 'maple.co.uk'; social/marketplace hosts -> ''."""
    raw = (url_or_domain or "").strip().lower()
    if not raw:
        return ""
    if "@" in raw and "//" not in raw:
        raw = raw.rsplit("@", 1)[1]
    if "//" not in raw:
        raw = "//" + raw
    host = (urlsplit(raw).hostname or "").strip(".")
    if not host or "." not in host:
        return ""
    labels = host.split(".")
    if labels[0] == "www":
        labels = labels[1:]
    keep = 3 if len(labels) >= 3 and labels[-2] in SECOND_LEVEL and len(labels[-1]) == 2 and labels[-1] != "ca" else 2
    domain = ".".join(labels[-keep:])
    if domain in SOCIAL_OR_MARKETPLACE or ".".join(labels[-2:]) in SOCIAL_OR_MARKETPLACE:
        return ""
    return domain


def phone_digits(phone: str) -> str:
    """NANP 10-digit form; extensions after x/ext are ignored. Unusable numbers -> ''."""
    text = re.split(r"(?i)\b(?:x|ext\.?|poste)\b", phone or "")[0]
    digits = re.sub(r"\D", "", text)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits if len(digits) == 10 and digits[0] not in "01" else ""


def normalize_email(email: str) -> str:
    value = (email or "").strip().lower()
    return value if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value) else ""


def postal_code(value: str) -> str:
    match = POSTAL_RE.match((value or "").strip())
    return (match.group(1) + match.group(2)).upper() if match else ""


def province_code(value: str) -> str:
    return PROVINCES.get(strip_accents((value or "").strip().lower()).replace(".", ""), "") or PROVINCES.get((value or "").strip().lower(), "")


def street_parts(address: str) -> tuple[str, str]:
    """Return (canonical street line, unit). Street keeps number + expanded abbreviations."""
    text = strip_accents(address or "").lower()
    unit_match = UNIT_RE.search(text)
    unit = unit_match.group(1) if unit_match else ""
    text = UNIT_RE.sub(" ", text)
    segments = [seg for seg in text.split(",") if seg.strip()]
    text = next((seg for seg in segments if re.match(r"\s*\d", seg)), segments[0] if segments else "")
    leading_unit = re.match(r"\s*(\d+[a-z]?)\s*-\s*(\d+)\b", text)
    if leading_unit:
        unit = unit or leading_unit.group(1)
        text = re.sub(r"^\s*\d+[a-z]?\s*-\s*", "", text)
    words = re.findall(r"[a-z0-9]+", text)
    words = [STREET_ABBREV.get(w, w) for w in words]
    words = [w for w in words if w not in {"the"}]
    return " ".join(words), unit
