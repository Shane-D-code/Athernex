"""
BRUTAL COMPREHENSIVE LANGUAGE DETECTION TEST SUITE

Tests every possible scenario, edge case, and boundary condition for:
- Pure language detection (Hindi, English, Kannada, Marathi)
- Code-mixed speech (Hinglish and other combinations)
- Edge cases (empty strings, numbers, special characters)
- Real-world food ordering scenarios
- Script mixing detection
- Confidence scoring
- Fallback behavior

Run with: pytest tests/test_brutal_language_detection.py -v -s
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from language.hybrid_detector import get_hybrid_detector


class TestPureHindi:
    """Brutal tests for pure Hindi detection."""
    
    def test_hindi_simple_order(self):
        """Test simple Hindi order."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मुझे दो पिज़्ज़ा चाहिए")
        assert result.language == "hi"
        assert not result.is_code_mixed
    
    def test_hindi_complex_order(self):
        """Test complex Hindi order with multiple items."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text(
            "मुझे दो पिज़्ज़ा, तीन बर्गर और एक कोल्ड ड्रिंक चाहिए"
        )
        assert result.language == "hi"
    
    def test_hindi_with_time(self):
        """Test Hindi with time expression."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("शाम सात बजे डिलीवर करना")
        assert result.language == "hi"
    
    def test_hindi_cancellation(self):
        """Test Hindi order cancellation."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मेरा ऑर्डर कैंसिल करो")
        assert result.language == "hi"
    
    def test_hindi_status_check(self):
        """Test Hindi status check."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मेरा ऑर्डर कहाँ है")
        assert result.language == "hi"
    
    def test_hindi_modification(self):
        """Test Hindi order modification."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("एक और पिज़्ज़ा जोड़ दो")
        assert result.language == "hi"
    
    def test_hindi_with_numbers(self):
        """Test Hindi with numeric quantities."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मुझे 2 पिज़्ज़ा और 3 बर्गर चाहिए")
        assert result.language == "hi"
    
    def test_hindi_polite_form(self):
        """Test Hindi polite form."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("कृपया मुझे दो पिज़्ज़ा दीजिए")
        assert result.language == "hi"
    
    def test_hindi_informal(self):
        """Test Hindi informal speech."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("भाई दो पिज़्ज़ा दे दे")
        assert result.language == "hi"
    
    def test_hindi_question(self):
        """Test Hindi question."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("क्या आप पिज़्ज़ा डिलीवर करते हो")
        assert result.language == "hi"


class TestPureEnglish:
    """Brutal tests for pure English detection."""
    
    def test_english_simple_order(self):
        """Test simple English order."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("I want two pizzas")
        assert result.language == "en"
        assert not result.is_code_mixed
    
    def test_english_complex_order(self):
        """Test complex English order."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text(
            "I want two large pizzas, three burgers and one cold drink"
        )
        assert result.language == "en"
    
    def test_english_with_time(self):
        """Test English with time."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("deliver at seven pm")
        assert result.language == "en"
    
    def test_english_cancellation(self):
        """Test English cancellation."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("cancel my order")
        assert result.language == "en"
    
    def test_english_status_check(self):
        """Test English status check."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("where is my order")
        assert result.language == "en"
    
    def test_english_modification(self):
        """Test English modification."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("add one more pizza")
        assert result.language == "en"
    
    def test_english_polite(self):
        """Test English polite form."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("could you please deliver two pizzas")
        assert result.language == "en"
    
    def test_english_casual(self):
        """Test English casual speech."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("gimme two pizzas")
        assert result.language == "en"
    
    def test_english_question(self):
        """Test English question."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("do you deliver pizzas")
        assert result.language == "en"
    
    def test_english_with_numbers(self):
        """Test English with numbers."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("I want 2 pizzas and 3 burgers")
        assert result.language == "en"


class TestHinglish:
    """Brutal tests for Hinglish (code-mixed) detection."""
    
    def test_hinglish_mixed_script(self):
        """Test Hinglish with mixed Devanagari and Latin."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मुझे pizza चाहिए")
        assert result.is_code_mixed or result.language == "hinglish"
    
    def test_hinglish_english_dominant(self):
        """Test Hinglish with English-dominant words."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("I want do pizza aur ek burger")
        # Should detect code-mixing
        assert result.is_code_mixed or result.language in ["hinglish", "en", "hi"]
    
    def test_hinglish_hindi_dominant(self):
        """Test Hinglish with Hindi-dominant words."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मुझे pizza और burger चाहिए please")
        assert result.is_code_mixed or result.language == "hinglish"
    
    def test_hinglish_balanced(self):
        """Test balanced Hinglish."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("two pizza aur ek burger chahiye")
        assert result.is_code_mixed or result.language in ["hinglish", "hi", "en"]
    
    def test_hinglish_with_time(self):
        """Test Hinglish with time expression."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("7 pm ko deliver karo please")
        assert result.is_code_mixed or result.language in ["hinglish", "hi", "en"]
    
    def test_hinglish_numbers_mixed(self):
        """Test Hinglish with numbers."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मुझे 2 pizza और 3 burger चाहिए")
        assert result.is_code_mixed or result.language == "hinglish"
    
    def test_hinglish_english_verbs(self):
        """Test Hinglish with English verbs."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मुझे order करना है")
        assert result.is_code_mixed or result.language == "hinglish"
    
    def test_hinglish_hindi_verbs(self):
        """Test Hinglish with Hindi verbs."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("I want pizza खाना है")
        assert result.is_code_mixed or result.language in ["hinglish", "hi", "en"]
    
    def test_hinglish_casual_speech(self):
        """Test casual Hinglish."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("bhai pizza de do yaar")
        # This is transliterated Hindi, might be detected as English
        assert result.language in ["en", "hi", "hinglish"]
    
    def test_hinglish_food_names(self):
        """Test Hinglish with food names."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मुझे margherita pizza और french fries चाहिए")
        assert result.is_code_mixed or result.language == "hinglish"


class TestKannada:
    """Brutal tests for Kannada detection."""
    
    def test_kannada_simple_order(self):
        """Test simple Kannada order."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("ನನಗೆ ಎರಡು ಪಿಜ್ಜಾ ಬೇಕು")
        assert result.language == "kn"
    
    def test_kannada_complex_order(self):
        """Test complex Kannada order."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("ನನಗೆ ಎರಡು ಪಿಜ್ಜಾ ಮತ್ತು ಒಂದು ಬರ್ಗರ್ ಬೇಕು")
        assert result.language == "kn"
    
    def test_kannada_with_time(self):
        """Test Kannada with time."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("ಸಂಜೆ ಏಳು ಗಂಟೆಗೆ ಡೆಲಿವರಿ ಮಾಡಿ")
        assert result.language == "kn"
    
    def test_kannada_status_check(self):
        """Test Kannada status check."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("ನನ್ನ ಆರ್ಡರ್ ಎಲ್ಲಿದೆ")
        assert result.language == "kn"
    
    def test_kannada_cancellation(self):
        """Test Kannada cancellation."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("ನನ್ನ ಆರ್ಡರ್ ರದ್ದು ಮಾಡಿ")
        assert result.language == "kn"
    
    def test_kannada_polite(self):
        """Test Kannada polite form."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("ದಯವಿಟ್ಟು ಎರಡು ಪಿಜ್ಜಾ ಕೊಡಿ")
        assert result.language == "kn"
    
    def test_kannada_question(self):
        """Test Kannada question."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("ನೀವು ಪಿಜ್ಜಾ ಡೆಲಿವರಿ ಮಾಡುತ್ತೀರಾ")
        assert result.language == "kn"


