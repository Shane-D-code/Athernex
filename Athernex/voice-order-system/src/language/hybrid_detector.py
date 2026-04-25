"""
Hybrid Language Detector - Combines fastText with STT word-level metadata.

Provides best-of-both-worlds:
- fastText for accurate text-based detection
- STT word metadata for code-mix validation
- Fallback to original detector if fastText unavailable

Integration point: STT output → detect_language(text) → route to LLM
"""

import logging
from typing import Optional
from dataclasses import dataclass

from stt.base import TranscriptionResult
from language.detector import LanguageDetector, DominantLanguageResult

logger = logging.getLogger(__name__)

# Try to import fastText detector
try:
    from language.fasttext_detector import (
        FastTextLanguageDetector,
        LanguageDetectionResult,
        FASTTEXT_AVAILABLE,
    )
except ImportError:
    FASTTEXT_AVAILABLE = False
    logger.warning("fastText detector not available, using fallback")

# Import trained detector for Devanagari disambiguation
try:
    from language.trained_detector import get_trained_detector
    TRAINED_DETECTOR_AVAILABLE = True
except ImportError:
    TRAINED_DETECTOR_AVAILABLE = False
    logger.warning("Trained detector not available")


@dataclass
class HybridLanguageResult:
    """Combined result from hybrid detection."""
    language: str  # "hi" | "en" | "kn" | "mr" | "hinglish"
    confidence: float
    is_code_mixed: bool
    method: str  # "fasttext" | "stt_metadata" | "fallback"
    fasttext_result: Optional[any] = None
    stt_result: Optional[DominantLanguageResult] = None


