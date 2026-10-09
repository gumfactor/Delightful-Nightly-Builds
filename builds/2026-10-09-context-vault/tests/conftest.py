import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ctxvault import store  # noqa: E402
from ctxvault.demo import write_demo  # noqa: E402


def write_jsonl(path: Path, records: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(r if isinstance(r, str) else json.dumps(r) for r in records) + "\n")


@pytest.fixture
def src(tmp_path):
    root = tmp_path / "projects"
    write_demo(root)
    return root


@pytest.fixture
def conn(src):
    connection = store.connect(":memory:")
    store.index_directory(connection, src)
    return connection