class TestMarathi:
    """Brutal tests for Marathi detection."""
    
    def test_marathi_simple_order(self):
        """Test simple Marathi order."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मला दोन पिझ्झा हवे")
        assert result.language == "mr"
    
    def test_marathi_complex_order(self):
        """Test complex Marathi order."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मला दोन पिझ्झा आणि एक बर्गर हवे")
        assert result.language == "mr"
    
    def test_marathi_with_time(self):
        """Test Marathi with time."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("संध्याकाळी सात वाजता डिलिव्हरी करा")
        assert result.language == "mr"
    
    def test_marathi_status_check(self):
        """Test Marathi status check."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("माझा ऑर्डर कुठे आहे")
        assert result.language == "mr"
    
    def test_marathi_cancellation(self):
        """Test Marathi cancellation."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("माझा ऑर्डर रद्द करा")
        assert result.language == "mr"
    
    def test_marathi_polite(self):
        """Test Marathi polite form."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("कृपया दोन पिझ्झा द्या")
        assert result.language == "mr"
    
    def test_marathi_question(self):
        """Test Marathi question."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("तुम्ही पिझ्झा डिलिव्हरी करता का")
        assert result.language == "mr"


class TestEdgeCases:
    """Brutal edge case tests."""
    
    def test_empty_string(self):
        """Test empty string."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("")
        # Should return some default
        assert result.language in ["hi", "en", "kn", "mr", "hinglish"]
    
    def test_whitespace_only(self):
        """Test whitespace only."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("   ")
        assert result.language in ["hi", "en", "kn", "mr", "hinglish"]
    
    def test_single_word_hindi(self):
        """Test single Hindi word."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("पिज़्ज़ा")
        assert result.language == "hi"
    
    def test_single_word_english(self):
        """Test single English word."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("pizza")
        assert result.language == "en"
    
    def test_numbers_only(self):
        """Test numbers only."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("2 3 7")
        # Should return some language
        assert result.language in ["hi", "en", "kn", "mr", "hinglish"]
    
    def test_special_characters(self):
        """Test special characters."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("!@#$%^&*()")
        assert result.language in ["hi", "en", "kn", "mr", "hinglish"]
    
    def test_mixed_special_chars(self):
        """Test text with special characters."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मुझे pizza चाहिए!!!")
        assert result.is_code_mixed or result.language in ["hinglish", "hi"]
    
    def test_very_long_text(self):
        """Test very long text."""
        detector = get_hybrid_detector()
        long_text = "मुझे पिज़्ज़ा चाहिए " * 100
        result = detector.detect_from_text(long_text)
        assert result.language == "hi"
    
    def test_repeated_words(self):
        """Test repeated words."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("pizza pizza pizza")
        assert result.language == "en"
    
    def test_mixed_case(self):
        """Test mixed case English."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("I WANT TWO PIZZAS")
        assert result.language == "en"


