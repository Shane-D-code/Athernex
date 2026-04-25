"""
Whisper STT engine client for faster-whisper-server.

Connects to the faster-whisper-server REST API running on port 8000.
Supports both batch transcription and streaming via chunked responses.
"""

import io
import wave
import struct
import logging
from typing import AsyncIterator, Optional

import httpx

from .base import STTEngine, TranscriptionResult, StreamingChunk, WordResult

logger = logging.getLogger(__name__)


def _pcm_to_wav(audio_bytes: bytes, sample_rate: int = 16000) -> bytes:
    """Wrap raw PCM_16 mono bytes in a WAV container."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit = 2 bytes
        wf.setframerate(sample_rate)
        wf.writeframes(audio_bytes)
    return buf.getvalue()


class WhisperSTTEngine(STTEngine):
    """
    Client for faster-whisper-server (OpenAI-compatible /v1/audio/transcriptions).

    The server must be running before this client is used.
    Start it with: python scripts/start_whisper.py
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        model: str = "medium",
        language: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.language = language  # None = auto-detect
        self._client = httpx.AsyncClient(timeout=timeout)

    @property
    def name(self) -> str:
        return f"Whisper-{self.model}"

    async def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> TranscriptionResult:
        """Send audio to faster-whisper-server and return full transcription."""
        wav_bytes = _pcm_to_wav(audio_bytes, sample_rate)

        files = {"file": ("audio.wav", wav_bytes, "audio/wav")}
        data = {
            "model": self.model,
            "response_format": "verbose_json",
            "timestamp_granularities[]": "word",
        }
        if self.language:
            data["language"] = self.language

        try:
            response = await self._client.post(
                f"{self.base_url}/v1/audio/transcriptions",
                files=files,
                data=data,
            )
            response.raise_for_status()
            payload = response.json()
            return self._parse_response(payload)
        except httpx.HTTPStatusError as e:
            logger.error("Whisper HTTP error: %s - %s", e.response.status_code, e.response.text)
            raise
        except httpx.RequestError as e:
            logger.error("Whisper connection error: %s", e)
            raise

    async def transcribe_stream(
        self, audio_chunks: AsyncIterator[bytes], sample_rate: int = 16000
    ) -> AsyncIterator[StreamingChunk]:
        """
        Accumulate audio chunks and transcribe when a pause is detected.

        For now this buffers all chunks and does a single transcription.
        A future version can use VAD to split on silence boundaries.
        """
        buffer = bytearray()
        async for chunk in audio_chunks:
            buffer.extend(chunk)

        if buffer:
            result = await self.transcribe(bytes(buffer), sample_rate)
            yield StreamingChunk(
                text=result.text,
                is_final=True,
                words=result.words,
                confidence=result.confidence,
            )

    async def health_check(self) -> bool:
        """Ping the /health endpoint."""
        try:
            r = await self._client.get(f"{self.base_url}/health", timeout=3.0)
            return r.status_code == 200
        except Exception:
            return False

    def _parse_response(self, payload: dict) -> TranscriptionResult:
        """Parse verbose_json response from faster-whisper-server."""
        text = payload.get("text", "").strip()
        language = payload.get("language", "en")
        duration = payload.get("duration", 0.0)

        words: list[WordResult] = []
        for w in payload.get("words", []):
            words.append(WordResult(
                word=w.get("word", ""),
                start=w.get("start", 0.0),
                end=w.get("end", 0.0),
                confidence=w.get("probability", 1.0),
                language=language,
            ))

        # Fallback: parse from segments if words not present
        if not words:
            for seg in payload.get("segments", []):
                for w in seg.get("words", []):
                    words.append(WordResult(
                        word=w.get("word", ""),
                        start=w.get("start", 0.0),
                        end=w.get("end", 0.0),
                        confidence=w.get("probability", 1.0),
                        language=language,
                    ))

        confidence = (
            sum(w.confidence for w in words) / len(words) if words else 0.8
        )

        return TranscriptionResult(
            text=text,
            language=language,
            language_probability=payload.get("language_probability", 1.0),
            words=words,
            duration=duration,
            confidence=confidence,
        )

    async def close(self):
        await self._client.aclose()
