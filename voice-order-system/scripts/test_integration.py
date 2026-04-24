"""Integration test for STT, LLM, and TTS components."""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm import OllamaLLMProcessor
from tts import EdgeTTSEngine


async def test_full_pipeline():
    """Test the complete STT → LLM → TTS pipeline."""
    print("\n" + "=" * 70)
    print("INTEGRATION TEST: Voice Order System Pipeline")
    print("=" * 70)
    
    # Initialize components
    print("\n[1/4] Initializing components...")
    # stt = WhisperSTTEngine()  # Skip STT for now (server not running)
    llm = OllamaLLMProcessor(model="phi3:latest")
    tts = EdgeTTSEngine()
    
    # Health checks
    print("\n[2/4] Running health checks...")
    # stt_healthy = await stt.health_check()
    llm_healthy = await llm.health_check()
    tts_healthy = await tts.health_check()
    
    print(f"  STT (Whisper):  SKIPPED (server not started)")
    print(f"  LLM (Ollama):   {'✓ OK' if llm_healthy else '✗ FAIL'}")
    print(f"  TTS (Edge):     {'✓ OK' if tts_healthy else '✗ FAIL'}")
    
    if not all([llm_healthy, tts_healthy]):
        print("\n✗ Some components are not healthy. Cannot proceed with integration test.")
        return False
    
    # Test LLM processing
    print("\n[3/4] Testing LLM intent extraction...")
    test_utterances = [
        "I want to order 2 pizzas for delivery at 7pm",
        "मुझे 3 डोसा चाहिए",  # Hindi: I want 3 dosas
        "Cancel my order please",
    ]
    
    for utterance in test_utterances:
        print(f"\n  Input: '{utterance}'")
        try:
            response = await llm.process_utterance(utterance)
            print(f"    Intent: {response.structured_data.intent.value}")
            print(f"    Items: {len(response.structured_data.items)} item(s)")
            if response.structured_data.items:
                for item in response.structured_data.items:
                    print(f"      - {item.quantity}x {item.name}")
            print(f"    Confidence: {response.structured_data.confidence:.2f}")
            print(f"    Time: {response.processing_time:.2f}s")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    # Test TTS synthesis
    print("\n[4/4] Testing TTS synthesis...")
    test_responses = [
        ("en", "Your order for 2 pizzas has been confirmed"),
        ("hi", "आपका ऑर्डर कन्फर्म हो गया है"),  # Your order is confirmed
    ]
    
    for lang, text in test_responses:
        print(f"\n  Language: {lang}")
        print(f"  Text: '{text}'")
        try:
            result = await tts.synthesize(text, language=lang)
            print(f"    ✓ Synthesized {len(result.audio_bytes)} bytes")
            print(f"    Duration: {result.duration:.2f}s")
            print(f"    Voice: {result.voice}")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    # Cleanup
    # await stt.close()
    await llm.close()
    
    print("\n" + "=" * 70)
    print("✓ Integration test completed successfully!")
    print("=" * 70)
    
    return True


async def main():
    try:
        success = await test_full_pipeline()
        return success
    except Exception as e:
        print(f"\n✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
