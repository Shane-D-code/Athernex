#!/usr/bin/env python3
"""
Test script for Android app integration.
Tests all API endpoints that the Android app will use.
"""

import requests
import json
import time

# Base URL (adjust if needed)
BASE_URL = "http://localhost:8000/api"

def test_health_check():
    """Test health check endpoint."""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL.replace('/api', '')}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_language_detection():
    """Test language detection endpoint."""
    print("\n" + "="*60)
    print("TEST 2: Language Detection")
    print("="*60)
    
    test_cases = [
        ("मुझे दो पिज़्ज़ा चाहिए", "hi", "Hindi"),
        ("I want two pizzas", "en", "English"),
        ("मुझे pizza चाहिए", "hinglish", "Hinglish"),
        ("ನನಗೆ ಎರಡು ಪಿಜ್ಜಾ ಬೇಕು", "kn", "Kannada"),
        ("मला दोन पिझ्झा हवे", "mr", "Marathi"),
    ]
    
    passed = 0
    for text, expected_lang, name in test_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/detect-language",
                json={"text": text}
            )
            
            if response.status_code == 200:
                data = response.json()
                detected = data["language"]
                confidence = data["confidence"]
                is_code_mixed = data["is_code_mixed"]
                
                # For Hinglish, accept hi, en, or hinglish
                if expected_lang == "hinglish":
                    success = detected in ["hi", "en", "hinglish"] or is_code_mixed
                else:
                    success = detected == expected_lang
                
                status = "✅" if success else "❌"
                print(f"\n{status} {name}")
                print(f"   Text: {text[:40]}...")
                print(f"   Expected: {expected_lang}")
                print(f"   Detected: {detected} (confidence: {confidence:.2f})")
                print(f"   Code-mixed: {is_code_mixed}")
                
                if success:
                    passed += 1
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {name}: {e}")
    
    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_intent_classification():
    """Test intent classification endpoint."""
    print("\n" + "="*60)
    print("TEST 3: Intent Classification")
    print("="*60)
    
    test_cases = [
        ("Haan confirm karo", "hinglish", "confirm_order"),
        ("Nahi chahiye, cancel karo", "hinglish", "cancel_order"),
        ("Paytm se pay karunga", "hinglish", "payment_query"),
        ("Yes, please confirm", "en", "confirm_order"),
        ("हां कन्फर्म करो", "hi", "confirm_order"),
    ]
    
    passed = 0
    for text, language, expected_intent in test_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/classify-intent",
                json={"text": text, "language": language}
            )
            
            if response.status_code == 200:
                data = response.json()
                detected_intent = data["primary_intent"]
                confidence = data["confidence"]
                bot_response = data["bot_response_suggestion"]
                
                success = detected_intent == expected_intent
                status = "✅" if success else "❌"
                
                print(f"\n{status} {text[:40]}...")
                print(f"   Expected: {expected_intent}")
                print(f"   Detected: {detected_intent} (confidence: {confidence:.2f})")
                print(f"   Bot response: {bot_response}")
                
                if success:
                    passed += 1
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed >= len(test_cases) * 0.8  # 80% pass rate


def test_speech_processing():
    """Test full speech processing endpoint."""
    print("\n" + "="*60)
    print("TEST 4: Full Speech Processing")
    print("="*60)
    
    test_cases = [
        ("मुझे pizza चाहिए", "auto"),
        ("Haan confirm karo, Paytm se pay karunga", "auto"),
        ("I want two pizzas delivered at 7 pm", "en"),
    ]
    
    passed = 0
    for text, language in test_cases:
        try:
            start_time = time.time()
            response = requests.post(
                f"{BASE_URL}/process-speech",
                json={"text": text, "language": language}
            )
            elapsed = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"\n✅ {text[:40]}...")
                print(f"   Language: {data['language']['language']} ({data['language']['confidence']:.2f})")
                print(f"   Intent: {data['intent']['primary_intent']} ({data['intent']['confidence']:.2f})")
                print(f"   Bot response: {data['bot_response']}")
                print(f"   Processing time: {elapsed:.1f}ms (backend: {data['processing_time_ms']:.1f}ms)")
                
                passed += 1
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_phrase_testing():
    """Test phrase testing endpoint."""
    print("\n" + "="*60)
    print("TEST 5: Phrase Testing (for Language Stress Test)")
    print("="*60)
    
    test_cases = [
        ("Haan bhai, confirm karo", "hinglish"),
        ("Yes, please deliver tomorrow", "en"),
        ("मुझे दो पिज़्ज़ा चाहिए", "hi"),
        ("ನನಗೆ ಎರಡು ಪಿಜ್ಜಾ ಬೇಕು", "kn"),
        ("मला दोन पिझ्झा हवे", "mr"),
    ]
    
    passed = 0
    for text, expected_lang in test_cases:
        try:
            response = requests.post(
                f"{BASE_URL}/test-phrase",
                json={"text": text, "expected_language": expected_lang}
            )
            
            if response.status_code == 200:
                data = response.json()
                match = data["language_match"]
                detected = data["detected_language"]
                confidence = data["language_confidence"]
                
                # For Hinglish, be lenient
                if expected_lang == "hinglish":
                    match = detected in ["hi", "en", "hinglish"]
                
                status = "✅" if match else "❌"
                
                print(f"\n{status} {text[:40]}...")
                print(f"   Expected: {expected_lang}")
                print(f"   Detected: {detected} (confidence: {confidence:.2f})")
                print(f"   Match: {match}")
                
                if match:
                    passed += 1
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed >= len(test_cases) * 0.8


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("ANDROID APP INTEGRATION TESTS")
    print("="*60)
    print(f"Testing backend at: {BASE_URL}")
    
    results = {
        "Health Check": test_health_check(),
        "Language Detection": test_language_detection(),
        "Intent Classification": test_intent_classification(),
        "Speech Processing": test_speech_processing(),
        "Phrase Testing": test_phrase_testing(),
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\nOverall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed! Android app integration ready.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed. Check backend.")
        return 1


if __name__ == "__main__":
    exit(main())
