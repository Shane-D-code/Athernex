"""
End-to-End Voice Pipeline.

Orchestrates the complete flow:
Audio Input -> VAD -> STT -> Language Detection -> LLM -> 
Confidence Analysis -> Dialogue Management -> Order Management -> 
TTS -> Audio Output

Task 16: End-to-End Pipeline implementation.
"""

import logging
import asyncio
import uuid
from typing import AsyncIterator, Optional, Dict, Any, Callable
from dataclasses import dataclass

from audio.vad import VoiceActivityDetector
from audio.processing import AudioProcessor
from audio.buffer import AudioBufferManager
from stt.base import TranscriptionResult
from llm.base import LLMResponse
from tts.base import SynthesisResult
from language.detector import LanguageDetector, DominantLanguageResult
from confidence.estimator import ConfidenceEstimationModule
from confidence.analyzer import ConfidenceAnalyzer, ClarificationRecommendation
from dialogue.manager import DialogueManager, DialogueContext, DialogueState
from orchestration.order_manager import OrderManager, OrderStatus
from orchestration.cache import CacheManager
from orchestration.orchestrator import ServiceOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of a complete pipeline execution."""
    session_id: str
    success: bool
    user_text: Optional[str] = None
    bot_text: Optional[str] = None
    audio_bytes: Optional[bytes] = None
    audio_format: str = "mp3"
    language: str = "en"
    intent: Optional[str] = None
    confidence: float = 0.0
    order_id: Optional[str] = None
    clarification_needed: bool = False
    processing_time_ms: float = 0.0
    error: Optional[str] = None


class VoicePipeline:
    """
    End-to-end voice order pipeline.
    
    Processes audio input through the complete chain and produces
    audio output with optional text metadata.
    """

    def __init__(
        self,
        orchestrator: ServiceOrchestrator,
        dialogue_manager: DialogueManager,
        order_manager: OrderManager,
        cache_manager: Optional[CacheManager] = None,
        enable_vad: bool = True,
        enable_audio_processing: bool = True,
    ):
        self.orchestrator = orchestrator
        self.dialogue = dialogue_manager
        self.orders = order_manager
        self.cache = cache_manager or CacheManager()
        
        # Sub-components
        self.vad = VoiceActivityDetector() if enable_vad else None
        self.audio_processor = AudioProcessor() if enable_audio_processing else None
        self.language_detector = LanguageDetector()
        self.confidence_estimator = ConfidenceEstimationModule()
        self.confidence_analyzer = ConfidenceAnalyzer()
        
        # Callbacks
        self.on_turn_complete: Optional[Callable[[PipelineResult], None]] = None
        
        logger.info("VoicePipeline initialized")

    async def process_text(
        self,
        text: str,
        session_id: Optional[str] = None,
        language: Optional[str] = None,
    ) -> PipelineResult:
        """
        Process text input through the pipeline (text-only mode).
        
        Useful for testing and text-based interfaces.
        """
        start_time = asyncio.get_event_loop().time()
        session_id = session_id or str(uuid.uuid4())[:8]
        
        try:
            # Get or create session
            context = self.dialogue.get_or_create_session(session_id, language or "en")
            
            # Anaphora resolution
            resolved_text = self.dialogue.resolve_anaphora(context, text)
            
            # Check LLM cache
            llm_cache_key = self.cache.get_llm_cache_key(resolved_text, "default")
            llm_result = self.cache.get_cached_llm_response(llm_cache_key)
            
            if llm_result is None:
                llm_result = await self.orchestrator.process_utterance(
                    resolved_text, context=context.to_llm_context()
                )
                self.cache.cache_llm_response(llm_cache_key, llm_result)
            
            # Confidence analysis
            stt_confidence = 0.95  # Assume high confidence for text input
            recommendation = self.confidence_analyzer.analyze(
                stt_confidence, llm_result.structured_data, []
            )
            
            # Update dialogue state
            new_state = self._determine_state(llm_result, recommendation)
            context = self.dialogue.update_session(
                session_id=session_id,
                user_utterance=text,
                bot_response="",  # Will be set after TTS
                structured_data=llm_result.structured_data,
                new_state=new_state,
            )
            
            # Process business logic
            order_result = await self._process_business_logic(
                context, llm_result, recommendation
            )
            
            # Generate response text
            response_text = await self._generate_response(
                context, llm_result, recommendation, order_result
            )
            
            # Synthesize TTS
            tts_result = await self._synthesize_response(response_text, context.language)
            
            # Update session with final bot response
            context.last_bot_response = response_text
            
            # Calculate processing time
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            result = PipelineResult(
                session_id=session_id,
                success=True,
                user_text=text,
                bot_text=response_text,
                audio_bytes=tts_result.audio_bytes if tts_result else None,
                audio_format=tts_result.format if tts_result else "mp3",
                language=context.language,
                intent=llm_result.structured_data.intent.value,
                confidence=recommendation.should_clarify,
                order_id=order_result.get("order_id") if order_result else None,
                clarification_needed=recommendation.should_clarify,
                processing_time_ms=processing_time,
            )
            
            if self.on_turn_complete:
                self.on_turn_complete(result)
            
            return result
            
        except Exception as e:
            logger.error("Pipeline error: %s", e, exc_info=True)
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return PipelineResult(
                session_id=session_id,
                success=False,
                user_text=text,
                error=str(e),
                processing_time_ms=processing_time,
            )

    async def process_audio(
        self,
        audio_bytes: bytes,
        session_id: Optional[str] = None,
        sample_rate: int = 16000,
    ) -> PipelineResult:
        """
        Process audio input through the complete pipeline.
        
        Flow: Audio -> Processing -> STT -> LLM -> Business Logic -> TTS
        """
        start_time = asyncio.get_event_loop().time()
        session_id = session_id or str(uuid.uuid4())[:8]
        
        try:
            # Step 1: Audio processing
            if self.audio_processor:
                audio_bytes = self.audio_processor.process(audio_bytes)
            
            # Step 2: STT
            stt_result = await self.orchestrator.transcribe(audio_bytes, sample_rate)
            user_text = stt_result.text
            
            if not user_text:
                return PipelineResult(
                    session_id=session_id,
                    success=False,
                    error="No speech detected",
                    processing_time_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
                )
            
            # Step 3: Language detection
            lang_result = self.language_detector.detect(stt_result)
            detected_language = lang_result.dominant_language
            
            # Step 4: Confidence estimation from STT
            confidence_meta = self.confidence_estimator.analyze(stt_result)
            
            # Get or create session with detected language
            context = self.dialogue.get_or_create_session(session_id, detected_language)
            
            # Anaphora resolution
            resolved_text = self.dialogue.resolve_anaphora(context, user_text)
            
            # Step 5: LLM processing
            llm_cache_key = self.cache.get_llm_cache_key(resolved_text, "default")
            llm_result = self.cache.get_cached_llm_response(llm_cache_key)
            
            if llm_result is None:
                llm_result = await self.orchestrator.process_utterance(
                    resolved_text, context=context.to_llm_context()
                )
                self.cache.cache_llm_response(llm_cache_key, llm_result)
            
            # Step 6: Confidence analysis
            recommendation = self.confidence_analyzer.analyze(
                confidence_meta.utterance_confidence,
                llm_result.structured_data,
                confidence_meta.low_confidence_words,
            )
            
            # Step 7: Update dialogue state
            new_state = self._determine_state(llm_result, recommendation)
            context = self.dialogue.update_session(
                session_id=session_id,
                user_utterance=user_text,
                bot_response="",
                structured_data=llm_result.structured_data,
                new_state=new_state,
            )
            
            # Step 8: Business logic
            order_result = await self._process_business_logic(
                context, llm_result, recommendation
            )
            
            # Step 9: Generate response
            response_text = await self._generate_response(
                context, llm_result, recommendation, order_result
            )
            
            # Step 10: TTS synthesis
            tts_result = await self._synthesize_response(response_text, context.language)
            
            # Finalize session
            context.last_bot_response = response_text
            
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            result = PipelineResult(
                session_id=session_id,
                success=True,
                user_text=user_text,
                bot_text=response_text,
                audio_bytes=tts_result.audio_bytes if tts_result else None,
                audio_format=tts_result.format if tts_result else "mp3",
                language=context.language,
                intent=llm_result.structured_data.intent.value,
                confidence=confidence_meta.utterance_confidence,
                order_id=order_result.get("order_id") if order_result else None,
                clarification_needed=recommendation.should_clarify,
                processing_time_ms=processing_time,
            )
            
            if self.on_turn_complete:
                self.on_turn_complete(result)
            
            return result
            
        except Exception as e:
            logger.error("Pipeline audio processing error: %s", e, exc_info=True)
            processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return PipelineResult(
                session_id=session_id,
                success=False,
                error=str(e),
                processing_time_ms=processing_time,
            )

    async def process_audio_stream(
        self,
        audio_chunks: AsyncIterator[bytes],
        session_id: Optional[str] = None,
        sample_rate: int = 16000,
    ) -> AsyncIterator[PipelineResult]:
        """
        Process streaming audio input.
        
        Uses VAD to detect speech segments and processes each segment.
        """
        session_id = session_id or str(uuid.uuid4())[:8]
        buffer_manager = AudioBufferManager(sample_rate=sample_rate)
        
        async for chunk in audio_chunks:
            buffer_manager.add_audio(chunk)
            
            # VAD check if enabled
            if self.vad:
                vad_result = self.vad.process_chunk(chunk)
                if vad_result["speech_ended"]:
                    segment_audio = buffer_manager.get_all()
                    if segment_audio:
                        result = await self.process_audio(segment_audio, session_id, sample_rate)
                        yield result
            else:
                # Without VAD, process when buffer reaches threshold
                if buffer_manager.get_duration_ms() >= 5000:  # 5 seconds
                    segment_audio = buffer_manager.get_all()
                    result = await self.process_audio(segment_audio, session_id, sample_rate)
                    yield result
        
        # Process any remaining audio
        remaining = buffer_manager.get_all()
        if remaining:
            result = await self.process_audio(remaining, session_id, sample_rate)
            yield result

    def _determine_state(
        self, llm_result: LLMResponse, recommendation: ClarificationRecommendation
    ) -> DialogueState:
        """Determine dialogue state from LLM result and confidence."""
        from llm.base import Intent
        
        intent = llm_result.structured_data.intent
        
        if recommendation.should_clarify:
            return DialogueState.CLARIFYING
        
        if intent == Intent.CANCEL_ORDER:
            return DialogueState.CANCELLED
        
        if intent == Intent.CONFIRM_ORDER:
            return DialogueState.COMPLETED
        
        if intent == Intent.PLACE_ORDER and not recommendation.should_clarify:
            return DialogueState.CONFIRMING
        
        if intent in (Intent.MODIFY_ORDER, Intent.CHECK_STATUS):
            return DialogueState.PROCESSING
        
        return DialogueState.AWAITING_ORDER

    async def _process_business_logic(
        self,
        context: DialogueContext,
        llm_result: LLMResponse,
        recommendation: ClarificationRecommendation,
    ) -> Optional[Dict[str, Any]]:
        """Process order-related business logic."""
        from llm.base import Intent
        
        data = llm_result.structured_data
        
        if recommendation.should_clarify:
            return None
        
        if data.intent == Intent.PLACE_ORDER:
            # Create new order
            order = self.orders.create_order(
                session_id=context.session_id,
                items=data.items,
                delivery_time=data.delivery_time,
                special_instructions=data.special_instructions,
                language=context.language,
            )
            return {"order_id": order.order_id, "action": "created"}
        
        elif data.intent == Intent.MODIFY_ORDER:
            # Try to modify last order
            order_id = data.order_id
            if not order_id:
                last_order = self.orders.get_last_order_for_session(context.session_id)
                if last_order:
                    order_id = last_order.order_id
            
            if order_id:
                order = self.orders.modify_order(
                    order_id=order_id,
                    add_items=data.items,
                    new_delivery_time=data.delivery_time,
                )
                if order:
                    return {"order_id": order.order_id, "action": "modified"}
            return {"error": "No order found to modify"}
        
        elif data.intent == Intent.CANCEL_ORDER:
            order_id = data.order_id
            if not order_id:
                last_order = self.orders.get_last_order_for_session(context.session_id)
                if last_order:
                    order_id = last_order.order_id
            
            if order_id:
                success = self.orders.cancel_order(order_id)
                return {"order_id": order_id, "action": "cancelled", "success": success}
            return {"error": "No order found to cancel"}
        
        elif data.intent == Intent.CHECK_STATUS:
            order_id = data.order_id
            if not order_id:
                last_order = self.orders.get_last_order_for_session(context.session_id)
                if last_order:
                    order_id = last_order.order_id
            
            if order_id:
                order = self.orders.get_order(order_id)
                if order:
                    return {"order_id": order_id, "status": order.status.value}
            return {"error": "No order found"}
        
        elif data.intent == Intent.CONFIRM_ORDER:
            # Confirm last pending order
            last_order = self.orders.get_last_order_for_session(context.session_id)
            if last_order and last_order.status == OrderStatus.PENDING:
                self.orders.confirm_order(last_order.order_id)
                return {"order_id": last_order.order_id, "action": "confirmed"}
            return {"error": "No pending order to confirm"}
        
        return None

    async def _generate_response(
        self,
        context: DialogueContext,
        llm_result: LLMResponse,
        recommendation: ClarificationRecommendation,
        order_result: Optional[Dict[str, Any]],
    ) -> str:
        """Generate bot response text."""
        from llm.base import Intent
        
        data = llm_result.structured_data
        
        # Clarification response
        if recommendation.should_clarify and recommendation.suggested_question:
            return recommendation.suggested_question
        
        # Order confirmation
        if data.intent == Intent.PLACE_ORDER and order_result:
            order_id = order_result.get("order_id")
            if order_id:
                order = self.orders.get_order(order_id)
                if order:
                    return order.get_confirmation_message()
        
        # Status check
        if data.intent == Intent.CHECK_STATUS and order_result:
            order_id = order_result.get("order_id")
            if order_id:
                order = self.orders.get_order(order_id)
                if order:
                    return order.get_status_message()
        
        # Cancel confirmation
        if data.intent == Intent.CANCEL_ORDER:
            if order_result and order_result.get("success"):
                messages = {
                    "hi": f"ऑर्डर {order_result.get('order_id')} कैंसिल हो गया।",
                    "en": f"Order {order_result.get('order_id')} has been cancelled.",
                }
                return messages.get(context.language, messages["en"])
            return "I couldn't find an order to cancel."
        
        # Modify confirmation
        if data.intent == Intent.MODIFY_ORDER:
            if order_result and "error" not in order_result:
                messages = {
                    "hi": f"ऑर्डर {order_result.get('order_id')} अपडेट हो गया।",
                    "en": f"Order {order_result.get('order_id')} has been updated.",
                }
                return messages.get(context.language, messages["en"])
            return "I couldn't find an order to modify."
        
        # Confirm order
        if data.intent == Intent.CONFIRM_ORDER:
            if order_result and "error" not in order_result:
                messages = {
                    "hi": "ऑर्डर कन्फर्म हो गया।",
                    "en": "Your order has been confirmed.",
                }
                return messages.get(context.language, messages["en"])
            return "No pending order to confirm."
        
        # Default response
        defaults = {
            "hi": "मैं आपकी कैसे मदद कर सकता हूँ?",
            "en": "How can I help you today?",
            "kn": "ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
            "mr": "मी तुम्हाला कशी मदत करू शकतो?",
        }
        return defaults.get(context.language, defaults["en"])

    async def _synthesize_response(self, text: str, language: str) -> Optional[SynthesisResult]:
        """Synthesize response text to speech."""
        if not text:
            return None
        
        # Check TTS cache
        tts_cache_key = self.cache.get_tts_cache_key(text, language)
        cached_audio = self.cache.get_cached_tts_audio(tts_cache_key)
        
        if cached_audio:
            # Return cached result
            return SynthesisResult(
                audio_bytes=cached_audio,
                sample_rate=24000,
                format="mp3",
                duration=0.0,
                text=text,
                language=language,
                voice="cached",
            )
        
        # Synthesize fresh
        try:
            result = await self.orchestrator.synthesize(text, language=language)
            self.cache.cache_tts_audio(tts_cache_key, result.audio_bytes)
            return result
        except Exception as e:
            logger.error("TTS synthesis failed: %s", e)
            return None

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a dialogue session."""
        context = self.dialogue.get_session(session_id)
        if not context:
            return None
        
        orders = self.orders.get_orders_by_session(session_id)
        return {
            "session_id": session_id,
            "state": context.state.value,
            "turn_count": context.turn_count,
            "language": context.language,
            "current_intent": context.current_intent.value if context.current_intent else None,
            "current_items": [
                {"name": i.name, "quantity": i.quantity}
                for i in context.current_items
            ],
            "orders": [o.to_dict() for o in orders],
        }

    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        return {
            "active_sessions": self.dialogue.get_active_session_count(),
            "orders": self.orders.get_order_statistics(),
            "cache": self.cache.get_stats(),
            "services": self.orchestrator.get_stats(),
        }

