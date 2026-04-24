"""
Vosk STT engine client.

Connects to a Vosk REST API wrapper running on port 8001.
Vosk is used as the fallback when faster-whisper-server is unavailable.
"""

import json
import logging
from typing import AsyncIterator, Optional

import httpx

from .base import STTEngine, TranscriptionResult, StreamingChunk, WordResult

logger = logging.getLogger(__name__)

# Vosk language model mapping
VOSK_LANGUAGE_MODELS = {
    "hi": "vosk-model-hi-0.22",
    "en": "vosk-model-en-in-0.5",
    "kn": "vosk-model-small-kn-0.1",
    "mr": "vosk-model-small-mr-0.1",
}


class VoskSTTEngine(STTEngine):
    """
    Client for the Vosk REST API wrapper (port 8001).

    Start the Vosk server with: python scripts/start_vosk.py
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8001",
        language: str = "hi",
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.language = language
        self._client = httpx.AsyncClient(timeout=timeout)

    @property
    def name(self) -> str:
        return f"Vosk-{self.language}"

    async def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> TranscriptionResult:
        """Send audio to Vosk REST API and return transcription."""
        files = {"file": ("audio.raw", audio_bytes, "application/octet-stream")}
        data = {
            "language": self.language,
            "sample_rate": str(sample_rate),
        }

        try:
            response = await self._client.post(
                f"{self.base_url}/transcribe",
                files=files,
                data=data,
            )
            response.raise_for_status()
            payload = response.json()
            return self._parse_response(payload)
        except httpx.HTTPStatusError as e:
            logger.error("Vosk HTTP error: %s - %s", e.response.status_code, e.response.text)
            raise
        except httpx.RequestError as e:
            logger.error("Vosk connection error: %s", e)
            raise

    async def transcribe_stream(
        self, audio_chunks: AsyncIterator[bytes], sample_rate: int = 16000
    ) -> AsyncIterator[StreamingChunk]:
        """Stream audio to Vosk and yield partial results."""
        buffer = bytearray()
        async for chunk in audio_chunks:
            buffer.extend(chunk)
            # Yield partial result every 2 seconds of audio (32000 bytes at 16kHz PCM16)
            if len(buffer) >= 32000:
                result = await self.transcribe(bytes(buffer), sample_rate)
                buffer.clear()
                yield StreamingChunk(
                    text=result.text,
                    is_final=False,
                    words=result.words,
                    confidence=result.confidence,
                )

        # Final chunk
        if buffer:
            result = await self.transcribe(bytes(buffer), sample_rate)
            yield StreamingChunk(
                text=result.text,
                is_final=True,
                words=result.words,
                confidence=result.confidence,
            )

    async def health_check(self) -> bool:
        try:
            r = await self._client.get(f"{self.base_url}/health", timeout=3.0)
            return r.status_code == 200
        except Exception:
            return False

    def _parse_response(self, payload: dict) -> TranscriptionResult:
        text = payload.get("text", "").strip()
        language = payload.get("language", self.language)
        words: list[WordResult] = []

        for w in payload.get("result", []):
            words.append(WordResult(
                word=w.get("word", ""),
                start=w.get("start", 0.0),
                end=w.get("end", 0.0),
                confidence=w.get("conf", 0.8),
                language=language,
            ))

        confidence = (
            sum(w.confidence for w in words) / len(words) if words else 0.6
        )

        return TranscriptionResult(
            text=text,
            language=language,
            language_probability=0.9,
            words=words,
            duration=words[-1].end if words else 0.0,
            confidence=confidence,
        )

    async def close(self):
        await self._client.aclose()
