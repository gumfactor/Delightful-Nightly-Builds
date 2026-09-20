"""Cross-references parsed reviewer comments against parsed author responses."""

from __future__ import annotations

from dataclasses import dataclass, field

from .parser import Comment


@dataclass(frozen=True)
class CompletenessReport:
    total: int
    addressed: int
    missing: list[str] = field(default_factory=list)
    orphaned: list[str] = field(default_factory=list)

    @property
    def percentage(self) -> int:
        if self.total == 0:
            return 0
        return round(self.addressed / self.total * 100)

    @property
    def is_complete(self) -> bool:
        return not self.missing


def match(comments: list[Comment], responses: dict[str, str]) -> CompletenessReport:
    """Compute which comments are addressed, missing a response, or orphaned.

    - ``missing``: comment IDs with no corresponding response.
    - ``orphaned``: response keys that don't match any parsed comment
      (usually a renumbering mistake — surfaced as a warning, not fatal).
    """
    comment_ids = {c.id for c in comments}
    response_ids = set(responses.keys())

    missing = sorted(comment_ids - response_ids, key=_sort_key)
    orphaned = sorted(response_ids - comment_ids, key=_sort_key)
    addressed = len(comment_ids) - len(missing)

    return CompletenessReport(
        total=len(comment_ids),
        addressed=addressed,
        missing=missing,
        orphaned=orphaned,
    )


def _sort_key(comment_id: str) -> tuple[int, int]:
    # comment_id is always "R{n}C{m}" — sort numerically, not lexicographically,
    # so R2C1 doesn't sort before R10C1.
    reviewer_part, comment_part = comment_id[1:].split("C")
    return (int(reviewer_part), int(comment_part))
