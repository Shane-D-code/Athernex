"""
Language detection and dominant language selection.

Extracts language information from STT word-level metadata and
determines the dominant language in code-mixed speech.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Optional
from collections import Counter

from stt.base import TranscriptionResult, WordResult

logger = logging.getLogger(__name__)


@dataclass
class LanguageStats:
    """Statistics for a detected language."""
    language: str
    word_count: int
    duration: float  # seconds
    percentage: float


@dataclass
class DominantLanguageResult:
    """Result of dominant language selection."""
    dominant_language: str
    is_code_mixed: bool
    languages: List[LanguageStats]
    ambiguous: bool  # True if languages are within 10% of each other


class LanguageDetector:
    """
    Detects languages in transcribed speech and selects dominant language.
    
    Handles code-mixed speech (multiple languages in one utterance).
    Uses 10% ambiguity rule for close language distributions.
    """

    def __init__(self, ambiguity_threshold: float = 0.10):
        """
        Initialize language detector.

        Args:
            ambiguity_threshold: Threshold for ambiguous language detection (default 10%)
        """
        self.ambiguity_threshold = ambiguity_threshold
        logger.info("LanguageDetector initialized with ambiguity_threshold=%.2f", ambiguity_threshold)

    def detect(self, transcription: TranscriptionResult) -> DominantLanguageResult:
        """
        Detect languages and select dominant language.

        Args:
            transcription: STT transcription result with word-level metadata

        Returns:
            DominantLanguageResult with dominant language and statistics
        """
        if not transcription.words:
            # No word-level data, use overall language
            return DominantLanguageResult(
                dominant_language=transcription.language,
                is_code_mixed=False,
                languages=[LanguageStats(
                    language=transcription.language,
                    word_count=len(transcription.text.split()),
                    duration=transcription.duration,
                    percentage=1.0,
                )],
                ambiguous=False,
            )

        # Extract language statistics from words
        language_stats = self._calculate_language_stats(transcription.words)

        # Determine if code-mixed
        is_code_mixed = len(language_stats) > 1

        # Select dominant language
        dominant_language, ambiguous = self._select_dominant_language(
            language_stats, transcription.words
        )

        logger.debug(
            "Language detection: dominant=%s, code_mixed=%s, ambiguous=%s, languages=%s",
            dominant_language, is_code_mixed, ambiguous,
            [(ls.language, ls.percentage) for ls in language_stats]
        )

        return DominantLanguageResult(
            dominant_language=dominant_language,
            is_code_mixed=is_code_mixed,
            languages=language_stats,
            ambiguous=ambiguous,
        )

    def _calculate_language_stats(self, words: List[WordResult]) -> List[LanguageStats]:
        """Calculate statistics for each detected language."""
        # Count words per language
        language_counts = Counter()
        language_durations = {}

        for word in words:
            lang = word.language or "unknown"
            language_counts[lang] += 1
            
            if lang not in language_durations:
                language_durations[lang] = 0.0
            language_durations[lang] += (word.end - word.start)

        # Calculate percentages
        total_words = sum(language_counts.values())
        
        stats = []
        for lang, count in language_counts.most_common():
            stats.append(LanguageStats(
                language=lang,
                word_count=count,
                duration=language_durations[lang],
                percentage=count / total_words if total_words > 0 else 0.0,
            ))

        return stats

    def _select_dominant_language(
        self, 
        language_stats: List[LanguageStats],
        words: List[WordResult]
    ) -> tuple[str, bool]:
        """
        Select dominant language using word count and duration.
        
        Returns:
            (dominant_language, ambiguous)
        """
        if not language_stats:
            return "unknown", False

        if len(language_stats) == 1:
            return language_stats[0].language, False

        # Sort by word count (primary) and duration (secondary)
        sorted_stats = sorted(
            language_stats,
            key=lambda s: (s.word_count, s.duration),
            reverse=True
        )

        top_lang = sorted_stats[0]
        second_lang = sorted_stats[1] if len(sorted_stats) > 1 else None

        # Check for ambiguity (within 10% difference)
        ambiguous = False
        if second_lang:
            diff = abs(top_lang.percentage - second_lang.percentage)
            ambiguous = diff <= self.ambiguity_threshold

        if ambiguous:
            # Use first-word language as tiebreaker
            first_word_lang = words[0].language if words else top_lang.language
            logger.debug(
                "Ambiguous languages (%.1f%% vs %.1f%%), using first-word language: %s",
                top_lang.percentage * 100, second_lang.percentage * 100, first_word_lang
            )
            return first_word_lang, True

        return top_lang.language, False
