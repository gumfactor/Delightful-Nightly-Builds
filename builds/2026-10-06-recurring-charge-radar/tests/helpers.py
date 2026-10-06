import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from recurring.detect import add_months  # noqa: E402
from recurring.models import Transaction  # noqa: E402


def monthly(desc, amount, start=date(2026, 1, 5), count=6, source="t.csv"):
    return [Transaction(add_months(start, i), desc, amount, source) for i in range(count)]
