"""AMA (JAMA) 11th Edition reference-list and in-text citation formatting."""

from __future__ import annotations

from ..models import Reference
from ..names import format_authors_ama
from . import _numbered_common


def format_reference(ref: Reference) -> str:
    return _numbered_common.build_reference(ref, format_authors_ama)


def format_in_text(ref: Reference, index: int) -> str:
    return _numbered_common.format_in_text(index)
