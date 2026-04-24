"""
Shared dependency injection for FastAPI routes.
The pipeline is initialised once at startup and reused across all requests.
"""

import logging
import os
from typing import Optional

from stt.whisper_engine import WhisperSTTEngine
from stt.vosk_engine import VoskSTTEngine
from llm.ollama_processor import OllamaLLMProcessor
from tts.edge_engine import EdgeTTSEngine
from pipeline.voice_pipeline import VoicePipeline
from confidence.analyzer import ConfidenceAnalyzer
from language.trained_detector import TrainedLanguageDetector
from orchestration.order_manager import OrderManager
from dialogue.tracker import DialogueStateTracker

logger = logging.getLogger(__name__)

_pipeline: Optional[VoicePipeline] = None


async def startup_pipeline():
    """Initialise the pipeline at application startup."""
    global _pipeline

    logger.info("Initialising voice pipeline components...")

    # STT: Try Whisper, fallback to Vosk
    try:
        stt = WhisperSTTEngine(
            base_url=os.getenv("WHISPER_BASE_URL", "http://localhost:8000"),
            model=os.getenv("WHISPER_MODEL", "medium"),
        )
        logger.info("STT: Whisper ready")
    except Exception as e:
        logger.warning(f"Whisper not available: {e}, using Vosk")
        stt = VoskSTTEngine(language="hi")

    # LLM: Ollama
    try:
        llm = OllamaLLMProcessor(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M"),
        )
        logger.info("LLM: Ollama ready")
    except Exception as e:
        logger.error(f"Ollama not available: {e}")
        raise

    # TTS: Edge TTS
    tts = EdgeTTSEngine()
    logger.info("TTS: EdgeTTS ready")

    # Additional components
    confidence_analyzer = ConfidenceAnalyzer()
    language_detector = TrainedLanguageDetector()
    order_manager = OrderManager()
    dialogue_tracker = DialogueStateTracker()

    _pipeline = VoicePipeline(
        stt_engine=stt,
        llm_processor=llm,
        tts_engine=tts,
        confidence_analyzer=confidence_analyzer,
        language_detector=language_detector,
        order_manager=order_manager,
        dialogue_tracker=dialogue_tracker,
    )
    logger.info("Voice pipeline initialised successfully")


async def shutdown_pipeline():
    global _pipeline
    _pipeline = None
    logger.info("Pipeline shut down")


def get_pipeline() -> VoicePipeline:
    if _pipeline is None:
        raise RuntimeError("Pipeline not initialised")
    return _pipeline
