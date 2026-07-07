"""Entry point: `python3 src/main.py diff <old> <new>` or `... history <path>`."""
import sys

from cli import main

if __name__ == "__main__":
    sys.exit(main())
