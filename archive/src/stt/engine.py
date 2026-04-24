"""
STT Engine implementations.
Whisper (primary) and Vosk (fallback) for multilingual speech-to-text.
Uses faster-whisper for GPU-accelerated inference on RTX 4060.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Optional

import numpy as np

from src.models import (
    STTResult,
    WordResult,
    SupportedLanguage,
)
from src.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Language mapping helpers
# ──────────────────────────────────────────────

# Whisper language codes → our SupportedLanguage enum
_WHISPER_LANG_MAP: dict[str, SupportedLanguage] = {
    "hi": SupportedLanguage.HINDI,
    "kn": SupportedLanguage.KANNADA,
    "mr": SupportedLanguage.MARATHI,
    "en": SupportedLanguage.ENGLISH,
    "hindi": SupportedLanguage.HINDI,
    "kannada": SupportedLanguage.KANNADA,
    "marathi": SupportedLanguage.MARATHI,
    "english": SupportedLanguage.ENGLISH,
}


def _map_language(lang_code: str) -> SupportedLanguage:
    """Map a Whisper language code to SupportedLanguage, default to English."""
    return _WHISPER_LANG_MAP.get(lang_code.lower(), SupportedLanguage.ENGLISH)


# ──────────────────────────────────────────────
# Abstract base
# ──────────────────────────────────────────────

class STTEngineBase(ABC):
    """Abstract base class for STT engines."""

    @abstractmethod
    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> STTResult:
        """Transcribe audio data to text with word-level confidence."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the STT engine is ready."""
        ...


# ──────────────────────────────────────────────
# Whisper implementation (primary)
# ──────────────────────────────────────────────

class WhisperSTTEngine(STTEngineBase):
    """
    Whisper STT using faster-whisper for GPU-accelerated inference.
    Optimised for RTX 4060 8GB — uses medium model (~2GB VRAM).
    """

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._model = None
        self._model_loaded = False

    # ── lazy model loading ──────────────────────

    def _load_model(self):
        """Load the Whisper model on first use (lazy init saves VRAM when idle)."""
        if self._model_loaded:
            return

        from faster_whisper import WhisperModel

        cfg = self._settings.stt
        logger.info(
            "Loading Whisper model=%s device=%s compute=%s",
            cfg.whisper_model, cfg.whisper_device, cfg.whisper_compute_type,
        )

        start = time.perf_counter()
        self._model = WhisperModel(
            cfg.whisper_model,
            device=cfg.whisper_device,
            compute_type=cfg.whisper_compute_type,
        )
        elapsed = (time.perf_counter() - start) * 1000
        self._model_loaded = True
        logger.info("Whisper model loaded in %.0f ms", elapsed)

    # ── public API ──────────────────────────────

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> STTResult:
        """
        Transcribe audio using Whisper.

        Args:
            audio_data: Audio samples as float32 numpy array, mono, 16kHz.
            sample_rate: Sample rate (must be 16000).

        Returns:
            STTResult with transcription, word-level confidence, and language info.
        """
        self._load_model()
        cfg = self._settings.stt

        start = time.perf_counter()

        # Run Whisper inference
        segments, info = self._model.transcribe(
            audio_data,
            beam_size=cfg.whisper_beam_size,
            language=cfg.whisper_language,  # None = auto-detect
            word_timestamps=True,
            vad_filter=True,
        )

        # Collect results from generator
        words: list[WordResult] = []
        full_text_parts: list[str] = []

        for segment in segments:
            full_text_parts.append(segment.text.strip())
            if segment.words:
                for w in segment.words:
                    words.append(WordResult(
                        word=w.word.strip(),
                        confidence=round(w.probability, 4),
                        language=_map_language(info.language),
                        start_time=round(w.start, 3),
                        end_time=round(w.end, 3),
                    ))

        transcription = " ".join(full_text_parts).strip()
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Calculate utterance-level confidence (mean of word confidences)
        if words:
            utterance_confidence = round(
                sum(w.confidence for w in words) / len(words), 4
            )
        else:
            utterance_confidence = 0.0

        # Detect language(s)
        detected_lang = _map_language(info.language)
        detected_languages = [detected_lang]
        # For code-mixed detection, check if words contain multiple script patterns
        unique_langs = list(set(w.language for w in words)) if words else [detected_lang]
        if len(unique_langs) > 1:
            detected_languages = unique_langs

        result = STTResult(
            transcription=transcription,
            words=words,
            utterance_confidence=utterance_confidence,
            detected_languages=detected_languages,
            dominant_language=detected_lang,
            is_code_mixed=len(detected_languages) > 1,
            processing_time_ms=round(elapsed_ms, 1),
        )

        logger.info(
            "STT: lang=%s confidence=%.2f words=%d time=%.0fms text='%s'",
            detected_lang.value,
            utterance_confidence,
            len(words),
            elapsed_ms,
            transcription[:80],
        )

        return result

    def is_available(self) -> bool:
        """Check if Whisper can be loaded (GPU available, model downloadable)."""
        try:
            self._load_model()
            return True
        except Exception as e:
            logger.error("Whisper not available: %s", e)
            return False


# ──────────────────────────────────────────────
# Vosk implementation (fallback — lightweight, CPU-only)
# ──────────────────────────────────────────────

class VoskSTTEngine(STTEngineBase):
    """
    Vosk STT fallback — lightweight, CPU-friendly.
    Used when GPU is unavailable or Whisper fails.
    """

    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._model = None
        self._model_loaded = False

    def _load_model(self):
        if self._model_loaded:
            return
        try:
            from vosk import Model
            model_path = self._settings.stt.vosk_model_path
            logger.info("Loading Vosk model from %s", model_path)
            self._model = Model(model_path)
            self._model_loaded = True
            logger.info("Vosk model loaded")
        except Exception as e:
            logger.error("Failed to load Vosk model: %s", e)
            raise

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> STTResult:
        """Transcribe using Vosk (CPU-based fallback)."""
        self._load_model()

        import json
        from vosk import KaldiRecognizer

        start = time.perf_counter()

        rec = KaldiRecognizer(self._model, sample_rate)
        rec.SetWords(True)

        # Convert float32 audio to int16 bytes for Vosk
        audio_int16 = (audio_data * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()

        rec.AcceptWaveform(audio_bytes)
        result_json = json.loads(rec.FinalResult())

        elapsed_ms = (time.perf_counter() - start) * 1000

        transcription = result_json.get("text", "")
        words = []
        if "result" in result_json:
            for w in result_json["result"]:
                words.append(WordResult(
                    word=w.get("word", ""),
                    confidence=round(w.get("conf", 0.0), 4),
                    language=SupportedLanguage.HINDI,  # Vosk model-dependent
                    start_time=round(w.get("start", 0.0), 3),
                    end_time=round(w.get("end", 0.0), 3),
                ))

        utterance_confidence = 0.0
        if words:
            utterance_confidence = round(
                sum(w.confidence for w in words) / len(words), 4
            )

        return STTResult(
            transcription=transcription,
            words=words,
            utterance_confidence=utterance_confidence,
            detected_languages=[SupportedLanguage.HINDI],
            dominant_language=SupportedLanguage.HINDI,
            is_code_mixed=False,
            processing_time_ms=round(elapsed_ms, 1),
        )

    def is_available(self) -> bool:
        try:
            self._load_model()
            return True
        except Exception:
            return False
