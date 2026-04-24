"""Language detection and selection package."""

from .detector import LanguageDetector, LanguageStats, DominantLanguageResult

__all__ = [
    "LanguageDetector",
    "LanguageStats",
    "DominantLanguageResult",
]
