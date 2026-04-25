"""
Quick test script for fastText language detection.

Tests all supported languages with realistic food ordering utterances.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from language.fasttext_detector import get_detector, FASTTEXT_AVAILABLE


def print_header(title):
    """Print section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_language(detector, language_name, test_cases):
    """Test a specific language."""
    print(f"\n{language_name} Tests:")
    print("-" * 70)
    
    passed = 0
    failed = 0
    
    for text, expected_lang in test_cases:
        result = detector.detect_language(text)
        
        # Check if detection matches expected
        match = result.lang == expected_lang
        status = "✓" if match else "✗"
        
        if match:
            passed += 1
        else:
            failed += 1
        
        # Print result
        print(f"{status} {text[:40]:40} → {result.lang:10} ({result.confidence:.3f})")
        if result.is_code_mixed:
            print(f"  └─ Code-mixed detected")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return passed, failed


def main():
    """Run all tests."""
    print_header("fastText Language Detection - Quick Test")
    
    if not FASTTEXT_AVAILABLE:
        print("✗ fasttext not installed!")
        print("\nInstall with:")
        print("  pip install fasttext")
        print("  python scripts/setup_fasttext.py")
        return 1
    
    try:
        detector = get_detector()
    except FileNotFoundError as e:
        print(f"✗ Model not found: {e}")
        print("\nDownload model with:")
        print("  python scripts/setup_fasttext.py")
        return 1
    
    print("✓ fastText detector loaded successfully\n")
    
    # Test cases: (text, expected_language)
    test_suites = {
        "Pure Hindi": [
            ("मुझे दो पिज़्ज़ा चाहिए", "hi"),
            ("शाम सात बजे डिलीवर करना", "hi"),
            ("मेरा ऑर्डर कहाँ है", "hi"),
            ("ऑर्डर कैंसिल करो", "hi"),
        ],
        
        "Pure English": [
            ("I want two pizzas", "en"),
            ("deliver at seven pm", "en"),
            ("where is my order", "en"),
            ("cancel my order", "en"),
        ],
        
        "Hinglish (Code-mixed)": [
            ("मुझे pizza चाहिए", "hinglish"),
            ("two pizza aur ek burger", "hinglish"),
            ("7 pm ko deliver karo", "hinglish"),
            ("मुझे burger chahiye please", "hinglish"),
        ],
        
        "Pure Kannada": [
            ("ನನಗೆ ಎರಡು ಪಿಜ್ಜಾ ಬೇಕು", "kn"),
            ("ಸಂಜೆ ಏಳು ಗಂಟೆಗೆ ಡೆಲಿವರಿ ಮಾಡಿ", "kn"),
            ("ನನ್ನ ಆರ್ಡರ್ ಎಲ್ಲಿದೆ", "kn"),
        ],
        
        "Pure Marathi": [
            ("मला दोन पिझ्झा हवे", "mr"),
            ("संध्याकाळी सात वाजता डिलिव्हरी करा", "mr"),
            ("माझा ऑर्डर कुठे आहे", "mr"),
        ],
    }
    
    total_passed = 0
    total_failed = 0
    
    for suite_name, test_cases in test_suites.items():
        passed, failed = test_language(detector, suite_name, test_cases)
        total_passed += passed
        total_failed += failed
    
    # Summary
    print_header("Test Summary")
    print(f"Total tests: {total_passed + total_failed}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    
    if total_failed == 0:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total_failed} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
