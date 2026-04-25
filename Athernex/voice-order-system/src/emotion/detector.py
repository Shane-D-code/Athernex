"""
Emotion detector — Task 21.1 / 21.2
Acoustic feature extraction + rule-based emotion classification.
Adjusts TTS prosody based on detected emotion.
Processes in < 100ms (no model loading required).
"""

import logging
import math
import struct
import wave
import io
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class Emotion(str, Enum):
    NEUTRAL    = "neutral"
    HAPPY      = "happy"
    FRUSTRATED = "frustrated"
    ANGRY      = "angry"
    CONFUSED   = "confused"


@dataclass
class EmotionResult:
    emotion: Emotion
    confidence: float           # 0.0 – 1.0
    should_escalate: bool       # True if angry/frustrated > 0.7
    prosody_hint: dict          # rate, pitch, volume adjustments for TTS


# ── Acoustic feature extraction ────────────────────────────────────────────

def _extract_pcm(audio_bytes: bytes) -> Optional[Tuple[list, int]]:
    """Try to decode audio as WAV and return (samples, framerate)."""
    try:
        with wave.open(io.BytesIO(audio_bytes)) as wf:
            n = wf.getnframes()
            raw = wf.readframes(n)
            sr = wf.getframerate()
            sw = wf.getsampwidth()
            samples = list(struct.unpack(f"<{n}{'h' if sw==2 else 'b'}", raw))
            return samples, sr
    except Exception:
        return None


def _rms_energy(samples: list) -> float:
    if not samples:
        return 0.0
    return math.sqrt(sum(s * s for s in samples) / len(samples))


def _zero_crossing_rate(samples: list) -> float:
    if len(samples) < 2:
        return 0.0
    crossings = sum(1 for i in range(1, len(samples)) if samples[i-1] * samples[i] < 0)
    return crossings / len(samples)


def _speaking_rate_proxy(samples: list, sr: int) -> float:
    """Estimate speaking rate via energy envelope peak count (syllable proxy)."""
    if not samples or sr == 0:
        return 0.0
    chunk = max(1, sr // 20)  # 50ms windows
    energies = [_rms_energy(samples[i:i+chunk]) for i in range(0, len(samples), chunk)]
    if not energies:
        return 0.0
    threshold = max(energies) * 0.3
    peaks = sum(1 for i in range(1, len(energies)-1)
                if energies[i] > threshold and energies[i] > energies[i-1] and energies[i] > energies[i+1])
    duration_s = len(samples) / sr
    return peaks / duration_s if duration_s > 0 else 0.0


# ── Classification ─────────────────────────────────────────────────────────

class EmotionDetector:
    """
    Rule-based acoustic emotion classifier.
    Requires no ML model — runs in < 5ms.
    Task 21.1 — acoustic emotion detection.
    """

    # Tuned thresholds for 16kHz int16 PCM
    HIGH_ENERGY   = 8000
    MEDIUM_ENERGY = 3000
    HIGH_ZCR      = 0.15
    HIGH_RATE     = 4.5   # syllables/sec

    def detect(self, audio_bytes: bytes) -> EmotionResult:
        """Classify emotion from raw audio bytes."""
        decoded = _extract_pcm(audio_bytes)
        if decoded is None:
            # Non-WAV audio (webm etc.) — return neutral with low confidence
            return EmotionResult(
                emotion=Emotion.NEUTRAL,
                confidence=0.4,
                should_escalate=False,
                prosody_hint=self._prosody(Emotion.NEUTRAL),
            )

        samples, sr = decoded
        energy   = _rms_energy(samples)
        zcr      = _zero_crossing_rate(samples)
        rate     = _speaking_rate_proxy(samples, sr)

        emotion, confidence = self._classify(energy, zcr, rate)
        should_escalate = emotion in (Emotion.ANGRY, Emotion.FRUSTRATED) and confidence > 0.70

        if should_escalate:
            logger.warning("Emotion escalation triggered: %s confidence=%.2f", emotion, confidence)

        return EmotionResult(
            emotion=emotion,
            confidence=round(confidence, 3),
            should_escalate=should_escalate,
            prosody_hint=self._prosody(emotion),
        )

    def _classify(self, energy: float, zcr: float, rate: float) -> Tuple[Emotion, float]:
        if energy > self.HIGH_ENERGY and rate > self.HIGH_RATE:
            # High energy + fast rate = angry
            conf = min(0.95, 0.65 + (energy / self.HIGH_ENERGY) * 0.15)
            return Emotion.ANGRY, conf
        if energy > self.HIGH_ENERGY:
            # High energy, normal rate = frustrated
            conf = min(0.90, 0.60 + (energy / self.HIGH_ENERGY) * 0.12)
            return Emotion.FRUSTRATED, conf
        if energy > self.MEDIUM_ENERGY and rate > self.HIGH_RATE and zcr > self.HIGH_ZCR:
            # Medium-high energy, high pitch proxy, fast = happy
            return Emotion.HAPPY, 0.72
        if zcr > self.HIGH_ZCR and energy < self.MEDIUM_ENERGY:
            # High ZCR, low energy = confused / questioning
            return Emotion.CONFUSED, 0.65
        return Emotion.NEUTRAL, 0.80

    def _prosody(self, emotion: Emotion) -> dict:
        """
        Task 21.2 — prosody hints for TTS.
        Returns adjustments Edge TTS / Piper can apply.
        """
        hints = {
            Emotion.NEUTRAL:    {"rate": "+0%",   "pitch": "+0Hz",   "volume": "+0%"},
            Emotion.HAPPY:      {"rate": "+10%",  "pitch": "+5Hz",   "volume": "+5%"},
            Emotion.FRUSTRATED: {"rate": "-10%",  "pitch": "-3Hz",   "volume": "+0%",
                                 "style": "empathetic"},
            Emotion.ANGRY:      {"rate": "-15%",  "pitch": "-5Hz",   "volume": "-5%",
                                 "style": "calm"},
            Emotion.CONFUSED:   {"rate": "-5%",   "pitch": "+2Hz",   "volume": "+0%",
                                 "style": "gentle"},
        }
        return hints.get(emotion, hints[Emotion.NEUTRAL])


# Singleton
_detector: Optional[EmotionDetector] = None

def get_emotion_detector() -> EmotionDetector:
    global _detector
    if _detector is None:
        _detector = EmotionDetector()
    return _detector
