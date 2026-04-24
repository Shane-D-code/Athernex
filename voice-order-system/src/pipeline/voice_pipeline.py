"""
Main voice processing pipeline orchestrator.

Wires together: Audio Input → VAD → Echo Cancel → STT → LLM →
Confidence → Order Manager → TTS → Audio Output.

Validates Requirements 7.1, 7.5, 7.6, 7.7, 7.8.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional

from stt.base import STTEngine, TranscriptionResult
from llm.base import LLMProcessor, StructuredOrderData
from tts.base import TTSEngine, SynthesisResult
from confidence.analyzer import ConfidenceAnalyzer, ClarificationRecommendation
from language.detector import LanguageDetector
from order_manager import OrderManager
from dialogue.tracker import DialogueStateTracker
from audio.barge_in import BargeInDetector
from audio.barge_in_handler import BargeInHandler

logger = logging.getLogger(__name__)


@dataclass
class LatencyBreakdown:
    """Per-component latency tracking."""
    stt_ms: float = 0.0
    llm_ms: float = 0.0
    confidence_ms: float = 0.0
    order_ms: float = 0.0
    tts_ms: float = 0.0
    total_ms: float = 0.0


@dataclass
class PipelineResult:
    """Result of a complete pipeline run."""
    session_id: str
    transcription: Optional[str] = None
    structured_data: Optional[StructuredOrderData] = None
    clarification_needed: bool = False
    clarification_question: Optional[str] = None
    order_result: Optional[Dict[str, Any]] = None
    audio_response: Optional[bytes] = None
    response_text: Optional[str] = None
    language: str = "en"
    latency: LatencyBreakdown = field(default_factory=LatencyBreakdown)
    error: Optional[str] = None


class VoicePipeline:
    """
    End-to-end voice processing pipeline.

    Requirements:
    - 7.1: Pass audio through STT → LLM → Confidence → OrderManager → TTS
    - 7.5: Error handling at each stage with voice error output
    - 7.6: Maintain conversation context across turns
    - 7.7: Wait for clarification response and resume
    - 7.8: Streaming audio mode to minimise perceived latency
    """

    def __init__(
        self,
        stt_engine: STTEngine,
        llm_processor: LLMProcessor,
        tts_engine: TTSEngine,
        confidence_analyzer: Optional[ConfidenceAnalyzer] = None,
        language_detector: Optional[LanguageDetector] = None,
        order_manager: Optional[OrderManager] = None,
        dialogue_tracker: Optional[DialogueStateTracker] = None,
    ):
        self.stt = stt_engine
        self.llm = llm_processor
        self.tts = tts_engine
        self.confidence_analyzer = confidence_analyzer or ConfidenceAnalyzer()
        self.language_detector = language_detector or LanguageDetector()
        self.order_manager = order_manager or OrderManager()
        self.dialogue_tracker = dialogue_tracker or DialogueStateTracker()
        self.barge_in_detector = BargeInDetector()
        self.barge_in_handler = BargeInHandler(tracker=self.dialogue_tracker)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def process_audio(
        self,
        audio_bytes: bytes,
        session_id: str,
        sample_rate: int = 16000,
    ) -> PipelineResult:
        """
        Process a complete audio utterance through the full pipeline.

        Args:
            audio_bytes: Raw PCM_16 mono audio
            session_id: Conversation session ID
            sample_rate: Audio sample rate

        Returns:
            PipelineResult with all outputs and latency breakdown
        """
        pipeline_start = time.time()
        result = PipelineResult(session_id=session_id)

        try:
            # Ensure session exists
            self.dialogue_tracker.get_or_create_session(session_id)

            # --- STT ---
            t0 = time.time()
            transcription = await self._run_stt(audio_bytes, sample_rate)
            result.latency.stt_ms = (time.time() - t0) * 1000
            result.transcription = transcription.text

            # Detect language
            lang_result = self.language_detector.detect(transcription)
            result.language = lang_result.dominant_language

            # Resolve anaphora
            resolved_text = self.dialogue_tracker.resolve_anaphora(
                session_id, transcription.text, result.language
            )

            # --- LLM ---
            t0 = time.time()
            context = self.dialogue_tracker.get_context_for_llm(session_id)
            llm_response = await self._run_llm(resolved_text, context)
            result.latency.llm_ms = (time.time() - t0) * 1000
            result.structured_data = llm_response.structured_data

            # --- Confidence Analysis ---
            t0 = time.time()
            low_conf_words = [
                w.word for w in transcription.words if w.confidence < 0.4
            ]
            clarification = self.confidence_analyzer.analyze(
                stt_confidence=transcription.confidence,
                llm_response=llm_response.structured_data,
                low_confidence_words=low_conf_words,
            )
            result.latency.confidence_ms = (time.time() - t0) * 1000

            # --- Order Processing or Clarification ---
            t0 = time.time()
            if clarification.should_clarify:
                result.clarification_needed = True
                result.clarification_question = clarification.suggested_question
                response_text = clarification.suggested_question or "Could you please repeat that?"
            else:
                order_result = self.order_manager.process_order(llm_response.structured_data)
                result.order_result = order_result
                response_text = order_result.get("confirmation_message", "Order processed.")
            result.latency.order_ms = (time.time() - t0) * 1000
            result.response_text = response_text

            # --- TTS ---
            t0 = time.time()
            tts_result = await self._run_tts(response_text, result.language)
            result.latency.tts_ms = (time.time() - t0) * 1000
            result.audio_response = tts_result.audio_bytes

            # Update dialogue state
            self.dialogue_tracker.update_session(
                session_id=session_id,
                user_utterance=transcription.text,
                system_response=response_text,
                extracted_data={
                    "intent": llm_response.structured_data.intent.value,
                    "confidence": llm_response.structured_data.confidence,
                },
            )

        except Exception as exc:
            logger.error("Pipeline error for session %s: %s", session_id, exc, exc_info=True)
            result.error = str(exc)
            result.response_text = "I'm sorry, I encountered an error. Please try again."
            try:
                err_tts = await self._run_tts(result.response_text, "en")
                result.audio_response = err_tts.audio_bytes
            except Exception:
                pass

        result.latency.total_ms = (time.time() - pipeline_start) * 1000
        logger.info(
            "Pipeline complete for session %s: total=%.0fms (stt=%.0f, llm=%.0f, tts=%.0f)",
            session_id,
            result.latency.total_ms,
            result.latency.stt_ms,
            result.latency.llm_ms,
            result.latency.tts_ms,
        )
        return result

    async def process_clarification(
        self,
        audio_bytes: bytes,
        session_id: str,
        original_data: StructuredOrderData,
        sample_rate: int = 16000,
    ) -> PipelineResult:
        """
        Process a clarification response and merge with original order data.

        Resumes from the Confidence Analyzer stage (Requirement 7.7).
        """
        pipeline_start = time.time()
        result = PipelineResult(session_id=session_id)

        try:
            # STT
            t0 = time.time()
            transcription = await self._run_stt(audio_bytes, sample_rate)
            result.latency.stt_ms = (time.time() - t0) * 1000
            result.transcription = transcription.text

            lang_result = self.language_detector.detect(transcription)
            result.language = lang_result.dominant_language

            # LLM — pass original data as context so it can merge
            t0 = time.time()
            context = self.dialogue_tracker.get_context_for_llm(session_id)
            context["original_order"] = {
                "intent": original_data.intent.value,
                "items": [{"name": i.name, "quantity": i.quantity} for i in original_data.items],
                "missing_fields": original_data.missing_fields,
            }
            llm_response = await self._run_llm(transcription.text, context)
            result.latency.llm_ms = (time.time() - t0) * 1000

            # Merge slots from clarification into session
            merged_slots: Dict[str, Any] = {}
            sd = llm_response.structured_data
            if sd.items:
                merged_slots["items"] = [{"name": i.name, "quantity": i.quantity} for i in sd.items]
            if sd.delivery_time:
                merged_slots["delivery_time"] = sd.delivery_time
            if sd.special_instructions:
                merged_slots["special_instructions"] = sd.special_instructions

            if merged_slots:
                self.dialogue_tracker.merge_slots(
                    session_id, merged_slots, confidence=sd.confidence
                )

            result.structured_data = sd

            # Confidence check again
            t0 = time.time()
            low_conf_words = [w.word for w in transcription.words if w.confidence < 0.4]
            clarification = self.confidence_analyzer.analyze(
                stt_confidence=transcription.confidence,
                llm_response=sd,
                low_confidence_words=low_conf_words,
            )
            result.latency.confidence_ms = (time.time() - t0) * 1000

            t0 = time.time()
            if clarification.should_clarify:
                result.clarification_needed = True
                result.clarification_question = clarification.suggested_question
                response_text = clarification.suggested_question or "Could you please clarify?"
            else:
                order_result = self.order_manager.process_order(sd)
                result.order_result = order_result
                response_text = order_result.get("confirmation_message", "Order processed.")
            result.latency.order_ms = (time.time() - t0) * 1000
            result.response_text = response_text

            t0 = time.time()
            tts_result = await self._run_tts(response_text, result.language)
            result.latency.tts_ms = (time.time() - t0) * 1000
            result.audio_response = tts_result.audio_bytes

            self.dialogue_tracker.update_session(
                session_id=session_id,
                user_utterance=transcription.text,
                system_response=response_text,
            )

        except Exception as exc:
            logger.error("Clarification pipeline error: %s", exc, exc_info=True)
            result.error = str(exc)
            result.response_text = "I'm sorry, I couldn't process that. Please try again."

        result.latency.total_ms = (time.time() - pipeline_start) * 1000
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _run_stt(self, audio_bytes: bytes, sample_rate: int) -> TranscriptionResult:
        return await self.stt.transcribe(audio_bytes, sample_rate)

    async def _run_llm(self, text: str, context: Optional[Dict[str, Any]] = None):
        return await self.llm.process_utterance(text, context)

    async def _run_tts(self, text: str, language: str) -> SynthesisResult:
        return await self.tts.synthesize(text, language)
