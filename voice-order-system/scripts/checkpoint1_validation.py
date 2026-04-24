"""
Checkpoint 1 Validation Script.

Verifies core components are functional:
- STT, LLM, TTS services
- Confidence scoring
- Language detection
- Basic integration
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm import OllamaLLMProcessor
from tts import EdgeTTSEngine
from confidence import ConfidenceAnalyzer
from language import LanguageDetector
from utils import TimeParser


async def main():
    print("\n" + "=" * 70)
    print("CHECKPOINT 1: Core Components Validation")
    print("=" * 70)
    
    results = {}
    
    # Test 1: LLM Service
    print("\n[1/5] Testing LLM Service...")
    try:
        llm = OllamaLLMProcessor(model="phi3:latest")
        healthy = await llm.health_check()
        if healthy:
            response = await llm.process_utterance("I want 2 pizzas at 7pm")
            print(f"  ✓ LLM healthy and processing")
            print(f"    Intent: {response.structured_data.intent.value}")
            print(f"    Items: {len(response.structured_data.items)}")
            results['llm'] = True
        else:
            print("  ✗ LLM not healthy")
            results['llm'] = False
        await llm.close()
    except Exception as e:
        print(f"  ✗ LLM error: {e}")
        results['llm'] = False
    
    # Test 2: TTS Service
    print("\n[2/5] Testing TTS Service...")
    try:
        tts = EdgeTTSEngine()
        healthy = await tts.health_check()
        if healthy:
            result = await tts.synthesize("Test", language="en")
            print(f"  ✓ TTS healthy and synthesizing")
            print(f"    Audio: {len(result.audio_bytes)} bytes")
            results['tts'] = True
        else:
            print("  ✗ TTS not healthy")
            results['tts'] = False
    except Exception as e:
        print(f"  ✗ TTS error: {e}")
        results['tts'] = False
    
    # Test 3: Confidence Analyzer
    print("\n[3/5] Testing Confidence Analyzer...")
    try:
        from llm.base import StructuredOrderData, Intent, OrderItem
        analyzer = ConfidenceAnalyzer()
        
        test_data = StructuredOrderData(
            intent=Intent.PLACE_ORDER,
            items=[OrderItem(name="pizza", quantity=2)],
            confidence=0.9,
            missing_fields=[]
        )
        
        recommendation = analyzer.analyze(0.85, test_data, [])
        print(f"  ✓ Confidence analyzer working")
        print(f"    Should clarify: {recommendation.should_clarify}")
        print(f"    Reason: {recommendation.reason}")
        results['confidence'] = True
    except Exception as e:
        print(f"  ✗ Confidence error: {e}")
        results['confidence'] = False
    
    # Test 4: Language Detector
    print("\n[4/5] Testing Language Detector...")
    try:
        from stt.base import TranscriptionResult, WordResult
        detector = LanguageDetector()
        
        test_transcription = TranscriptionResult(
            text="I want pizza",
            language="en",
            language_probability=0.95,
            words=[
                WordResult(word="I", start=0.0, end=0.1, confidence=0.9, language="en"),
                WordResult(word="want", start=0.1, end=0.3, confidence=0.95, language="en"),
                WordResult(word="pizza", start=0.3, end=0.6, confidence=0.92, language="en"),
            ],
            duration=0.6,
            confidence=0.92
        )
        
        result = detector.detect(test_transcription)
        print(f"  ✓ Language detector working")
        print(f"    Dominant: {result.dominant_language}")
        print(f"    Code-mixed: {result.is_code_mixed}")
        results['language'] = True
    except Exception as e:
        print(f"  ✗ Language error: {e}")
        results['language'] = False
    
    # Test 5: Time Parser
    print("\n[5/5] Testing Time Parser...")
    try:
        parser = TimeParser()
        
        test_cases = [
            "in 30 minutes",
            "tomorrow at 5pm",
            "at 7pm"
        ]
        
        all_passed = True
        for expr in test_cases:
            result = parser.parse(expr)
            if result:
                print(f"  ✓ '{expr}' → {result[:19]}")
            else:
                print(f"  ✗ Failed to parse '{expr}'")
                all_passed = False
        
        results['time_parser'] = all_passed
    except Exception as e:
        print(f"  ✗ Time parser error: {e}")
        results['time_parser'] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("CHECKPOINT 1 RESULTS:")
    print("=" * 70)
    for component, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {component.upper():20s} {status}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ CHECKPOINT 1 PASSED - All core components functional")
    else:
        print("✗ CHECKPOINT 1 FAILED - Some components need attention")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
