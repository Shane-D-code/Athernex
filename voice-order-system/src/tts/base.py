"""Abstract base class for TTS engines."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Optional


@dataclass
class AudioChunk:
    """A chunk of synthesized audio."""
    audio_bytes: bytes
    sample_rate: int
    format: str  # "pcm_16", "mp3", "wav"
    is_final: bool = False


@dataclass
class SynthesisResult:
    """Complete synthesis result from TTS engine."""
    audio_bytes: bytes
    sample_rate: int
    format: str
    duration: float  # seconds
    text: str
    language: str
    voice: str


class TTSEngine(ABC):
    """Abstract interface for Text-to-Speech engines."""

    @abstractmethod
    async def synthesize(
        self, 
        text: str, 
        language: str = "en", 
        voice: Optional[str] = None
    ) -> SynthesisResult:
        """
        Synthesize text to speech audio.

        Args:
            text: Text to synthesize
            language: Language code (e.g., "en", "hi", "kn", "mr")
            voice: Optional specific voice name

        Returns:
            SynthesisResult with audio bytes and metadata
        """

    @abstractmethod
    async def synthesize_stream(
        self, 
        text: str, 
        language: str = "en", 
        voice: Optional[str] = None
    ) -> AsyncIterator[AudioChunk]:
        """
        Stream synthesized audio in chunks.

        Args:
            text: Text to synthesize
            language: Language code
            voice: Optional specific voice name

        Yields:
            AudioChunk with partial audio data
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the TTS service is reachable and healthy."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable engine name."""

    @abstractmethod
    def get_available_voices(self, language: Optional[str] = None) -> list[str]:
        """
        Get list of available voices.

        Args:
            language: Optional language filter

        Returns:
            List of voice names
        """
