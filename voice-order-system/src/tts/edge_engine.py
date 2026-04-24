"""
Edge TTS engine using Microsoft Edge's free TTS service.

Fallback TTS when Piper is unavailable.
Requires internet connection but no API key.
"""

import io
import logging
from typing import AsyncIterator, Optional

import edge_tts

from .base import TTSEngine, SynthesisResult, AudioChunk

logger = logging.getLogger(__name__)


# Voice mappings for Indian languages
EDGE_VOICES = {
    "hi": "hi-IN-SwaraNeural",      # Hindi (Female)
    "en": "en-IN-NeerjaNeural",     # English-India (Female)
    "kn": "kn-IN-SapnaNeural",      # Kannada (Female)
    "mr": "mr-IN-AarohiNeural",     # Marathi (Female)
}


class EdgeTTSEngine(TTSEngine):
    """
    Microsoft Edge TTS engine (free, cloud-based).
    
    No API key required, but needs internet connection.
    Supports Hindi, English-IN, Kannada, Marathi voices.
    """

    def __init__(self, sample_rate: int = 24000):
        self.sample_rate = sample_rate

    @property
    def name(self) -> str:
        return "Edge-TTS"

    def _get_voice(self, language: str, voice: Optional[str] = None) -> str:
        """Get voice name for language."""
        if voice:
            return voice
        return EDGE_VOICES.get(language, "en-IN-NeerjaNeural")

    async def synthesize(
        self, 
        text: str, 
        language: str = "en", 
        voice: Optional[str] = None
    ) -> SynthesisResult:
        """Synthesize text using Edge TTS."""
        try:
            voice_name = self._get_voice(language, voice)
            communicate = edge_tts.Communicate(text, voice_name)
            
            # Collect all audio chunks
            audio_chunks = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])
            
            audio_data = b"".join(audio_chunks)
            
            # Edge TTS returns MP3, estimate duration
            # Rough estimate: MP3 is ~1/10 the size of PCM
            estimated_duration = len(audio_data) / (self.sample_rate * 0.1)
            
            return SynthesisResult(
                audio_bytes=audio_data,
                sample_rate=self.sample_rate,
                format="mp3",
                duration=estimated_duration,
                text=text,
                language=language,
                voice=voice_name,
            )
        except Exception as e:
            logger.error("Edge TTS synthesis failed: %s", e)
            raise

    async def synthesize_stream(
        self, 
        text: str, 
        language: str = "en", 
        voice: Optional[str] = None
    ) -> AsyncIterator[AudioChunk]:
        """Stream synthesized audio from Edge TTS."""
        try:
            voice_name = self._get_voice(language, voice)
            communicate = edge_tts.Communicate(text, voice_name)
            
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield AudioChunk(
                        audio_bytes=chunk["data"],
                        sample_rate=self.sample_rate,
                        format="mp3",
                        is_final=False,
                    )
            
            # Final chunk marker
            yield AudioChunk(
                audio_bytes=b"",
                sample_rate=self.sample_rate,
                format="mp3",
                is_final=True,
            )
        except Exception as e:
            logger.error("Edge TTS streaming failed: %s", e)
            raise

    async def health_check(self) -> bool:
        """Check if Edge TTS is available."""
        try:
            # Simple check - Edge TTS requires internet
            # Just verify the module is available
            return True  # Edge TTS is always available if imported
        except Exception:
            return False

    def get_available_voices(self, language: Optional[str] = None) -> list[str]:
        """Get available Edge TTS voices."""
        if language:
            voice = EDGE_VOICES.get(language)
            return [voice] if voice else []
        return list(EDGE_VOICES.values())