class HybridLanguageDetector:
    """
    Hybrid language detector combining fastText and STT metadata.
    
    Strategy:
    1. If fastText available: Use it as primary detector
    2. If STT has word-level language data: Use it for validation
    3. Fallback to STT-only detection if fastText unavailable
    
    Benefits:
    - fastText: Better accuracy on short utterances
    - STT metadata: Validates code-mixing at word level
    - Graceful degradation: Works without fastText
    """

    def __init__(self, fasttext_model_path: Optional[str] = None):
        """
        Initialize hybrid detector.

        Args:
            fasttext_model_path: Optional path to fastText model
        """
        self.stt_detector = LanguageDetector()
        self.fasttext_detector = None
        self.trained_detector = None
        
        if FASTTEXT_AVAILABLE:
            try:
                self.fasttext_detector = FastTextLanguageDetector(
                    model_path=fasttext_model_path
                )
                logger.info("HybridLanguageDetector: fastText enabled")
            except Exception as e:
                logger.warning("Failed to load fastText: %s", e)
                self.fasttext_detector = None
        else:
            logger.info("HybridLanguageDetector: fastText not available, using STT-only")
        
        # Initialize trained detector for Devanagari disambiguation
        if TRAINED_DETECTOR_AVAILABLE:
            try:
                self.trained_detector = get_trained_detector()
                logger.info("HybridLanguageDetector: Trained detector enabled for Hindi/Marathi disambiguation")
            except Exception as e:
                logger.warning("Failed to load trained detector: %s", e)
                self.trained_detector = None

    def detect(
        self,
        transcription: TranscriptionResult,
        use_fasttext: bool = True,
    ) -> HybridLanguageResult:
        """
        Detect language using hybrid approach.

        Args:
            transcription: STT transcription result
            use_fasttext: Whether to use fastText (default True)

        Returns:
            HybridLanguageResult with detected language
        """
        text = transcription.text

        # Strategy 1: fastText detection (if available and enabled)
        if use_fasttext and self.fasttext_detector:
            return self._detect_with_fasttext(transcription)

        # Strategy 2: STT metadata detection (fallback)
        return self._detect_with_stt_metadata(transcription)

    def _detect_with_fasttext(
        self, transcription: TranscriptionResult
    ) -> HybridLanguageResult:
        """Detect using fastText with STT validation."""
        text = transcription.text
        
        # Get fastText prediction
        ft_result = self.fasttext_detector.detect_language(text)
        
        # Validate with STT metadata if available
        if transcription.words:
            stt_result = self.stt_detector.detect(transcription)
            
            # Cross-validate code-mixing
            is_code_mixed = ft_result.is_code_mixed or stt_result.is_code_mixed
            
            # If both agree on code-mixing, high confidence
            if ft_result.is_code_mixed and stt_result.is_code_mixed:
                confidence = min(1.0, ft_result.confidence + 0.1)
            else:
                confidence = ft_result.confidence
            
            logger.debug(
                "Hybrid detection: fastText=%s (%.3f), STT=%s, code_mixed=%s",
                ft_result.lang, ft_result.confidence,
                stt_result.dominant_language, is_code_mixed
            )
            
            return HybridLanguageResult(
                language=ft_result.lang,
                confidence=confidence,
                is_code_mixed=is_code_mixed,
                method="fasttext",
                fasttext_result=ft_result,
                stt_result=stt_result,
            )
        
        # No STT metadata, use fastText only
        return HybridLanguageResult(
            language=ft_result.lang,
            confidence=ft_result.confidence,
            is_code_mixed=ft_result.is_code_mixed,
            method="fasttext",
            fasttext_result=ft_result,
            stt_result=None,
        )

    def _detect_with_stt_metadata(
        self, transcription: TranscriptionResult
    ) -> HybridLanguageResult:
        """Detect using STT metadata only (fallback)."""
        stt_result = self.stt_detector.detect(transcription)
        
        # Map to standard format
        language = stt_result.dominant_language
        
        # Estimate confidence from STT
        if stt_result.languages:
            confidence = stt_result.languages[0].percentage
        else:
            confidence = transcription.language_probability
        
        logger.debug(
            "Fallback detection: STT=%s (%.3f), code_mixed=%s",
            language, confidence, stt_result.is_code_mixed
        )
        
        return HybridLanguageResult(
            language=language,
            confidence=confidence,
            is_code_mixed=stt_result.is_code_mixed,
            method="stt_metadata",
            fasttext_result=None,
            stt_result=stt_result,
        )

    def detect_from_text(self, text: str) -> HybridLanguageResult:
        """
        Detect language from text only (no STT metadata).
        
        Useful for text-only inputs or testing.

        Args:
            text: Input text

        Returns:
            HybridLanguageResult
        """
        if self.fasttext_detector:
            ft_result = self.fasttext_detector.detect_language(text)
            return HybridLanguageResult(
                language=ft_result.lang,
                confidence=ft_result.confidence,
                is_code_mixed=ft_result.is_code_mixed,
                method="fasttext",
                fasttext_result=ft_result,
                stt_result=None,
            )
        
        # Use trained detector if available
        if self.trained_detector:
            lang, confidence, is_code_mixed = self.trained_detector.detect(text)
            return HybridLanguageResult(
                language=lang,
                confidence=confidence,
                is_code_mixed=is_code_mixed,
                method="trained",
                fasttext_result=None,
                stt_result=None,
            )
        
        # Fallback: guess based on script
        import re
        has_devanagari = bool(re.search(r'[\u0900-\u097F]', text))
        has_kannada = bool(re.search(r'[\u0C80-\u0CFF]', text))
        has_latin = bool(re.search(r'[a-zA-Z]', text))
        
        if has_devanagari and has_latin:
            language = "hinglish"
            is_code_mixed = True
        elif has_devanagari:
            language = "hi"
            is_code_mixed = False
        elif has_kannada:
            language = "kn"
            is_code_mixed = False
        elif has_latin:
            language = "en"
            is_code_mixed = False
        else:
            language = "en"
            is_code_mixed = False
        
        return HybridLanguageResult(
            language=language,
            confidence=0.5,  # Low confidence for fallback
            is_code_mixed=is_code_mixed,
            method="fallback",
            fasttext_result=None,
            stt_result=None,
        )


# Singleton instance
_hybrid_detector: Optional[HybridLanguageDetector] = None


def get_hybrid_detector(
    fasttext_model_path: Optional[str] = None
) -> HybridLanguageDetector:
    """
    Get or create singleton hybrid detector.

    Args:
        fasttext_model_path: Optional path to fastText model

    Returns:
        HybridLanguageDetector instance
    """
    global _hybrid_detector
    if _hybrid_detector is None:
        _hybrid_detector = HybridLanguageDetector(
            fasttext_model_path=fasttext_model_path
        )
    return _hybrid_detector
