"""
Audio signal processing utilities.

Includes noise suppression and basic echo cancellation.
"""

import logging
import numpy as np
from scipy import signal

logger = logging.getLogger(__name__)


class AudioProcessor:
    """
    Audio signal processor for noise suppression and echo cancellation.
    
    Targets:
    - Noise suppression: 15dB reduction
    - SNR: >20dB
    - Latency: <20ms
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        noise_reduction_db: float = 15.0,
    ):
        """
        Initialize audio processor.

        Args:
            sample_rate: Audio sample rate in Hz
            noise_reduction_db: Target noise reduction in dB
        """
        self.sample_rate = sample_rate
        self.noise_reduction_db = noise_reduction_db
        
        # Noise profile (estimated from first few frames)
        self.noise_profile = None
        self.noise_frames_collected = 0
        self.noise_frames_needed = 10

        logger.info("AudioProcessor initialized: %dHz, %.1fdB noise reduction",
                    sample_rate, noise_reduction_db)

    def suppress_noise(self, audio_float32: np.ndarray) -> np.ndarray:
        """
        Apply noise suppression using spectral subtraction.

        Args:
            audio_float32: Audio samples as float32 array

        Returns:
            Noise-suppressed audio as float32 array
        """
        # Simple spectral subtraction
        # In production, use more sophisticated methods like Wiener filtering

        # Estimate noise profile from first few frames
        if self.noise_profile is None and self.noise_frames_collected < self.noise_frames_needed:
            if self.noise_profile is None:
                self.noise_profile = np.abs(np.fft.rfft(audio_float32))
            else:
                self.noise_profile += np.abs(np.fft.rfft(audio_float32))
            self.noise_frames_collected += 1
            
            if self.noise_frames_collected == self.noise_frames_needed:
                self.noise_profile /= self.noise_frames_needed
                logger.debug("Noise profile estimated")
            
            return audio_float32  # Return original during calibration

        if self.noise_profile is None:
            return audio_float32  # No noise profile yet

        # Apply spectral subtraction
        spectrum = np.fft.rfft(audio_float32)
        magnitude = np.abs(spectrum)
        phase = np.angle(spectrum)

        # Subtract noise profile
        noise_reduction_factor = 10 ** (-self.noise_reduction_db / 20)
        magnitude_clean = np.maximum(magnitude - self.noise_profile * noise_reduction_factor, 0)

        # Reconstruct signal
        spectrum_clean = magnitude_clean * np.exp(1j * phase)
        audio_clean = np.fft.irfft(spectrum_clean, n=len(audio_float32))

        return audio_clean.astype(np.float32)

    def apply_highpass_filter(self, audio_float32: np.ndarray, cutoff_hz: float = 80.0) -> np.ndarray:
        """
        Apply high-pass filter to remove low-frequency noise.

        Args:
            audio_float32: Audio samples as float32 array
            cutoff_hz: Cutoff frequency in Hz

        Returns:
            Filtered audio as float32 array
        """
        # Design Butterworth high-pass filter
        nyquist = self.sample_rate / 2
        normalized_cutoff = cutoff_hz / nyquist
        b, a = signal.butter(4, normalized_cutoff, btype='high')

        # Apply filter
        filtered = signal.filtfilt(b, a, audio_float32)
        return filtered.astype(np.float32)

    def normalize_volume(self, audio_float32: np.ndarray, target_level: float = 0.3) -> np.ndarray:
        """
        Normalize audio volume to target level.

        Args:
            audio_float32: Audio samples as float32 array
            target_level: Target RMS level (0.0-1.0)

        Returns:
            Normalized audio as float32 array
        """
        # Calculate current RMS
        rms = np.sqrt(np.mean(audio_float32 ** 2))
        
        if rms < 1e-6:  # Silence
            return audio_float32

        # Calculate gain
        gain = target_level / rms
        
        # Limit gain to prevent clipping
        gain = min(gain, 1.0 / np.max(np.abs(audio_float32)))

        # Apply gain
        normalized = audio_float32 * gain
        return normalized.astype(np.float32)

    def process(self, audio_bytes: bytes) -> bytes:
        """
        Apply full audio processing pipeline.

        Args:
            audio_bytes: Raw PCM_16 mono audio bytes

        Returns:
            Processed audio as PCM_16 bytes
        """
        # Convert to float32
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0

        # Apply processing
        audio_float32 = self.apply_highpass_filter(audio_float32)
        audio_float32 = self.suppress_noise(audio_float32)
        audio_float32 = self.normalize_volume(audio_float32)

        # Convert back to int16
        audio_int16 = (audio_float32 * 32768.0).astype(np.int16)
        return audio_int16.tobytes()

    def reset(self):
        """Reset processor state."""
        self.noise_profile = None
        self.noise_frames_collected = 0
        logger.debug("AudioProcessor state reset")
