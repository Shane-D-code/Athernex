"""TTS engine package — Piper (primary) + Edge TTS (fallback)."""

from .base import TTSEngine, SynthesisResult, AudioChunk
from .piper_engine import PiperTTSEngine
from .edge_engine import EdgeTTSEngine

__all__ = [
    "TTSEngine",
    "SynthesisResult",
    "AudioChunk",
    "PiperTTSEngine",
    "EdgeTTSEngine",
]
