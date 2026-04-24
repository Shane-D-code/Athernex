"""
Server entry point.
Run: python main.py   OR   uvicorn main:app --reload --app-dir src
"""

import sys
import logging
from pathlib import Path

# Add src/ to Python path so all modules resolve correctly
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn
from api.app import app  # noqa: F401 — re-exported for uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8090,
        reload=False,
        log_level="info",
    )
