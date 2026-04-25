"""Abstract base class for STT engines."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, List, Optional


@dataclass
class WordResult:
    """A single transcribed word with timing and confidence."""
    word: str
    start: float          # seconds
    end: float            # seconds
    confidence: float     # 0.0 - 1.0
    language: Optional[str] = None


@dataclass
class TranscriptionResult:
    """Full transcription result from STT engine."""
    text: str
    language: str
    language_probability: float
    words: List[WordResult] = field(default_factory=list)
    duration: float = 0.0
    # Utterance-level confidence (mean of word confidences)
    confidence: float = 0.0

    def __post_init__(self):
        if self.words and self.confidence == 0.0:
            self.confidence = sum(w.confidence for w in self.words) / len(self.words)


@dataclass
class StreamingChunk:
    """Partial result from streaming transcription."""
    text: str
    is_final: bool
    words: List[WordResult] = field(default_factory=list)
    confidence: float = 0.0


class STTEngine(ABC):
    """Abstract interface for Speech-to-Text engines."""

    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> TranscriptionResult:
        """
        Transcribe audio bytes to text.

        Args:
            audio_bytes: Raw PCM_16 mono audio bytes
            sample_rate: Audio sample rate in Hz (default 16000)

        Returns:
            TranscriptionResult with text, language, words, and confidence
        """

    @abstractmethod
    async def transcribe_stream(
        self, audio_chunks: AsyncIterator[bytes], sample_rate: int = 16000
    ) -> AsyncIterator[StreamingChunk]:
        """
        Stream audio chunks and yield partial transcription results.

        Args:
            audio_chunks: Async iterator of raw PCM_16 audio chunks
            sample_rate: Audio sample rate in Hz

        Yields:
            StreamingChunk with partial text and is_final flag
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the STT service is reachable and healthy."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable engine name."""
