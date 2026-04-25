"""
Run brutal comprehensive tests with proper path setup.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Now run pytest
import pytest

if __name__ == "__main__":
    args = [
        "tests/test_brutal_comprehensive.py",
        "-v",
        "--tb=short",
        "--maxfail=50",
        "-x",  # Stop on first failure for debugging
    ]
    sys.exit(pytest.main(args))
