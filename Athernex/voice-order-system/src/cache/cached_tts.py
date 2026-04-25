"""
Cached wrapper for TTS engines.

Adds transparent TTS audio caching with cache invalidation support.
Validates Requirements 20.2, 20.6.
"""

import logging
from typing import AsyncIterator, List, Optional

from tts.base import TTSEngine, SynthesisResult, AudioChunk
from .tts_cache import TTSCache

logger = logging.getLogger(__name__)

_DEFAULT_VOICE = "default"


class CachedTTSEngine(TTSEngine):
    """
    Wraps any TTSEngine with transparent audio caching.

    Cache key is language:voice:text. Streaming synthesis bypasses the cache
    (only non-streaming synthesize() is cached).
    """

    def __init__(self, engine: TTSEngine, cache: Optional[TTSCache] = None):
        self._engine = engine
        self._cache = cache or TTSCache()

    @property
    def name(self) -> str:
        return f"Cached({self._engine.name})"

    async def synthesize(
        self,
        text: str,
        language: str = "en",
        voice: Optional[str] = None,
    ) -> SynthesisResult:
        voice_key = voice or _DEFAULT_VOICE
        cached_audio = self._cache.get(language, voice_key, text)

        if cached_audio is not None:
            logger.debug("TTS cache hit for '%s' (%s)", text[:30], language)
            # Reconstruct a minimal SynthesisResult from cached bytes
            return SynthesisResult(
                audio_bytes=cached_audio,
                sample_rate=22050,
                format="pcm_16",
                duration=len(cached_audio) / (22050 * 2),
                text=text,
                language=language,
                voice=voice_key,
            )

        result = await self._engine.synthesize(text, language, voice)
        self._cache.put(language, voice_key, text, result.audio_bytes)
        return result

    async def synthesize_stream(
        self,
        text: str,
        language: str = "en",
        voice: Optional[str] = None,
    ) -> AsyncIterator[AudioChunk]:
        # Streaming bypasses cache — delegate directly
        async for chunk in self._engine.synthesize_stream(text, language, voice):
            yield chunk

    async def health_check(self) -> bool:
        return await self._engine.health_check()

    def get_available_voices(self, language: Optional[str] = None) -> List[str]:
        return self._engine.get_available_voices(language)

    def invalidate_cache(self) -> None:
        self._cache.invalidate()
