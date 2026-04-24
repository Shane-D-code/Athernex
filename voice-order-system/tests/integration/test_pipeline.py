"""
Integration tests for the end-to-end voice processing pipeline.

Tests the complete flow using mock STT, LLM, and TTS engines so no
external services are required.
"""

import asyncio
import sys
from pathlib import Path
from typing import AsyncIterator, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from stt.base import STTEngine, TranscriptionResult, StreamingChunk, WordResult
from llm.base import LLMProcessor, LLMResponse, StructuredOrderData, Intent, OrderItem
from tts.base import TTSEngine, SynthesisResult, AudioChunk
from pipeline.voice_pipeline import VoicePipeline, PipelineResult
from pipeline.clarification import ClarificationManager
from orchestration.service_orchestrator import ServiceOrchestrator


# ---------------------------------------------------------------------------
# Mock engines
# ---------------------------------------------------------------------------

class MockSTTEngine(STTEngine):
    """STT engine that returns a preset transcription."""

    def __init__(self, text: str = "I want 2 pizzas", confidence: float = 0.9, language: str = "en"):
        self._text = text
        self._confidence = confidence
        self._language = language

    @property
    def name(self) -> str:
        return "MockSTT"

    async def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> TranscriptionResult:
        words = [
            WordResult(word=w, start=i * 0.3, end=(i + 1) * 0.3, confidence=self._confidence, language=self._language)
            for i, w in enumerate(self._text.split())
        ]
        return TranscriptionResult(
            text=self._text,
            language=self._language,
            language_probability=0.95,
            words=words,
            duration=len(words) * 0.3,
            confidence=self._confidence,
        )

    async def transcribe_stream(self, audio_chunks: AsyncIterator[bytes], sample_rate: int = 16000) -> AsyncIterator[StreamingChunk]:
        async def _gen():
            yield StreamingChunk(text=self._text, is_final=True, confidence=self._confidence)
        return _gen()

    async def health_check(self) -> bool:
        return True


class MockLLMProcessor(LLMProcessor):
    """LLM processor that returns a preset structured response."""

    def __init__(
        self,
        intent: Intent = Intent.PLACE_ORDER,
        items: Optional[List[OrderItem]] = None,
        confidence: float = 0.9,
        missing_fields: Optional[List[str]] = None,
    ):
        self._intent = intent
        self._items = items or [OrderItem(name="Pizza", quantity=2)]
        self._confidence = confidence
        self._missing_fields = missing_fields or []

    @property
    def name(self) -> str:
        return "MockLLM"

    async def process_utterance(self, text: str, context=None) -> LLMResponse:
        data = StructuredOrderData(
            intent=self._intent,
            items=self._items,
            confidence=self._confidence,
            missing_fields=self._missing_fields,
        )
        return LLMResponse(
            structured_data=data,
            raw_response="{}",
            processing_time=0.1,
            model_used="mock",
            confidence=self._confidence,
        )

    async def health_check(self) -> bool:
        return True

    async def add_intent(self, intent: str, examples: List[str]) -> bool:
        return True


class MockTTSEngine(TTSEngine):
    """TTS engine that returns silent audio bytes."""

    @property
    def name(self) -> str:
        return "MockTTS"

    async def synthesize(self, text: str, language: str = "en", voice=None) -> SynthesisResult:
        audio = b"\x00" * 1000  # silent audio
        return SynthesisResult(
            audio_bytes=audio,
            sample_rate=22050,
            format="pcm_16",
            duration=len(audio) / (22050 * 2),
            text=text,
            language=language,
            voice=voice or "default",
        )

    async def synthesize_stream(self, text: str, language: str = "en", voice=None) -> AsyncIterator[AudioChunk]:
        async def _gen():
            yield AudioChunk(audio_bytes=b"\x00" * 500, sample_rate=22050, format="pcm_16")
            yield AudioChunk(audio_bytes=b"", sample_rate=22050, format="pcm_16", is_final=True)
        return _gen()

    async def health_check(self) -> bool:
        return True

    def get_available_voices(self, language=None) -> List[str]:
        return ["default"]


class FailingSTTEngine(MockSTTEngine):
    async def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> TranscriptionResult:
        raise ConnectionError("STT service unavailable")

    async def health_check(self) -> bool:
        return False


class FailingLLMProcessor(MockLLMProcessor):
    async def process_utterance(self, text: str, context=None) -> LLMResponse:
        raise ConnectionError("LLM service unavailable")

    async def health_check(self) -> bool:
        return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DUMMY_AUDIO = b"\x00" * 3200  # 100ms of silence at 16kHz PCM_16


