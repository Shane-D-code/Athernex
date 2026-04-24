#!/usr/bin/env python3
"""Quick language detection test."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from language.hybrid_detector import get_hybrid_detector

def main():
    print("\n" + "="*60)
    print("QUICK LANGUAGE DETECTION TEST")
    print("="*60)
    
    detector = get_hybrid_detector()
    
    tests = [
        ("मुझे दो पिज़्ज़ा चाहिए", "hi", "Hindi"),
        ("I want two pizzas", "en", "English"),
        ("मुझे pizza चाहिए", "hinglish", "Hinglish"),
        ("ನನಗೆ ಎರಡು ಪಿಜ್ಜಾ ಬೇಕು", "kn", "Kannada"),
        ("मला दोन पिझ्झा हवे", "mr", "Marathi"),
    ]
    
    passed = 0
    total = len(tests)
    
    for text, expected, name in tests:
        result = detector.detect_from_text(text)
        detected = result.language
        
        # For Hinglish, accept hi, en, or hinglish
        if expected == "hinglish":
            success = detected in ["hi", "en", "hinglish"] or result.is_code_mixed
        else:
            success = detected == expected
        
        status = "✅" if success else "❌"
        if success:
            passed += 1
        
        print(f"\n{status} {name}")
        print(f"   Text: {text[:40]}...")
        print(f"   Expected: {expected}")
        print(f"   Detected: {detected} (confidence: {result.confidence:.2f})")
        print(f"   Code-mixed: {result.is_code_mixed}")
        print(f"   Method: {result.method}")
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
