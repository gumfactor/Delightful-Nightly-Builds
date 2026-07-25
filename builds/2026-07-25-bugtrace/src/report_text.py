"""Terminal report rendering."""

from . import store
from .classify import CATEGORY_LABELS


def render_text(conn):
    counts = store.category_counts(conn)
    total = sum(c["count"] for c in counts)
    lines = [f"BugTrace — {total} classified fix commit(s)", ""]

    if not counts:
        lines.append("No fix commits recorded yet. Run `sync` first.")
        return "\n".join(lines)

    lines.append("Recurring bug patterns, most frequent first:")
    for entry in counts:
        pct = (entry["count"] / total * 100) if total else 0.0
        label = CATEGORY_LABELS.get(entry["category"], entry["category"])
        lines.append(f"  {label:<28} {entry['count']:>4}  ({pct:5.1f}%)")

    repos = store.repo_counts(conn)
    lines.append("")
    lines.append("By repo:")
    for entry in repos:
        lines.append(f"  {entry['repo']:<40} {entry['count']:>4}")

    return "\n".join(lines)
