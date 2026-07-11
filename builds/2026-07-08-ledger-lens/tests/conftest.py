import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture
def sample_csv_path():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_transactions.csv"
    )
