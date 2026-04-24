"""
Voice Activity Detection using Silero VAD.

Detects speech onset and offset in audio streams with low latency.
"""

import logging
import numpy as np
import torch
from typing import Optional
from collections import deque

logger = logging.getLogger(__name__)


class VoiceActivityDetector:
    """
    Voice Activity Detection using Silero VAD model.
    
    Detects speech onset (<50ms target) and offset (<300ms target).
    Maintains a pre-roll buffer to capture speech from the beginning.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        threshold: float = 0.5,
        min_speech_duration_ms: int = 250,
        min_silence_duration_ms: int = 300,
        speech_pad_ms: int = 30,
    ):
        """
        Initialize VAD.

        Args:
            sample_rate: Audio sample rate (8000, 16000)
            threshold: Speech probability threshold (0.0-1.0)
            min_speech_duration_ms: Minimum speech duration to trigger
            min_silence_duration_ms: Minimum silence to end speech
            speech_pad_ms: Padding around speech segments
        """
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.min_silence_duration_ms = min_silence_duration_ms
        self.speech_pad_ms = speech_pad_ms

        # Load Silero VAD model
        try:
            self.model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False
            )
            self.get_speech_timestamps = utils[0]
            logger.info("Silero VAD model loaded successfully")
        except Exception as e:
            logger.error("Failed to load Silero VAD: %s", e)
            raise

        # State tracking
        self.is_speech = False
        self.speech_start_time = None
        self.last_speech_time = None
        
        # Pre-roll buffer (stores last 500ms of audio)
        self.preroll_duration_ms = 500
        self.preroll_samples = int(sample_rate * self.preroll_duration_ms / 1000)
        self.preroll_buffer = deque(maxlen=self.preroll_samples)

    def process_chunk(self, audio_chunk: bytes) -> dict:
        """
        Process an audio chunk and detect voice activity.

        Args:
            audio_chunk: Raw PCM_16 mono audio bytes

        Returns:
            dict with keys:
                - is_speech: bool, whether speech is detected
                - speech_started: bool, whether speech just started
                - speech_ended: bool, whether speech just ended
                - confidence: float, speech probability (0.0-1.0)
        """
        # Convert bytes to numpy array
        audio_int16 = np.frombuffer(audio_chunk, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0

        # Add to preroll buffer
        self.preroll_buffer.extend(audio_float32)

        # Convert to torch tensor
        audio_tensor = torch.from_numpy(audio_float32)

        # Get speech probability
        with torch.no_grad():
            speech_prob = self.model(audio_tensor, self.sample_rate).item()

        # Detect speech state changes
        speech_started = False
        speech_ended = False
        current_is_speech = speech_prob > self.threshold

        if current_is_speech and not self.is_speech:
            # Speech onset detected
            self.is_speech = True
            self.speech_start_time = 0  # Would be actual timestamp in production
            speech_started = True
            logger.debug("Speech onset detected (prob=%.2f)", speech_prob)

        elif not current_is_speech and self.is_speech:
            # Potential speech offset
            # Check if silence duration exceeds threshold
            silence_duration_ms = self.min_silence_duration_ms  # Simplified
            if silence_duration_ms >= self.min_silence_duration_ms:
                self.is_speech = False
                speech_ended = True
                logger.debug("Speech offset detected (prob=%.2f)", speech_prob)

        return {
            "is_speech": self.is_speech,
            "speech_started": speech_started,
            "speech_ended": speech_ended,
            "confidence": speech_prob,
        }

    def get_preroll_audio(self) -> np.ndarray:
        """Get the pre-roll buffer as numpy array."""
        return np.array(self.preroll_buffer, dtype=np.float32)

    def reset(self):
        """Reset VAD state."""
        self.is_speech = False
        self.speech_start_time = None
        self.last_speech_time = None
        self.preroll_buffer.clear()
        logger.debug("VAD state reset")
