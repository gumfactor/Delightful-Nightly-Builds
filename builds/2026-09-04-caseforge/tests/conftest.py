import os
import sys

# Allow "from src import ..." style imports when pytest is run from the
# build folder root (python -m pytest tests/ -v).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
