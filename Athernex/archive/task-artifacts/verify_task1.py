"""
TASK 1 Verification Script
Checks fastText installation and runs comprehensive tests.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 70)
print("🔍 TASK 1 — fastText Language Detection Verification")
print("=" * 70)

# Step 1: Check fasttext installation
print("\n📦 Step 1: Checking fasttext installation...")
try:
    import fasttext
    print(f"✅ fasttext installed: version {fasttext.__version__}")
except ImportError as e:
    print(f"❌ fasttext NOT installed: {e}")
    print("\n💡 Install with: pip install fasttext==0.9.2")
    sys.exit(1)

# Step 2: Check model file
print("\n📁 Step 2: Checking lid.176.bin model...")
model_path = os.path.expanduser("~/.fasttext/lid.176.bin")
if os.path.exists(model_path):
    size_mb = os.path.getsize(model_path) / (1024 * 1024)
    print(f"✅ Model found: {model_path} ({size_mb:.1f} MB)")
else:
    print(f"❌ Model NOT found at: {model_path}")
    print("\n💡 Download with:")
    print("   mkdir -p ~/.fasttext")
    print("   wget -O ~/.fasttext/lid.176.bin https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin")
    sys.exit(1)

# Step 3: Test detector initialization
print("\n🔧 Step 3: Initializing fastText detector...")
try:
    from language.fasttext_detector import get_detector
    detector = get_detector()
    print("✅ Detector initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize detector: {e}")
    sys.exit(1)

# Step 4: Run test cases
print("\n🧪 Step 4: Running test cases...")
print("-" * 70)

test_cases = [
    ("मुझे दो पिज़्ज़ा चाहिए", "hi", False, "Pure Hindi"),
    ("I want two pizzas please", "en", False, "Pure English"),
    ("मुझे pizza चाहिए tomorrow", "hi", True, "Hinglish (code-mixed)"),
    ("ನನಗೆ ಎರಡು ಪಿಜ್ಜಾ ಬೇಕು", "kn", False, "Pure Kannada"),
    ("मला दोन पिझ्झा हवे", "mr", False, "Pure Marathi"),
    ("हाँ confirm करो", "hi", True, "Short Hinglish"),
    ("Paytm से pay करूंगा", "hi", True, "Payment Hinglish"),
    ("नहीं चाहिए cancel करो", "hi", True, "Cancel Hinglish"),
]

passed = 0
failed = 0

for text, expected_lang, expected_mixed, description in test_cases:
    result = detector.detect_language(text)
    
    # Check language (allow hinglish as valid for code-mixed)
    lang_match = (result.lang == expected_lang or 
                  (expected_mixed and result.lang == "hinglish"))
    
    # Check code-mixed detection
    mixed_match = result.is_code_mixed == expected_mixed
    
    if lang_match and mixed_match:
        status = "✅ PASS"
        passed += 1
    else:
        status = "❌ FAIL"
        failed += 1
    
    print(f"{status} | {description}")
    print(f"     Input: {text}")
    print(f"     Expected: lang={expected_lang}, mixed={expected_mixed}")
    print(f"     Got: lang={result.lang}, conf={result.confidence:.2f}, mixed={result.is_code_mixed}")
    print()

print("-" * 70)
print(f"\n📊 Results: {passed}/{len(test_cases)} tests passed")

if failed == 0:
    print("\n🎉 SUCCESS! All tests passed!")
    print("\n✅ TASK 1 is COMPLETE and WORKING")
    print("\n📖 Next steps:")
    print("   1. Integrate into your pipeline (see TASK1_FASTTEXT_OPTIMIZATION.md)")
    print("   2. Test with real voice input")
    print("   3. Move to TASK 2 (Piper TTS)")
else:
    print(f"\n⚠️  {failed} test(s) failed")
    print("\n💡 Check:")
    print("   1. Model file is correct version (lid.176.bin)")
    print("   2. fasttext version matches (0.9.2)")
    print("   3. Review TASK1_FASTTEXT_OPTIMIZATION.md for troubleshooting")

print("=" * 70)

# Step 5: Performance benchmark
if failed == 0:
    print("\n⚡ Step 5: Performance benchmark...")
    import time
    
    test_text = "मुझे pizza चाहिए tomorrow"
    iterations = 100
    
    start = time.time()
    for _ in range(iterations):
        detector.detect_language(test_text)
    end = time.time()
    
    avg_time_ms = ((end - start) / iterations) * 1000
    print(f"✅ Average detection time: {avg_time_ms:.2f}ms ({iterations} iterations)")
    print(f"✅ Throughput: {1000/avg_time_ms:.0f} detections/second")
    
    if avg_time_ms < 50:
        print("🚀 Excellent performance!")
    elif avg_time_ms < 100:
        print("✅ Good performance")
    else:
        print("⚠️  Performance could be improved (consider caching)")

print("\n" + "=" * 70)