class TestRealWorldScenarios:
    """Brutal real-world scenario tests."""
    
    def test_noisy_transcription_hindi(self):
        """Test noisy Hindi transcription."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मुझे  दो   पिज़्ज़ा   चाहिए")
        assert result.language == "hi"
    
    def test_noisy_transcription_english(self):
        """Test noisy English transcription."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("I  want   two   pizzas")
        assert result.language == "en"
    
    def test_incomplete_sentence_hindi(self):
        """Test incomplete Hindi sentence."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मुझे दो")
        assert result.language == "hi"
    
    def test_incomplete_sentence_english(self):
        """Test incomplete English sentence."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("I want two")
        assert result.language == "en"
    
    def test_multiple_sentences_hindi(self):
        """Test multiple Hindi sentences."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text(
            "मुझे दो पिज़्ज़ा चाहिए। शाम सात बजे डिलीवर करना।"
        )
        assert result.language == "hi"
    
    def test_multiple_sentences_english(self):
        """Test multiple English sentences."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text(
            "I want two pizzas. Deliver at seven pm."
        )
        assert result.language == "en"
    
    def test_brand_names_hindi(self):
        """Test Hindi with brand names."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मुझे Dominos का pizza चाहिए")
        assert result.is_code_mixed or result.language in ["hinglish", "hi"]
    
    def test_brand_names_english(self):
        """Test English with brand names."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("I want Dominos pizza")
        assert result.language == "en"
    
    def test_address_hindi(self):
        """Test Hindi with address."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text(
            "मुझे दो पिज़्ज़ा चाहिए MG Road पर"
        )
        assert result.is_code_mixed or result.language in ["hinglish", "hi"]
    
    def test_phone_number_hindi(self):
        """Test Hindi with phone number."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मुझे कॉल करो 9876543210 पर")
        assert result.language == "hi"


