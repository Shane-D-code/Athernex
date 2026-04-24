"""Language detection and selection package."""

from .detector import LanguageDetector, LanguageStats, DominantLanguageResult

# Try to import trained detector (always available)
try:
    from .trained_detector import (
        TrainedLanguageDetector,
        get_trained_detector,
    )
    _TRAINED_AVAILABLE = True
except ImportError:
    _TRAINED_AVAILABLE = False

# Try to import fastText components (optional dependency)
try:
    from .fasttext_detector import (
        FastTextLanguageDetector,
        LanguageDetectionResult,
        get_detector,
        detect_language,
        FASTTEXT_AVAILABLE,
    )
    from .hybrid_detector import (
        HybridLanguageDetector,
        HybridLanguageResult,
        get_hybrid_detector,
    )
    _FASTTEXT_AVAILABLE = True
except ImportError:
    _FASTTEXT_AVAILABLE = False

__all__ = [
    "LanguageDetector",
    "LanguageStats",
    "DominantLanguageResult",
]

# Add trained detector exports if available
if _TRAINED_AVAILABLE:
    __all__.extend([
        "TrainedLanguageDetector",
        "get_trained_detector",
    ])

# Add fastText exports if available
if _FASTTEXT_AVAILABLE:
    __all__.extend([
        "FastTextLanguageDetector",
        "LanguageDetectionResult",
        "get_detector",
        "detect_language",
        "HybridLanguageDetector",
        "HybridLanguageResult",
        "get_hybrid_detector",
        "FASTTEXT_AVAILABLE",
    ])

