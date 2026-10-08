import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lookalike.schema import Record  # noqa: E402


def rec(rid: str, **fields: str) -> Record:
    return Record.build(rid, "batch", fields, {})
