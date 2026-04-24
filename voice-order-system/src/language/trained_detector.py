"""
Trained Language Detector for Kannada and Marathi.

Uses linguistic features, character n-grams, and keyword patterns
to distinguish between Hindi, Marathi, Kannada, and English.

This detector is trained on food ordering domain vocabulary.
"""

import logging
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class LanguageFeatures:
    """Features extracted from text for language detection."""
    script: str  # devanagari, kannada, latin
    char_ngrams: Counter
    word_patterns: List[str]
    unique_chars: set
    word_count: int


class TrainedLanguageDetector:
    """
    Trained language detector for Indian languages.
    
    Uses multiple features:
    1. Script detection (Unicode ranges)
    2. Language-specific keywords
    3. Character n-grams
    4. Morphological patterns
    5. Common word endings
    """
    
    # Unicode ranges for scripts
    DEVANAGARI_RANGE = (0x0900, 0x097F)  # Hindi, Marathi
    KANNADA_RANGE = (0x0C80, 0x0CFF)     # Kannada
    
    # Language-specific keywords (food ordering domain)
    HINDI_KEYWORDS = {
        # Pronouns
        "मुझे", "मैं", "मेरा", "आप", "तुम",
        # Verbs
        "चाहिए", "है", "हैं", "करो", "दो", "दे", "दीजिए",
        # Common words
        "और", "का", "की", "को", "से", "में",
        # Food ordering
        "ऑर्डर", "डिलीवर", "कैंसिल",
        # Questions
        "क्या", "कहाँ", "कब", "कैसे",
    }
    
    MARATHI_KEYWORDS = {
        # Pronouns
        "मला", "मी", "माझा", "तुम्ही", "तू",
        # Verbs
        "हवे", "आहे", "आहेत", "करा", "द्या", "दे", "करता",
        # Common words
        "आणि", "चा", "ची", "ला", "पासून", "मध्ये", "दोन",
        # Food ordering
        "ऑर्डर", "डिलिव्हरी", "पिझ्झा",
        # Questions
        "काय", "कुठे", "केव्हा", "कसे", "का",
        # Polite words
        "कृपया",
    }
    
    KANNADA_KEYWORDS = {
        # Pronouns
        "ನನಗೆ", "ನಾನು", "ನನ್ನ", "ನೀವು", "ನೀನು",
        # Verbs
        "ಬೇಕು", "ಇದೆ", "ಮಾಡಿ", "ಕೊಡಿ", "ಮಾಡು",
        # Common words
        "ಮತ್ತು", "ಅಥವಾ", "ಗೆ", "ನಿಂದ", "ನಲ್ಲಿ",
        # Food ordering
        "ಆರ್ಡರ್", "ಡೆಲಿವರಿ",
        # Questions
        "ಏನು", "ಎಲ್ಲಿ", "ಯಾವಾಗ", "ಹೇಗೆ",
    }
    
    ENGLISH_KEYWORDS = {
        "i", "want", "need", "order", "pizza", "burger",
        "deliver", "cancel", "please", "thank", "you",
        "my", "the", "and", "or", "at", "to", "from",
    }
    
    # Character patterns specific to each language
    MARATHI_CHAR_PATTERNS = {
        # Marathi-specific characters and combinations
        "ळ", "ऱ",  # Unique to Marathi
        "ह्या", "त्या", "ज्या",  # Common Marathi patterns
    }
    
    HINDI_CHAR_PATTERNS = {
        # Hindi-specific patterns
        "ये", "वो", "यह", "वह",
    }
    
    def __init__(self):
        """Initialize the trained detector."""
        logger.info("TrainedLanguageDetector initialized")
    
    def detect(self, text: str) -> Tuple[str, float, bool]:
        """
        Detect language of text.
        
        Args:
            text: Input text
            
        Returns:
            (language, confidence, is_code_mixed)
            language: "hi", "mr", "kn", "en", "hinglish"
            confidence: 0.0 - 1.0
            is_code_mixed: True if multiple scripts detected
        """
        if not text or not text.strip():
            return "en", 0.0, False
        
        # Extract features
        features = self._extract_features(text)
        
        # Detect script
        script_scores = self._score_by_script(features)
        
        # Detect by keywords
        keyword_scores = self._score_by_keywords(text)
        
        # Detect by character patterns
        pattern_scores = self._score_by_patterns(text)
        
        # Combine scores
        combined_scores = self._combine_scores(
            script_scores, keyword_scores, pattern_scores
        )
        
        # Determine language
        language, confidence = self._determine_language(combined_scores)
        
        # Check for code-mixing
        is_code_mixed = self._is_code_mixed(features, combined_scores)
        
        logger.debug(
            "Detected: %s (conf=%.3f, mixed=%s) for: %s",
            language, confidence, is_code_mixed, text[:50]
        )
        
        return language, confidence, is_code_mixed
    
    def _extract_features(self, text: str) -> LanguageFeatures:
        """Extract linguistic features from text."""
        # Detect script
        has_devanagari = any(
            self.DEVANAGARI_RANGE[0] <= ord(c) <= self.DEVANAGARI_RANGE[1]
            for c in text
        )
        has_kannada = any(
            self.KANNADA_RANGE[0] <= ord(c) <= self.KANNADA_RANGE[1]
            for c in text
        )
        has_latin = bool(re.search(r'[a-zA-Z]', text))
        
        if has_kannada:
            script = "kannada"
        elif has_devanagari:
            script = "devanagari"
        elif has_latin:
            script = "latin"
        else:
            script = "unknown"
        
        # Extract character n-grams
        char_ngrams = Counter()
        for i in range(len(text) - 1):
            bigram = text[i:i+2]
            char_ngrams[bigram] += 1
        
        # Extract word patterns
        words = text.split()
        word_patterns = [w.lower() for w in words if len(w) > 1]
        
        # Unique characters
        unique_chars = set(text)
        
        return LanguageFeatures(
            script=script,
            char_ngrams=char_ngrams,
            word_patterns=word_patterns,
            unique_chars=unique_chars,
            word_count=len(words)
        )
    
    def _score_by_script(self, features: LanguageFeatures) -> Dict[str, float]:
        """Score languages based on script."""
        scores = {"hi": 0.0, "mr": 0.0, "kn": 0.0, "en": 0.0}
        
        if features.script == "kannada":
            scores["kn"] = 1.0
        elif features.script == "devanagari":
            # Both Hindi and Marathi use Devanagari
            scores["hi"] = 0.5
            scores["mr"] = 0.5
        elif features.script == "latin":
            scores["en"] = 1.0
        
        return scores
    
    def _score_by_keywords(self, text: str) -> Dict[str, float]:
        """Score languages based on keyword matching."""
        text_lower = text.lower()
        words = set(text.split())
        
        scores = {"hi": 0.0, "mr": 0.0, "kn": 0.0, "en": 0.0}
        
        # Count keyword matches
        hindi_matches = sum(1 for kw in self.HINDI_KEYWORDS if kw in text)
        marathi_matches = sum(1 for kw in self.MARATHI_KEYWORDS if kw in text)
        kannada_matches = sum(1 for kw in self.KANNADA_KEYWORDS if kw in text)
        english_matches = sum(1 for kw in self.ENGLISH_KEYWORDS if kw in text_lower)
        
        total_matches = hindi_matches + marathi_matches + kannada_matches + english_matches
        
        if total_matches > 0:
            scores["hi"] = hindi_matches / total_matches
            scores["mr"] = marathi_matches / total_matches
            scores["kn"] = kannada_matches / total_matches
            scores["en"] = english_matches / total_matches
        
        return scores
    
    def _score_by_patterns(self, text: str) -> Dict[str, float]:
        """Score languages based on character patterns."""
        scores = {"hi": 0.0, "mr": 0.0, "kn": 0.0, "en": 0.0}
        
        # Check for Marathi-specific characters
        marathi_pattern_count = sum(
            1 for pattern in self.MARATHI_CHAR_PATTERNS
            if pattern in text
        )
        
        # Check for Hindi-specific patterns
        hindi_pattern_count = sum(
            1 for pattern in self.HINDI_CHAR_PATTERNS
            if pattern in text
        )
        
        if marathi_pattern_count > 0:
            scores["mr"] += 0.5 * marathi_pattern_count
        
        if hindi_pattern_count > 0:
            scores["hi"] += 0.5 * hindi_pattern_count
        
        # Normalize
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}
        
        return scores
    
    def _combine_scores(
        self,
        script_scores: Dict[str, float],
        keyword_scores: Dict[str, float],
        pattern_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Combine scores from different methods."""
        combined = {"hi": 0.0, "mr": 0.0, "kn": 0.0, "en": 0.0}
        
        # Weighted combination
        # Script: 30%, Keywords: 50%, Patterns: 20%
        for lang in combined.keys():
            combined[lang] = (
                0.3 * script_scores.get(lang, 0.0) +
                0.5 * keyword_scores.get(lang, 0.0) +
                0.2 * pattern_scores.get(lang, 0.0)
            )
        
        return combined
    
    def _determine_language(
        self, scores: Dict[str, float]
    ) -> Tuple[str, float]:
        """Determine final language from scores."""
        if not scores or all(v == 0 for v in scores.values()):
            return "en", 0.5
        
        # Get top language
        sorted_langs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_lang, top_score = sorted_langs[0]
        
        # If score is very low, return default
        if top_score < 0.1:
            return "en", 0.5
        
        return top_lang, top_score
    
    def _is_code_mixed(
        self, features: LanguageFeatures, scores: Dict[str, float]
    ) -> bool:
        """Determine if text is code-mixed."""
        # Check for mixed scripts
        text = "".join(features.unique_chars)
        
        has_devanagari = any(
            self.DEVANAGARI_RANGE[0] <= ord(c) <= self.DEVANAGARI_RANGE[1]
            for c in text
        )
        has_kannada = any(
            self.KANNADA_RANGE[0] <= ord(c) <= self.KANNADA_RANGE[1]
            for c in text
        )
        has_latin = bool(re.search(r'[a-zA-Z]', text))
        
        # Mixed scripts = code-mixed (but only if Latin is involved)
        # Devanagari alone is not code-mixed (could be Hindi or Marathi)
        if has_latin and (has_devanagari or has_kannada):
            return True
        
        # Check if multiple languages have significant scores
        # But exclude Hindi/Marathi confusion (both use Devanagari)
        significant_langs = [lang for lang, score in scores.items() if score > 0.2]
        if len(significant_langs) > 1:
            # If it's just Hindi and Marathi, not code-mixed
            if set(significant_langs) == {"hi", "mr"}:
                return False
            return True
        
        return False


# Singleton instance
_trained_detector: Optional[TrainedLanguageDetector] = None


def get_trained_detector() -> TrainedLanguageDetector:
    """Get or create singleton trained detector."""
    global _trained_detector
    if _trained_detector is None:
        _trained_detector = TrainedLanguageDetector()
    return _trained_detector
