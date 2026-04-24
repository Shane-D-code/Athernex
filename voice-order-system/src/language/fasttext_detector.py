"""
fastText-based Language Detection with Hinglish/Code-mix Support.

Uses Facebook's fastText lid.176.bin model for accurate language detection
on short utterances (3-8 words). Handles pure languages and code-mixed speech.

Task 1: Replace/augment current language detector with fastText.
"""

import logging
import os
from dataclasses import dataclass
from typing import Optional, List, Tuple
import re

logger = logging.getLogger(__name__)

# Try to import fasttext
try:
    import fasttext
    FASTTEXT_AVAILABLE = True
except ImportError:
    FASTTEXT_AVAILABLE = False
    logger.warning("fasttext not installed. Run: pip install fasttext")


@dataclass
class LanguageDetectionResult:
    """Result of language detection."""
    lang: str  # "hi" | "en" | "kn" | "mr" | "hinglish"
    confidence: float  # 0.0 - 1.0
    is_code_mixed: bool
    all_predictions: List[Tuple[str, float]]  # [(lang, confidence), ...]
    raw_text: str


class FastTextLanguageDetector:
    """
    fastText-based language detector optimized for Indian languages.
    
    Features:
    - Detects Hindi, English, Kannada, Marathi
    - Identifies Hinglish/code-mixed speech
    - Handles short utterances (3-8 words)
    - Confidence-based fallback to "hinglish" label
    """

    # Language code mapping (fastText uses __label__ prefix)
    LANG_MAP = {
        "__label__hi": "hi",  # Hindi
        "__label__en": "en",  # English
        "__label__kn": "kn",  # Kannada
        "__label__mr": "mr",  # Marathi
    }

    # Reverse mapping
    LANG_CODES = {"hi", "en", "kn", "mr", "hinglish"}

    # Threshold for considering speech as code-mixed
    CODE_MIX_THRESHOLD = 0.75

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize fastText language detector.

        Args:
            model_path: Path to lid.176.bin model. If None, uses default location.
        """
        if not FASTTEXT_AVAILABLE:
            raise ImportError(
                "fasttext not installed. Install with: pip install fasttext"
            )

        # Default model path
        if model_path is None:
            model_path = os.path.expanduser("~/.fasttext/lid.176.bin")

        self.model_path = model_path
        self.model = None
        self._load_model()

        logger.info("FastTextLanguageDetector initialized with model: %s", model_path)

    def _load_model(self):
        """Load the fastText model."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"fastText model not found at {self.model_path}\n"
                f"Download with:\n"
                f"  mkdir -p ~/.fasttext\n"
                f"  wget -O ~/.fasttext/lid.176.bin https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
            )

        # Suppress fastText warnings
        fasttext.FastText.eprint = lambda x: None
        
        self.model = fasttext.load_model(self.model_path)
        logger.info("fastText model loaded successfully")

    def detect_language(self, text: str, k: int = 3) -> LanguageDetectionResult:
        """
        Detect language of input text.

        Args:
            text: Input text (transcribed utterance)
            k: Number of top predictions to return (default 3)

        Returns:
            LanguageDetectionResult with detected language and confidence
        """
        if not text or not text.strip():
            return LanguageDetectionResult(
                lang="en",
                confidence=0.0,
                is_code_mixed=False,
                all_predictions=[],
                raw_text=text,
            )

        # Preprocess text
        cleaned_text = self._preprocess_text(text)

        # Get predictions
        labels, scores = self.model.predict(cleaned_text, k=k)

        # Convert to readable format
        predictions = []
        for label, score in zip(labels, scores):
            lang_code = self.LANG_MAP.get(label, label.replace("__label__", ""))
            predictions.append((lang_code, float(score)))

        # Determine primary language
        primary_lang, primary_conf = predictions[0]

        # Check for code-mixing (Hinglish detection)
        is_code_mixed, final_lang = self._detect_code_mixing(
            text, predictions, primary_lang, primary_conf
        )

        logger.debug(
            "Language detected: %s (conf=%.3f, code_mixed=%s) for text: '%s'",
            final_lang, primary_conf, is_code_mixed, text[:50]
        )

        return LanguageDetectionResult(
            lang=final_lang,
            confidence=primary_conf,
            is_code_mixed=is_code_mixed,
            all_predictions=predictions,
            raw_text=text,
        )

    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for fastText.
        
        fastText expects lowercase, single-line text.
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Convert to lowercase (fastText model is case-insensitive)
        text = text.lower()
        
        # Remove special characters that might confuse the model
        text = re.sub(r'[^\w\s\u0900-\u097F\u0C80-\u0CFF\u0900-\u097F]', ' ', text)
        
        return text

    def _detect_code_mixing(
        self,
        text: str,
        predictions: List[Tuple[str, float]],
        primary_lang: str,
        primary_conf: float,
    ) -> Tuple[bool, str]:
        """
        Detect if text is code-mixed (Hinglish).

        Logic:
        1. If confidence < 0.75 on primary language → likely code-mixed
        2. If top 2 languages are Hindi + English with close scores → Hinglish
        3. Check for script mixing (Devanagari + Latin)

        Returns:
            (is_code_mixed, final_lang)
        """
        # Rule 1: Low confidence indicates code-mixing
        if primary_conf < self.CODE_MIX_THRESHOLD:
            # Check if it's Hindi-English mix
            lang_set = {lang for lang, _ in predictions[:2]}
            if {"hi", "en"}.issubset(lang_set):
                return True, "hinglish"
            # Other code-mix scenarios
            return True, primary_lang

        # Rule 2: Check for Hindi-English balance
        if len(predictions) >= 2:
            lang1, conf1 = predictions[0]
            lang2, conf2 = predictions[1]
            
            # If Hindi and English are both present with close scores
            if {lang1, lang2} == {"hi", "en"}:
                score_diff = abs(conf1 - conf2)
                if score_diff < 0.25:  # Within 25% of each other
                    return True, "hinglish"

        # Rule 3: Script mixing detection
        has_devanagari = bool(re.search(r'[\u0900-\u097F]', text))
        has_latin = bool(re.search(r'[a-zA-Z]', text))
        
        if has_devanagari and has_latin:
            # Check word-level mixing
            words = text.split()
            if len(words) >= 3:  # Only for utterances with 3+ words
                devanagari_words = sum(1 for w in words if re.search(r'[\u0900-\u097F]', w))
                latin_words = sum(1 for w in words if re.search(r'[a-zA-Z]', w))
                
                # If both scripts are significantly present
                if devanagari_words > 0 and latin_words > 0:
                    return True, "hinglish"

        # Not code-mixed
        return False, primary_lang

    def detect_language_batch(self, texts: List[str]) -> List[LanguageDetectionResult]:
        """
        Detect language for multiple texts efficiently.

        Args:
            texts: List of input texts

        Returns:
            List of LanguageDetectionResult
        """
        return [self.detect_language(text) for text in texts]


# Convenience function for quick detection
def detect_language(text: str, model_path: Optional[str] = None) -> LanguageDetectionResult:
    """
    Quick language detection function.

    Args:
        text: Input text
        model_path: Optional path to fastText model

    Returns:
        LanguageDetectionResult
    """
    detector = FastTextLanguageDetector(model_path=model_path)
    return detector.detect_language(text)


# Singleton instance for reuse
_detector_instance: Optional[FastTextLanguageDetector] = None


def get_detector(model_path: Optional[str] = None) -> FastTextLanguageDetector:
    """
    Get or create singleton detector instance.

    Args:
        model_path: Optional path to fastText model

    Returns:
        FastTextLanguageDetector instance
    """
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = FastTextLanguageDetector(model_path=model_path)
    return _detector_instance