def make_pipeline(**kwargs) -> VoicePipeline:
    defaults = dict(
        stt_engine=MockSTTEngine(),
        llm_processor=MockLLMProcessor(),
        tts_engine=MockTTSEngine(),
    )
    defaults.update(kwargs)
    return VoicePipeline(**defaults)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEndToEndPipeline:

    @pytest.mark.asyncio
    async def test_complete_place_order_flow(self):
        """Test complete flow from audio input to audio output for place_order."""
        pipeline = make_pipeline()
        result = await pipeline.process_audio(DUMMY_AUDIO, session_id="test-session-1")

        assert result.error is None
        assert result.transcription == "I want 2 pizzas"
        assert result.structured_data is not None
        assert result.structured_data.intent == Intent.PLACE_ORDER
        assert result.audio_response is not None
        assert len(result.audio_response) > 0
        assert result.order_result is not None
        assert result.order_result["status"] == "success"

    @pytest.mark.asyncio
    async def test_clarification_triggered_on_low_confidence(self):
        """Test that clarification is triggered when confidence is below threshold."""
        pipeline = make_pipeline(
            stt_engine=MockSTTEngine(confidence=0.3),
            llm_processor=MockLLMProcessor(confidence=0.3, missing_fields=["items"]),
        )
        result = await pipeline.process_audio(DUMMY_AUDIO, session_id="test-session-2")

        assert result.error is None
        assert result.clarification_needed is True
        assert result.clarification_question is not None
        assert result.order_result is None

    @pytest.mark.asyncio
    async def test_error_handling_stt_failure(self):
        """Test that STT failure produces a graceful error response."""
        pipeline = make_pipeline(stt_engine=FailingSTTEngine())
        result = await pipeline.process_audio(DUMMY_AUDIO, session_id="test-session-3")

        assert result.error is not None
        assert result.response_text is not None
        assert "error" in result.response_text.lower() or "sorry" in result.response_text.lower()

    @pytest.mark.asyncio
    async def test_latency_breakdown_populated(self):
        """Test that latency breakdown is populated for all components."""
        pipeline = make_pipeline()
        result = await pipeline.process_audio(DUMMY_AUDIO, session_id="test-session-4")

        assert result.latency.stt_ms >= 0
        assert result.latency.llm_ms >= 0
        assert result.latency.tts_ms >= 0
        assert result.latency.total_ms >= 0

    @pytest.mark.asyncio
    async def test_session_context_maintained_across_turns(self):
        """Test that conversation context is maintained across multiple turns."""
        pipeline = make_pipeline()
        session_id = "test-session-5"

        # First turn
        result1 = await pipeline.process_audio(DUMMY_AUDIO, session_id=session_id)
        assert result1.error is None

        # Second turn — session should still exist
        result2 = await pipeline.process_audio(DUMMY_AUDIO, session_id=session_id)
        assert result2.error is None

        # Verify session has 2 turns
        state = pipeline.dialogue_tracker.get_session(session_id)
        assert state is not None
        assert state.turn_count == 2

    @pytest.mark.asyncio
    async def test_clarification_flow_merges_data(self):
        """Test that clarification response is merged with original order data."""
        pipeline = make_pipeline(
            llm_processor=MockLLMProcessor(
                items=[OrderItem(name="Burger", quantity=1)],
                confidence=0.9,
            )
        )
        session_id = "test-session-6"

        # Create session first
        pipeline.dialogue_tracker.create_session(session_id)

        original_data = StructuredOrderData(
            intent=Intent.PLACE_ORDER,
            items=[],
            confidence=0.4,
            missing_fields=["items"],
        )

        result = await pipeline.process_clarification(
            DUMMY_AUDIO, session_id, original_data
        )

        assert result.error is None
        assert result.structured_data is not None


class TestServiceOrchestratorFallback:

    @pytest.mark.asyncio
    async def test_fallback_triggered_after_threshold_errors(self):
        """Test that fallback is used after primary service fails repeatedly."""
        orchestrator = ServiceOrchestrator()
        call_log = []

        async def primary():
            call_log.append("primary")
            raise ConnectionError("primary down")

        async def fallback():
            call_log.append("fallback")
            return "fallback_result"

        # First 2 calls: primary fails, fallback used
        for _ in range(2):
            result = await orchestrator.execute_with_fallback("stt", primary, fallback)
            assert result == "fallback_result"

        # After threshold (3 errors), should switch to fallback-only
        result = await orchestrator.execute_with_fallback("stt", primary, fallback)
        assert result == "fallback_result"
        assert "fallback" in call_log

    @pytest.mark.asyncio
    async def test_successful_primary_resets_error_count(self):
        """Test that a successful primary call resets the error counter."""
        orchestrator = ServiceOrchestrator()
        call_count = {"n": 0}

        async def primary():
            call_count["n"] += 1
            return "ok"

        result = await orchestrator.execute_with_fallback("llm", primary)
        assert result == "ok"

        status = orchestrator.get_service_status("llm")
        assert status["error_count"] == 0
        assert not status["using_fallback"]


class TestClarificationManager:

    def test_start_clarification_returns_question(self):
        from confidence.analyzer import ClarificationRecommendation
        mgr = ClarificationManager()
        data = StructuredOrderData(
            intent=Intent.PLACE_ORDER,
            missing_fields=["items"],
            confidence=0.3,
        )
        rec = ClarificationRecommendation(
            should_clarify=True,
            reason="missing items",
            missing_fields=["items"],
            low_confidence_items=[],
        )
        question = mgr.start_clarification("sess-1", data, rec)
        assert isinstance(question, str)
        assert len(question) > 0

    def test_apply_clarification_resolves_when_confident(self):
        from confidence.analyzer import ClarificationRecommendation
        mgr = ClarificationManager()
        original = StructuredOrderData(
            intent=Intent.PLACE_ORDER,
            missing_fields=["items"],
            confidence=0.3,
        )
        rec_start = ClarificationRecommendation(
            should_clarify=True, reason="missing", missing_fields=["items"], low_confidence_items=[]
        )
        mgr.start_clarification("sess-2", original, rec_start)

        clarification = StructuredOrderData(
            intent=Intent.PLACE_ORDER,
            items=[OrderItem(name="Pizza", quantity=2)],
            confidence=0.95,
            missing_fields=[],
        )
        rec_ok = ClarificationRecommendation(
            should_clarify=False, reason="ok", missing_fields=[], low_confidence_items=[]
        )
        resolved, follow_up, merged = mgr.apply_clarification("sess-2", clarification, rec_ok)

        assert resolved is True
        assert follow_up is None
        assert merged is not None
        assert len(merged.items) == 1
        assert merged.items[0].name == "Pizza"
