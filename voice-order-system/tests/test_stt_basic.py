"""
Basic test for STT engine functionality.
Tests Whisper STT with synthetic audio.
"""

import numpy as np
import sys
sys.path.insert(0, 'src')

from src.stt.engine import WhisperSTTEngine


def generate_test_audio(duration_sec: float = 1.0, sample_rate: int = 16000) -> np.ndarray:
    """Generate simple sine wave test audio (simulates speech)."""
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec))
    # Mix of frequencies to simulate speech-like audio
    audio = (
        0.3 * np.sin(2 * np.pi * 200 * t) +  # Low frequency
        0.2 * np.sin(2 * np.pi * 800 * t) +  # Mid frequency
        0.1 * np.sin(2 * np.pi * 1500 * t)   # High frequency
    )
    return audio.astype(np.float32)


def test_whisper_basic():
    """Test basic Whisper STT functionality."""
    print("=" * 60)
    print("Testing Whisper STT Engine")
    print("=" * 60)
    
    # Create engine
    print("\n1. Creating Whisper engine...")
    engine = WhisperSTTEngine()
    
    # Check availability
    print("2. Checking availability...")
    available = engine.is_available()
    print(f"   ✓ Whisper available: {available}")
    assert available, "Whisper should be available"
    
    # Generate test audio
    print("\n3. Generating test audio (1 second)...")
    audio = generate_test_audio(duration_sec=1.0)
    print(f"   ✓ Audio shape: {audio.shape}, dtype: {audio.dtype}")
    
    # Transcribe
    print("\n4. Transcribing audio...")
    result = engine.transcribe(audio, sample_rate=16000)
    
    # Display results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Transcription: '{result.transcription}'")
    print(f"Confidence: {result.utterance_confidence:.2f}")
    print(f"Language: {result.dominant_language.value}")
    print(f"Code-mixed: {result.is_code_mixed}")
    print(f"Processing time: {result.processing_time_ms:.0f}ms")
    print(f"Words detected: {len(result.words)}")
    
    if result.words:
        print("\nWord-level details:")
        for w in result.words[:5]:  # Show first 5 words
            print(f"  - '{w.word}' (conf={w.confidence:.2f}, lang={w.language.value})")
    
    print("\n" + "=" * 60)
    print("✓ Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_whisper_basic()
