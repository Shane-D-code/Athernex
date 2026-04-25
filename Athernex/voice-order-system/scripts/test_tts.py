"""Test script for TTS engines."""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tts import EdgeTTSEngine, PiperTTSEngine


async def test_edge_tts():
    """Test Edge TTS engine."""
    print("\n[TEST] Edge TTS Engine")
    engine = EdgeTTSEngine()
    
    try:
        # Health check
        healthy = await engine.health_check()
        print(f"✓ Health check: {healthy}")
        
        if healthy:
            # Test synthesis
            result = await engine.synthesize("Hello, this is a test", language="en")
            print(f"✓ Synthesized {len(result.audio_bytes)} bytes")
            print(f"✓ Duration: {result.duration:.2f}s")
            print(f"✓ Voice: {result.voice}")
            print(f"✓ Format: {result.format}")
            
            # Test Hindi
            result_hi = await engine.synthesize("नमस्ते", language="hi")
            print(f"✓ Hindi synthesis: {len(result_hi.audio_bytes)} bytes")
            
            return True
        else:
            print("✗ Edge TTS not healthy")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def test_piper_tts():
    """Test Piper TTS engine."""
    print("\n[TEST] Piper TTS Engine")
    engine = PiperTTSEngine()
    
    try:
        # Health check
        healthy = await engine.health_check()
        print(f"✓ Health check: {healthy}")
        
        if healthy:
            # Test synthesis
            result = await engine.synthesize("Hello, this is a test", language="en")
            print(f"✓ Synthesized {len(result.audio_bytes)} bytes")
            print(f"✓ Duration: {result.duration:.2f}s")
            print(f"✓ Voice: {result.voice}")
            print(f"✓ Format: {result.format}")
            
            return True
        else:
            print("✗ Piper TTS not healthy")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all TTS tests."""
    print("=" * 60)
    print("TTS Engine Tests")
    print("=" * 60)
    
    # Test Edge TTS (should work with internet)
    edge_ok = await test_edge_tts()
    
    # Test Piper TTS (may need model download)
    piper_ok = await test_piper_tts()
    
    print("\n" + "=" * 60)
    print("Results:")
    print(f"  Edge TTS:  {'✓ PASS' if edge_ok else '✗ FAIL'}")
    print(f"  Piper TTS: {'✓ PASS' if piper_ok else '✗ FAIL'}")
    print("=" * 60)
    
    return edge_ok or piper_ok


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
