"""STT engine package — Whisper (primary) + Vosk (fallback)."""

from .base import STTEngine, TranscriptionResult, StreamingChunk, WordResult
from .whisper_engine import WhisperSTTEngine
from .vosk_engine import VoskSTTEngine

__all__ = [
    "STTEngine",
    "TranscriptionResult",
    "StreamingChunk",
    "WordResult",
    "WhisperSTTEngine",
    "VoskSTTEngine",
]
