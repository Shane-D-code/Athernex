"""
Piper TTS engine for high-quality offline speech synthesis.

Uses Piper TTS with Indian language models (Hindi, English-IN).
Runs locally without API calls.
"""

import io
import wave
import logging
from typing import AsyncIterator, Optional
from pathlib import Path

from piper import PiperVoice

from .base import TTSEngine, SynthesisResult, AudioChunk

logger = logging.getLogger(__name__)


# Voice model mappings for Indian languages
PIPER_VOICES = {
    "hi": "hi_IN-medium",  # Hindi
    "en": "en_IN-medium",  # English (India)
    "kn": "en_IN-medium",  # Kannada (fallback to English-IN)
    "mr": "en_IN-medium",  # Marathi (fallback to English-IN)
}


class PiperTTSEngine(TTSEngine):
    """
    Piper TTS engine for offline speech synthesis.
    
    Models are downloaded automatically on first use.
    Supports Hindi and English (India) voices.
    """

    def __init__(
        self,
        models_dir: Optional[Path] = None,
        sample_rate: int = 22050,
    ):
        self.models_dir = models_dir or Path(__file__).parent.parent.parent / "models" / "piper"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.sample_rate = sample_rate
        self._voices: dict[str, PiperVoice] = {}

    @property
    def name(self) -> str:
        return "Piper-TTS"

    def _get_voice(self, language: str) -> PiperVoice:
        """Load or retrieve cached voice model."""
        voice_name = PIPER_VOICES.get(language, "en_IN-medium")
        
        if voice_name not in self._voices:
            logger.info("Loading Piper voice: %s", voice_name)
            try:
                # For now, use the default voice loading
                # Piper models need to be manually downloaded
                # Download from: https://github.com/rhasspy/piper/releases
                voice = PiperVoice.load(voice_name, use_cuda=False)
                self._voices[voice_name] = voice
            except Exception as e:
                logger.warning("Piper voice %s not available: %s", voice_name, e)
                # Piper requires manual model download
                # For MVP, we'll rely on Edge TTS as fallback
                raise RuntimeError(
                    f"Piper voice '{voice_name}' not found. "
                    "Download models from: https://github.com/rhasspy/piper/releases"
                )
        
        return self._voices[voice_name]

    async def synthesize(
        self, 
        text: str, 
        language: str = "en", 
        voice: Optional[str] = None
    ) -> SynthesisResult:
        """Synthesize text to audio using Piper."""
        try:
            piper_voice = self._get_voice(language)
            
            # Synthesize audio
            audio_chunks = []
            for audio_bytes in piper_voice.synthesize_stream_raw(text):
                audio_chunks.append(audio_bytes)
            
            audio_data = b"".join(audio_chunks)
            
            # Calculate duration
            num_samples = len(audio_data) // 2  # 16-bit = 2 bytes per sample
            duration = num_samples / self.sample_rate
            
            return SynthesisResult(
                audio_bytes=audio_data,
                sample_rate=self.sample_rate,
                format="pcm_16",
                duration=duration,
                text=text,
                language=language,
                voice=voice or PIPER_VOICES.get(language, "en_IN-medium"),
            )
        except Exception as e:
            logger.error("Piper synthesis failed: %s", e)
            raise

    async def synthesize_stream(
        self, 
        text: str, 
        language: str = "en", 
        voice: Optional[str] = None
    ) -> AsyncIterator[AudioChunk]:
        """Stream synthesized audio in chunks."""
        try:
            piper_voice = self._get_voice(language)
            
            chunk_count = 0
            for audio_bytes in piper_voice.synthesize_stream_raw(text):
                chunk_count += 1
                yield AudioChunk(
                    audio_bytes=audio_bytes,
                    sample_rate=self.sample_rate,
                    format="pcm_16",
                    is_final=False,
                )
            
            # Final chunk marker
            yield AudioChunk(
                audio_bytes=b"",
                sample_rate=self.sample_rate,
                format="pcm_16",
                is_final=True,
            )
            
            logger.debug("Streamed %d audio chunks", chunk_count)
        except Exception as e:
            logger.error("Piper streaming failed: %s", e)
            raise

    async def health_check(self) -> bool:
        """Check if Piper is available."""
        try:
            # Try to load a voice
            self._get_voice("en")
            return True
        except Exception:
            return False

    def get_available_voices(self, language: Optional[str] = None) -> list[str]:
        """Get available Piper voices."""
        if language:
            voice = PIPER_VOICES.get(language)
            return [voice] if voice else []
        return list(set(PIPER_VOICES.values()))
