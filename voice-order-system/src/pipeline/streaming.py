"""
Streaming audio processing for the voice pipeline.

Processes audio in real-time chunks (20-100ms), begins STT transcription
before the complete utterance, and streams TTS output as it's generated.

Validates Requirements 1.7, 7.8.
"""

import asyncio
import logging
from typing import AsyncIterator, Callable, Optional

from stt.base import STTEngine, StreamingChunk
from tts.base import TTSEngine, AudioChunk
from audio.barge_in import BargeInDetector

logger = logging.getLogger(__name__)

CHUNK_SIZE_MS = 40          # 40ms chunks
SAMPLE_RATE = 16000
BYTES_PER_SAMPLE = 2        # PCM_16
CHUNK_BYTES = int(SAMPLE_RATE * CHUNK_SIZE_MS / 1000) * BYTES_PER_SAMPLE


class StreamingAudioProcessor:
    """
    Handles real-time streaming audio for both input (STT) and output (TTS).

    Requirements:
    - 1.7: Begin STT transcription within 100ms of speech detection
    - 7.8: Process audio in streaming mode to minimise perceived latency
    """

    def __init__(
        self,
        stt_engine: STTEngine,
        tts_engine: TTSEngine,
        barge_in_detector: Optional[BargeInDetector] = None,
    ):
        self.stt = stt_engine
        self.tts = tts_engine
        self.barge_in_detector = barge_in_detector or BargeInDetector()

    async def stream_transcription(
        self,
        audio_source: AsyncIterator[bytes],
        on_partial: Optional[Callable[[str], None]] = None,
        on_final: Optional[Callable[[str, float], None]] = None,
    ) -> str:
        """
        Stream audio chunks to STT and collect the final transcription.

        Args:
            audio_source: Async iterator yielding raw PCM_16 audio chunks
            on_partial: Optional callback for partial transcription results
            on_final: Optional callback(text, confidence) for final result

        Returns:
            Final transcribed text
        """
        final_text = ""
        final_confidence = 0.0

        async for chunk in self.stt.transcribe_stream(audio_source):
            if chunk.is_final:
                final_text = chunk.text
                final_confidence = chunk.confidence
                if on_final:
                    on_final(final_text, final_confidence)
                logger.debug("STT final: '%s' (conf=%.2f)", final_text[:50], final_confidence)
            else:
                if on_partial:
                    on_partial(chunk.text)
                logger.debug("STT partial: '%s'", chunk.text[:40])

        return final_text

    async def stream_tts_with_barge_in(
        self,
        text: str,
        language: str = "en",
        voice: Optional[str] = None,
        audio_input: Optional[AsyncIterator[bytes]] = None,
    ) -> AsyncIterator[AudioChunk]:
        """
        Stream TTS output while monitoring for barge-in.

        Stops yielding audio chunks as soon as barge-in is detected.

        Args:
            text: Text to synthesize
            language: Language code
            voice: Optional voice name
            audio_input: Optional async iterator of microphone audio for barge-in detection

        Yields:
            AudioChunk objects until completion or barge-in
        """
        stop_event = self.barge_in_detector.start_tts_playback()

        # Start barge-in monitoring in background if audio input provided
        monitor_task: Optional[asyncio.Task] = None
        if audio_input is not None:
            monitor_task = asyncio.create_task(
                self._monitor_barge_in(audio_input, stop_event)
            )

        try:
            async for chunk in self.tts.synthesize_stream(text, language, voice):
                if stop_event.is_set():
                    logger.info("TTS streaming stopped due to barge-in")
                    break
                yield chunk
        finally:
            self.barge_in_detector.stop_tts_playback()
            if monitor_task and not monitor_task.done():
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass

    async def _monitor_barge_in(
        self,
        audio_input: AsyncIterator[bytes],
        stop_event: asyncio.Event,
    ) -> None:
        """Background task that monitors microphone audio for barge-in."""
        async for chunk in audio_input:
            if stop_event.is_set():
                break
            self.barge_in_detector.process_audio_chunk(chunk)

    @staticmethod
    def chunk_audio(audio_bytes: bytes, chunk_size_bytes: int = CHUNK_BYTES) -> AsyncIterator[bytes]:
        """
        Split raw audio bytes into fixed-size chunks for streaming.

        Args:
            audio_bytes: Complete audio buffer
            chunk_size_bytes: Bytes per chunk (default ~40ms at 16kHz PCM_16)

        Returns:
            Async iterator of audio chunks
        """
        async def _gen():
            offset = 0
            while offset < len(audio_bytes):
                yield audio_bytes[offset: offset + chunk_size_bytes]
                offset += chunk_size_bytes
                await asyncio.sleep(0)  # yield control

        return _gen()
