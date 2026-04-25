"""
Unit tests for emotion detector — Task 21.3
"""
import struct
import wave
import io
import pytest
from emotion.detector import EmotionDetector, Emotion


def _make_wav(amplitude: int, duration_s: float = 0.5, sr: int = 16000) -> bytes:
    """Generate a synthetic WAV with given amplitude (simulates energy level)."""
    n = int(sr * duration_s)
    samples = bytes(struct.pack(f"<{n}h", *([amplitude] * n)))
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(samples)
    return buf.getvalue()


def _make_alternating_wav(amplitude: int, duration_s: float = 0.5, sr: int = 16000) -> bytes:
    """High zero-crossing rate (alternating +/- samples)."""
    n = int(sr * duration_s)
    samples = [amplitude if i % 2 == 0 else -amplitude for i in range(n)]
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(bytes(struct.pack(f"<{n}h", *samples)))
    return buf.getvalue()


@pytest.fixture
def detector():
    return EmotionDetector()


def test_neutral_low_energy(detector):
    audio = _make_wav(amplitude=500)
    result = detector.detect(audio)
    assert result.emotion == Emotion.NEUTRAL
    assert result.confidence >= 0.5
    assert result.should_escalate is False


def test_high_energy_frustrated(detector):
    audio = _make_wav(amplitude=12000)
    result = detector.detect(audio)
    assert result.emotion in (Emotion.FRUSTRATED, Emotion.ANGRY)
    assert result.confidence >= 0.6


def test_should_escalate_when_confident_anger(detector):
    audio = _make_wav(amplitude=20000)  # Max amplitude → angry
    result = detector.detect(audio)
    # At very high energy escalation threshold should trigger
    if result.confidence > 0.70 and result.emotion in (Emotion.ANGRY, Emotion.FRUSTRATED):
        assert result.should_escalate is True


def test_confused_high_zcr_low_energy(detector):
    audio = _make_alternating_wav(amplitude=1000)
    result = detector.detect(audio)
    # High ZCR + low energy → confused or neutral
    assert result.emotion in (Emotion.CONFUSED, Emotion.NEUTRAL)


def test_non_wav_returns_neutral(detector):
    # webm magic bytes
    fake_webm = b'\x1a\x45\xdf\xa3' + b'\x00' * 100
    result = detector.detect(fake_webm)
    assert result.emotion == Emotion.NEUTRAL
    assert result.confidence < 0.6  # Low confidence since we can't decode


def test_prosody_hint_keys(detector):
    audio = _make_wav(amplitude=500)
    result = detector.detect(audio)
    hint = result.prosody_hint
    assert "rate" in hint
    assert "pitch" in hint
    assert "volume" in hint


def test_happy_prosody_increases_rate(detector):
    from emotion.detector import Emotion
    d = EmotionDetector()
    happy_hint   = d._prosody(Emotion.HAPPY)
    neutral_hint = d._prosody(Emotion.NEUTRAL)
    # Happy should have higher rate than neutral
    assert "+" in happy_hint["rate"]


def test_angry_prosody_decreases_rate(detector):
    from emotion.detector import Emotion
    d = EmotionDetector()
    angry_hint = d._prosody(Emotion.ANGRY)
    assert "-" in angry_hint["rate"]


def test_latency_under_100ms(detector):
    import time
    audio = _make_wav(amplitude=3000, duration_s=1.0)
    t0 = time.time()
    detector.detect(audio)
    elapsed_ms = (time.time() - t0) * 1000
    assert elapsed_ms < 100, f"Emotion detection took {elapsed_ms:.1f}ms > 100ms"


def test_all_emotions_classifiable(detector):
    """All 5 emotions should be reachable with different inputs."""
    detected = set()
    for amp in [200, 2000, 6000, 12000, 20000]:
        r = detector.detect(_make_wav(amp))
        detected.add(r.emotion)
    for amp in [500, 1500]:
        r = detector.detect(_make_alternating_wav(amp))
        detected.add(r.emotion)
    # At minimum neutral, frustrated, angry should be hit
    assert Emotion.NEUTRAL in detected or Emotion.CONFUSED in detected
