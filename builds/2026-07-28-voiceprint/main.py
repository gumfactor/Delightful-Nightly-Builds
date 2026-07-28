"""Voiceprint entry point. Run: python main.py analyze <file>"""

import sys

from src.cli import main

if __name__ == "__main__":
    sys.exit(main())
