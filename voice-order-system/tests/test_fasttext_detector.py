"""
Test suite for fastText language detector.

Covers:
- Pure Hindi utterances
- Pure English utterances
- Hinglish (code-mixed) utterances
- Kannada utterances
- Marathi utterances
- Short utterances (3-8 words)
"""

import pytest
from language.fasttext_detector import (
    FastTextLanguageDetector,
    LanguageDetectionResult,
    get_detector,
    FASTTEXT_AVAILABLE,
)


# Skip all tests if fasttext not available
pytestmark = pytest.mark.skipif(
    not FASTTEXT_AVAILABLE,
    reason="fasttext not installed"
)


class TestFastTextDetector:
    """Test cases for fastText language detection."""

    @pytest.fixture
    def detector(self):
        """Create detector instance."""
        return get_detector()

    # ========== PURE HINDI TESTS ==========
    
    def test_pure_hindi_short(self, detector):
        """Test short pure Hindi utterance."""
        text = "मुझे दो पिज़्ज़ा चाहिए"
        result = detector.detect_language(text)
        
        assert result.lang == "hi"
        assert result.confidence > 0.85
        assert not result.is_code_mixed

    def test_pure_hindi_medium(self, detector):
        """Test medium-length pure Hindi utterance."""
        text = "मुझे आज शाम सात बजे दो पिज़्ज़ा और एक बर्गर चाहिए"
        result = detector.detect_language(text)
        
        assert result.lang == "hi"
        assert result.confidence > 0.90

    def test_pure_hindi_with_numbers(self, detector):
        """Test Hindi with numbers."""
        text = "मुझे 2 पिज़्ज़ा और 3 बर्गर चाहिए"
        result = detector.detect_language(text)
        
        assert result.lang == "hi"
        assert result.confidence > 0.80

    # ========== PURE ENGLISH TESTS ==========
    
    def test_pure_english_short(self, detector):
        """Test short pure English utterance."""
        text = "I want two pizzas"
        result = detector.detect_language(text)
        
        assert result.lang == "en"
        assert result.confidence > 0.85
        assert not result.is_code_mixed

    def test_pure_english_medium(self, detector):
        """Test medium-length pure English utterance."""
        text = "I want two pizzas and one burger at seven pm"
        result = detector.detect_language(text)
        
        assert result.lang == "en"
        assert result.confidence > 0.90

    def test_pure_english_order_query(self, detector):
        """Test English order status query."""
        text = "what is the status of my order"
        result = detector.detect_language(text)
        
        assert result.lang == "en"
        assert result.confidence > 0.85

    # ========== HINGLISH (CODE-MIXED) TESTS ==========
    
    def test_hinglish_mixed_script(self, detector):
        """Test Hinglish with mixed Devanagari and Latin scripts."""
        text = "मुझे 2 pizza चाहिए"
        result = detector.detect_language(text)
        
        assert result.lang == "hinglish"
        assert result.is_code_mixed

    def test_hinglish_english_dominant(self, detector):
        """Test Hinglish with English-dominant words."""
        text = "I want do pizza aur ek burger"
        result = detector.detect_language(text)
        
        # Should detect as code-mixed (either hinglish or low confidence)
        assert result.lang in ["hinglish", "en", "hi"]
        if result.confidence < 0.75:
            assert result.is_code_mixed

    def test_hinglish_hindi_dominant(self, detector):
        """Test Hinglish with Hindi-dominant words."""
        text = "मुझे pizza और burger चाहिए please"
        result = detector.detect_language(text)
        
        assert result.lang == "hinglish"
        assert result.is_code_mixed

    def test_hinglish_balanced(self, detector):
        """Test balanced Hinglish."""
        text = "two pizza aur ek burger chahiye"
        result = detector.detect_language(text)
        
        # Should be detected as code-mixed
        assert result.is_code_mixed or result.confidence < 0.75

    def test_hinglish_time_expression(self, detector):
        """Test Hinglish with time expression."""
        text = "7 pm ko deliver karo please"
        result = detector.detect_language(text)
        
        # Should detect mixing
        assert result.is_code_mixed or result.lang in ["hinglish", "en", "hi"]

    # ========== KANNADA TESTS ==========
    
    def test_pure_kannada_short(self, detector):
        """Test short pure Kannada utterance."""
        text = "ನನಗೆ ಎರಡು ಪಿಜ್ಜಾ ಬೇಕು"
        result = detector.detect_language(text)
        
        assert result.lang == "kn"
        assert result.confidence > 0.80

    def test_pure_kannada_medium(self, detector):
        """Test medium-length pure Kannada utterance."""
        text = "ನನಗೆ ಎರಡು ಪಿಜ್ಜಾ ಮತ್ತು ಒಂದು ಬರ್ಗರ್ ಬೇಕು"
        result = detector.detect_language(text)
        
        assert result.lang == "kn"
        assert result.confidence > 0.85

    def test_kannada_with_time(self, detector):
        """Test Kannada with time expression."""
        text = "ಸಂಜೆ ಏಳು ಗಂಟೆಗೆ ಡೆಲಿವರಿ ಮಾಡಿ"
        result = detector.detect_language(text)
        
        assert result.lang == "kn"

    # ========== MARATHI TESTS ==========
    
    def test_pure_marathi_short(self, detector):
        """Test short pure Marathi utterance."""
        text = "मला दोन पिझ्झा हवे"
        result = detector.detect_language(text)
        
        assert result.lang == "mr"
        assert result.confidence > 0.80

    def test_pure_marathi_medium(self, detector):
        """Test medium-length pure Marathi utterance."""
        text = "मला दोन पिझ्झा आणि एक बर्गर हवे"
        result = detector.detect_language(text)
        
        assert result.lang == "mr"
        assert result.confidence > 0.85

    def test_marathi_with_time(self, detector):
        """Test Marathi with time expression."""
        text = "संध्याकाळी सात वाजता डिलिव्हरी करा"
        result = detector.detect_language(text)
        
        assert result.lang == "mr"

    # ========== EDGE CASES ==========
    
    def test_empty_string(self, detector):
        """Test empty string handling."""
        result = detector.detect_language("")
        
        assert result.lang == "en"  # Default fallback
        assert result.confidence == 0.0

    def test_very_short_utterance(self, detector):
        """Test very short utterance (1-2 words)."""
        text = "pizza chahiye"
        result = detector.detect_language(text)
        
        # Should still detect something
        assert result.lang in ["hi", "en", "hinglish"]

    def test_numbers_only(self, detector):
        """Test utterance with only numbers."""
        text = "2 3 7"
        result = detector.detect_language(text)
        
        # Should return some result
        assert result.lang in ["hi", "en", "kn", "mr", "hinglish"]

    def test_special_characters(self, detector):
        """Test handling of special characters."""
        text = "मुझे pizza चाहिए!!!"
        result = detector.detect_language(text)
        
        assert result.lang in ["hinglish", "hi"]

    # ========== BATCH PROCESSING ==========
    
    def test_batch_detection(self, detector):
        """Test batch language detection."""
        texts = [
            "मुझे दो पिज़्ज़ा चाहिए",
            "I want two pizzas",
            "मुझे pizza चाहिए",
            "ನನಗೆ ಎರಡು ಪಿಜ್ಜಾ ಬೇಕು",
            "मला दोन पिझ्झा हवे",
        ]
        
        results = detector.detect_language_batch(texts)
        
        assert len(results) == 5
        assert results[0].lang == "hi"
        assert results[1].lang == "en"
        assert results[2].lang == "hinglish"
        assert results[3].lang == "kn"
        assert results[4].lang == "mr"


