"""
Audio buffer manager for streaming audio processing.

Handles audio chunk buffering, format conversion, and memory management.
"""

import logging
import numpy as np
from collections import deque
from typing import Optional

logger = logging.getLogger(__name__)


class AudioBufferManager:
    """
    Manages audio buffers for streaming processing.
    
    Supports 16kHz sample rate, PCM_16 encoding, mono channel.
    Handles chunk size management (20-100ms) and overflow protection.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_duration_ms: int = 30,
        max_buffer_duration_ms: int = 10000,
    ):
        """
        Initialize audio buffer manager.

        Args:
            sample_rate: Audio sample rate in Hz
            chunk_duration_ms: Target chunk duration in milliseconds
            max_buffer_duration_ms: Maximum buffer duration before overflow
        """
        self.sample_rate = sample_rate
        self.chunk_duration_ms = chunk_duration_ms
        self.max_buffer_duration_ms = max_buffer_duration_ms

        # Calculate sizes
        self.chunk_size = int(sample_rate * chunk_duration_ms / 1000)
        self.max_buffer_size = int(sample_rate * max_buffer_duration_ms / 1000)

        # Buffer storage (stores PCM_16 samples as int16)
        self.buffer = deque(maxlen=self.max_buffer_size)
        
        logger.info(
            "AudioBufferManager initialized: %dHz, %dms chunks (%d samples)",
            sample_rate, chunk_duration_ms, self.chunk_size
        )

    def add_audio(self, audio_bytes: bytes) -> None:
        """
        Add audio bytes to the buffer.

        Args:
            audio_bytes: Raw PCM_16 mono audio bytes
        """
        # Convert bytes to int16 samples
        audio_samples = np.frombuffer(audio_bytes, dtype=np.int16)
        
        # Add to buffer
        self.buffer.extend(audio_samples)
        
        # Check for overflow
        if len(self.buffer) >= self.max_buffer_size:
            logger.warning("Audio buffer overflow, dropping oldest samples")

    def get_chunk(self, chunk_size: Optional[int] = None) -> Optional[bytes]:
        """
        Get a chunk of audio from the buffer.

        Args:
            chunk_size: Number of samples to retrieve (default: configured chunk_size)

        Returns:
            Audio bytes or None if insufficient data
        """
        if chunk_size is None:
            chunk_size = self.chunk_size

        if len(self.buffer) < chunk_size:
            return None

        # Extract chunk
        chunk_samples = []
        for _ in range(chunk_size):
            if self.buffer:
                chunk_samples.append(self.buffer.popleft())
            else:
                break

        # Convert to bytes
        chunk_array = np.array(chunk_samples, dtype=np.int16)
        return chunk_array.tobytes()

    def get_all(self) -> bytes:
        """Get all buffered audio and clear the buffer."""
        if not self.buffer:
            return b""

        # Convert all samples to bytes
        all_samples = np.array(list(self.buffer), dtype=np.int16)
        self.buffer.clear()
        return all_samples.tobytes()

    def clear(self) -> None:
        """Clear the buffer."""
        self.buffer.clear()
        logger.debug("Audio buffer cleared")

    def get_duration_ms(self) -> float:
        """Get current buffer duration in milliseconds."""
        return (len(self.buffer) / self.sample_rate) * 1000

    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return len(self.buffer) == 0

    def is_full(self) -> bool:
        """Check if buffer is at capacity."""
        return len(self.buffer) >= self.max_buffer_size

    @staticmethod
    def bytes_to_float32(audio_bytes: bytes) -> np.ndarray:
        """Convert PCM_16 bytes to float32 numpy array."""
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        return audio_int16.astype(np.float32) / 32768.0

    @staticmethod
    def float32_to_bytes(audio_float32: np.ndarray) -> bytes:
        """Convert float32 numpy array to PCM_16 bytes."""
        audio_int16 = (audio_float32 * 32768.0).astype(np.int16)
        return audio_int16.tobytes()
