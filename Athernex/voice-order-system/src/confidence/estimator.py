"""
Confidence Estimation Module (CEM).

Extracts and analyzes confidence scores from STT output.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from stt.base import TranscriptionResult, WordResult

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceMetadata:
    """Confidence metadata for downstream components."""
    utterance_confidence: float
    word_confidences: List[float]
    low_confidence_words: List[str]
    min_word_confidence: float
    has_low_confidence_words: bool


class ConfidenceEstimationModule:
    """
    Extracts and analyzes confidence scores from STT output.
    
    Calculates utterance-level confidence and identifies low-confidence words.
    """

    def __init__(self, low_confidence_threshold: float = 0.4):
        """
        Initialize CEM.

        Args:
            low_confidence_threshold: Threshold below which words are flagged
        """
        self.low_confidence_threshold = low_confidence_threshold
        logger.info("CEM initialized with threshold=%.2f", low_confidence_threshold)

    def analyze(self, transcription: TranscriptionResult) -> ConfidenceMetadata:
        """
        Analyze transcription and extract confidence metadata.

        Args:
            transcription: STT transcription result

        Returns:
            ConfidenceMetadata with analysis results
        """
        if not transcription.words:
            # No word-level data, use overall confidence
            return ConfidenceMetadata(
                utterance_confidence=transcription.confidence,
                word_confidences=[],
                low_confidence_words=[],
                min_word_confidence=transcription.confidence,
                has_low_confidence_words=False,
            )

        # Extract word confidences
        word_confidences = [w.confidence for w in transcription.words]
        
        # Calculate utterance-level confidence (mean of word confidences)
        utterance_confidence = sum(word_confidences) / len(word_confidences)

        # Identify low-confidence words
        low_confidence_words = [
            w.word for w in transcription.words
            if w.confidence < self.low_confidence_threshold
        ]

        min_word_confidence = min(word_confidences) if word_confidences else 0.0

        metadata = ConfidenceMetadata(
            utterance_confidence=utterance_confidence,
            word_confidences=word_confidences,
            low_confidence_words=low_confidence_words,
            min_word_confidence=min_word_confidence,
            has_low_confidence_words=len(low_confidence_words) > 0,
        )

        if metadata.has_low_confidence_words:
            logger.debug(
                "Low confidence words detected: %s (min=%.2f)",
                low_confidence_words, min_word_confidence
            )

        return metadata