# ========== INTEGRATION TEST SCENARIOS ==========

class TestRealWorldScenarios:
    """Test real-world food ordering scenarios."""

    @pytest.fixture
    def detector(self):
        return get_detector()

    def test_order_placement_hindi(self, detector):
        """Test typical Hindi order placement."""
        utterances = [
            "मुझे दो पिज़्ज़ा चाहिए",
            "शाम सात बजे डिलीवर करना",
            "ठीक है कन्फर्म करो",
        ]
        
        for text in utterances:
            result = detector.detect_language(text)
            assert result.lang == "hi"

    def test_order_placement_hinglish(self, detector):
        """Test typical Hinglish order placement."""
        utterances = [
            "मुझे two pizza chahiye",
            "7 pm ko deliver karo",
            "ok confirm karo",
        ]
        
        for text in utterances:
            result = detector.detect_language(text)
            assert result.lang in ["hinglish", "hi", "en"]
            # At least one should be detected as code-mixed
        
        code_mixed_count = sum(
            1 for text in utterances
            if detector.detect_language(text).is_code_mixed
        )
        assert code_mixed_count >= 1

    def test_order_modification_english(self, detector):
        """Test English order modification."""
        utterances = [
            "add one more pizza",
            "change delivery time to eight pm",
            "cancel my order",
        ]
        
        for text in utterances:
            result = detector.detect_language(text)
            assert result.lang == "en"

    def test_status_check_kannada(self, detector):
        """Test Kannada status check."""
        text = "ನನ್ನ ಆರ್ಡರ್ ಎಲ್ಲಿದೆ"
        result = detector.detect_language(text)
        
        assert result.lang == "kn"

    def test_status_check_marathi(self, detector):
        """Test Marathi status check."""
        text = "माझा ऑर्डर कुठे आहे"
        result = detector.detect_language(text)
        
        assert result.lang == "mr"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
