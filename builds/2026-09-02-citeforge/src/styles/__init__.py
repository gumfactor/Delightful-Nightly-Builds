"""Citation style formatting engines. Each module exposes:

- format_reference(ref) -> str   the reference-list entry
- format_in_text(ref, index) -> str   an in-text citation marker

`index` is the reference's 1-based position in the library, used as the
numbered-citation marker for AMA/Vancouver (which cite by citation order,
not by author name).
"""

from . import ama, apa, chicago, vancouver

STYLES = {
    "apa": apa,
    "ama": ama,
    "vancouver": vancouver,
    "chicago": chicago,
}

STYLE_LABELS = {
    "apa": "APA 7th Edition",
    "ama": "AMA 11th Edition",
    "vancouver": "Vancouver / ICMJE",
    "chicago": "Chicago Author-Date 17th Edition",
}
