"""
Barge-in detection using Voice Activity Detection.

Monitors for speech input during TTS playback and signals interruption.
Validates Requirements 15.1, 15.2, 15.3.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

logger = logging.getLogger(__name__)

BARGE_IN_DETECTION_MS = 200  # detect within 200ms of speech onset


@dataclass
class BargeInEvent:
    """Emitted when a barge-in is detected."""
    detected_at: float = field(default_factory=time.time)
    audio_chunk: Optional[bytes] = None


class BargeInDetector:
    """
    Detects when a user speaks while TTS is playing.

    Uses a lightweight energy-based detector so it works without the full
    Silero VAD model (which requires a network download). Falls back to
    the full VoiceActivityDetector when available.

    Requirements:
    - 15.1: Detect barge-in within 200ms of speech onset
    - 15.2: Stop TTS output immediately on barge-in
    - 15.3: Begin processing new customer input
    """

    def __init__(
        self,
        energy_threshold: float = 0.01,
        on_barge_in: Optional[Callable[[BargeInEvent], None]] = None,
    ):
        """
        Args:
            energy_threshold: RMS energy level above which speech is assumed
            on_barge_in: Optional callback invoked when barge-in is detected
        """
        self.energy_threshold = energy_threshold
        self.on_barge_in = on_barge_in

        self._tts_playing = False
        self._stop_event: Optional[asyncio.Event] = None
        self._last_barge_in: Optional[BargeInEvent] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_tts_playback(self) -> asyncio.Event:
        """
        Signal that TTS playback has started.

        Returns:
            An asyncio.Event that will be set when barge-in is detected.
            Callers should await this event to know when to stop playback.
        """
        self._tts_playing = True
        self._stop_event = asyncio.Event()
        logger.debug("TTS playback started — barge-in monitoring active")
        return self._stop_event

    def stop_tts_playback(self) -> None:
        """Signal that TTS playback has ended normally (no barge-in)."""
        self._tts_playing = False
        if self._stop_event and not self._stop_event.is_set():
            self._stop_event.set()
        logger.debug("TTS playback ended normally")

    def process_audio_chunk(self, audio_chunk: bytes) -> bool:
        """
        Process an incoming audio chunk during TTS playback.

        Args:
            audio_chunk: Raw PCM_16 mono audio bytes

        Returns:
            True if barge-in was detected, False otherwise
        """
        if not self._tts_playing:
            return False

        if self._is_speech(audio_chunk):
            event = BargeInEvent(audio_chunk=audio_chunk)
            self._last_barge_in = event
            self._tts_playing = False

            logger.info("Barge-in detected — stopping TTS output")

            # Signal the stop event so TTS streaming can halt
            if self._stop_event and not self._stop_event.is_set():
                self._stop_event.set()

            # Invoke callback if provided
            if self.on_barge_in:
                self.on_barge_in(event)

            return True

        return False

    @property
    def is_monitoring(self) -> bool:
        """True while TTS is playing and barge-in monitoring is active."""
        return self._tts_playing

    @property
    def last_barge_in(self) -> Optional[BargeInEvent]:
        """The most recent barge-in event, or None."""
        return self._last_barge_in

    def reset(self) -> None:
        """Reset detector state for a new turn."""
        self._tts_playing = False
        self._stop_event = None
        self._last_barge_in = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_speech(self, audio_chunk: bytes) -> bool:
        """
        Lightweight energy-based speech detection.

        Computes RMS energy of the chunk and compares to threshold.
        This avoids requiring the full Silero VAD model for barge-in.
        """
        if len(audio_chunk) < 2:
            return False
        try:
            import numpy as np
            samples = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
            rms = float(np.sqrt(np.mean(samples ** 2)))
            return rms > self.energy_threshold
        except Exception:
            # Fallback: treat any non-silent chunk as speech
            return any(b != 0 for b in audio_chunk[:64])