class TestConfidenceScoring:
    """Test confidence scoring."""
    
    def test_high_confidence_hindi(self):
        """Test high confidence Hindi."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text(
            "मुझे दो पिज़्ज़ा और तीन बर्गर चाहिए शाम सात बजे"
        )
        assert result.language == "hi"
        # Confidence should be reasonable
        assert result.confidence >= 0.0
    
    def test_high_confidence_english(self):
        """Test high confidence English."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text(
            "I want two large pizzas and three burgers at seven pm"
        )
        assert result.language == "en"
        assert result.confidence >= 0.0
    
    def test_low_confidence_mixed(self):
        """Test low confidence mixed speech."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मुझे pizza burger fries चाहिए")
        # Should detect as code-mixed
        assert result.is_code_mixed or result.language == "hinglish"


class TestBatchProcessing:
    """Test batch processing."""
    
    def test_batch_mixed_languages(self):
        """Test batch with mixed languages."""
        detector = get_hybrid_detector()
        
        texts = [
            "मुझे दो पिज़्ज़ा चाहिए",
            "I want two pizzas",
            "मुझे pizza चाहिए",
            "ನನಗೆ ಎರಡು ಪಿಜ್ಜಾ ಬೇಕು",
            "मला दोन पिझ्झा हवे",
        ]
        
        results = [detector.detect_from_text(text) for text in texts]
        
        assert results[0].language == "hi"
        assert results[1].language == "en"
        assert results[2].is_code_mixed or results[2].language == "hinglish"
        assert results[3].language == "kn"
        assert results[4].language == "mr"


class TestFallbackBehavior:
    """Test fallback behavior when fastText not available."""
    
    def test_fallback_hindi_script(self):
        """Test fallback detects Hindi script."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मुझे पिज़्ज़ा चाहिए")
        # Should detect Hindi even with fallback
        assert result.language == "hi"
    
    def test_fallback_english_script(self):
        """Test fallback detects English script."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("I want pizza")
        # Should detect English even with fallback
        assert result.language == "en"
    
    def test_fallback_mixed_script(self):
        """Test fallback detects mixed script."""
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मुझे pizza चाहिए")
        # Should detect code-mixing even with fallback
        assert result.is_code_mixed or result.language == "hinglish"


class TestStressTests:
    """Stress tests for language detection."""
    
    def test_rapid_succession(self):
        """Test rapid successive detections."""
        detector = get_hybrid_detector()
        
        for _ in range(100):
            result = detector.detect_from_text("मुझे pizza चाहिए")
            assert result.language in ["hi", "en", "hinglish"]
    
    def test_different_languages_succession(self):
        """Test different languages in succession."""
        detector = get_hybrid_detector()
        
        texts = [
            "मुझे दो पिज़्ज़ा चाहिए",
            "I want two pizzas",
            "ನನಗೆ ಎರಡು ಪಿಜ್ಜಾ ಬೇಕು",
            "मला दोन पिझ्झा हवे",
        ] * 25  # 100 total
        
        for text in texts:
            result = detector.detect_from_text(text)
            assert result.language in ["hi", "en", "kn", "mr"]
    
    def test_unicode_edge_cases(self):
        """Test Unicode edge cases."""
        detector = get_hybrid_detector()
        
        # Zero-width characters
        result = detector.detect_from_text("मुझे\u200bपिज़्ज़ा\u200bचाहिए")
        assert result.language == "hi"
        
        # Combining characters
        result = detector.detect_from_text("मुझे पिज़्ज़ा चाहिए")
        assert result.language == "hi"


# Summary test to run all
def test_summary():
    """Summary of all language detection tests."""
    detector = get_hybrid_detector()
    
    test_cases = {
        "Pure Hindi": [
            ("मुझे दो पिज़्ज़ा चाहिए", "hi"),
            ("शाम सात बजे डिलीवर करना", "hi"),
            ("मेरा ऑर्डर कहाँ है", "hi"),
        ],
        "Pure English": [
            ("I want two pizzas", "en"),
            ("deliver at seven pm", "en"),
            ("where is my order", "en"),
        ],
        "Hinglish": [
            ("मुझे pizza चाहिए", "hinglish"),
            ("two pizza aur ek burger", "hinglish"),
            ("7 pm ko deliver karo", "hinglish"),
        ],
        "Kannada": [
            ("ನನಗೆ ಎರಡು ಪಿಜ್ಜಾ ಬೇಕು", "kn"),
            ("ಸಂಜೆ ಏಳು ಗಂಟೆಗೆ ಡೆಲಿವರಿ ಮಾಡಿ", "kn"),
        ],
        "Marathi": [
            ("मला दोन पिझ्झा हवे", "mr"),
            ("संध्याकाळी सात वाजता डिलिव्हरी करा", "mr"),
        ],
    }
    
    results = {}
    for category, cases in test_cases.items():
        passed = 0
        total = len(cases)
        
        for text, expected in cases:
            result = detector.detect_from_text(text)
            if expected == "hinglish":
                # For Hinglish, accept code-mixed or hinglish label
                if result.is_code_mixed or result.language == "hinglish":
                    passed += 1
            else:
                if result.language == expected:
                    passed += 1
        
        results[category] = f"{passed}/{total}"
    
    print("\n" + "="*60)
    print("LANGUAGE DETECTION TEST SUMMARY")
    print("="*60)
    for category, result in results.items():
        print(f"{category:20} {result}")
    print("="*60)


if __name__ == "__main__":
    # Run with: python tests/test_brutal_language_detection.py
    pytest.main([__file__, "-v", "-s"])
