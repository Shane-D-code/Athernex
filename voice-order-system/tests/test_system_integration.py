"""
Integration tests for the voice order system.

Tests the complete system without requiring external services.
Works with or without fastText installed.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestLanguageDetection:
    """Test language detection (with fallback)."""
    
    def test_hybrid_detector_import(self):
        """Test that hybrid detector can be imported."""
        from language.hybrid_detector import get_hybrid_detector
        detector = get_hybrid_detector()
        assert detector is not None
    
    def test_detect_hindi_text(self):
        """Test Hindi detection from text."""
        from language.hybrid_detector import get_hybrid_detector
        
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मुझे दो पिज़्ज़ा चाहिए")
        
        assert result.language == "hi"
        assert not result.is_code_mixed
    
    def test_detect_english_text(self):
        """Test English detection from text."""
        from language.hybrid_detector import get_hybrid_detector
        
        detector = get_hybrid_detector()
        result = detector.detect_from_text("I want two pizzas")
        
        assert result.language == "en"
        assert not result.is_code_mixed
    
    def test_detect_hinglish_text(self):
        """Test Hinglish detection from text."""
        from language.hybrid_detector import get_hybrid_detector
        
        detector = get_hybrid_detector()
        result = detector.detect_from_text("मुझे pizza चाहिए")
        
        # Should detect as code-mixed (either hinglish or hi with code_mixed flag)
        assert result.is_code_mixed or result.language == "hinglish"
    
    def test_detect_kannada_text(self):
        """Test Kannada detection from text."""
        from language.hybrid_detector import get_hybrid_detector
        
        detector = get_hybrid_detector()
        result = detector.detect_from_text("ನನಗೆ ಎರಡು ಪಿಜ್ಜಾ ಬೇಕು")
        
        assert result.language == "kn"


class TestDialogueManager:
    """Test dialogue management."""
    
    def test_create_session(self):
        """Test session creation."""
        from dialogue.manager import DialogueManager
        
        manager = DialogueManager()
        session = manager.create_session("test-123", "en")
        
        assert session.session_id == "test-123"
        assert session.language == "en"
        assert session.turn_count == 0
    
    def test_update_session(self):
        """Test session update."""
        from dialogue.manager import DialogueManager
        
        manager = DialogueManager()
        session = manager.create_session("test-123", "en")
        
        manager.update_session(
            session_id="test-123",
            user_utterance="I want pizza",
            bot_response="How many pizzas?"
        )
        
        updated = manager.get_session("test-123")
        assert updated.turn_count == 1
        assert updated.last_user_utterance == "I want pizza"
    
    def test_anaphora_resolution(self):
        """Test anaphora resolution."""
        from dialogue.manager import DialogueManager
        from llm.base import OrderItem
        
        manager = DialogueManager()
        context = manager.create_session("test-123", "en")
        context.current_items = [OrderItem(name="pizza", quantity=2)]
        
        resolved = manager.resolve_anaphora(context, "add one more")
        
        assert "pizza" in resolved.lower()


class TestOrderManager:
    """Test order management."""
    
    def test_create_order(self):
        """Test order creation."""
        from orchestration.order_manager import OrderManager
        from llm.base import OrderItem
        
        manager = OrderManager()
        order = manager.create_order(
            session_id="test-123",
            items=[OrderItem(name="pizza", quantity=2)],
            language="en"
        )
        
        assert order.order_id.startswith("ORD-")
        assert len(order.items) == 1
        assert order.items[0].name == "pizza"
        assert order.total_items == 2
    
    def test_modify_order(self):
        """Test order modification."""
        from orchestration.order_manager import OrderManager
        from llm.base import OrderItem
        
        manager = OrderManager()
        order = manager.create_order(
            session_id="test-123",
            items=[OrderItem(name="pizza", quantity=2)],
            language="en"
        )
        
        modified = manager.modify_order(
            order_id=order.order_id,
            add_items=[OrderItem(name="burger", quantity=1)]
        )
        
        assert modified is not None
        assert len(modified.items) == 2
        assert modified.total_items == 3
    
    def test_cancel_order(self):
        """Test order cancellation."""
        from orchestration.order_manager import OrderManager
        from llm.base import OrderItem
        
        manager = OrderManager()
        order = manager.create_order(
            session_id="test-123",
            items=[OrderItem(name="pizza", quantity=2)],
            language="en"
        )
        
        success = manager.cancel_order(order.order_id)
        
        assert success
        cancelled = manager.get_order(order.order_id)
        assert cancelled.status.value == "cancelled"


class TestCacheManager:
    """Test caching functionality."""
    
    def test_cache_initialization(self):
        """Test cache manager initialization."""
        from orchestration.cache import CacheManager
        
        cache = CacheManager()
        stats = cache.get_stats()
        
        assert "llm_cache" in stats
        assert "tts_cache" in stats
        assert stats["llm_cache"]["size"] == 0
    
    def test_llm_cache(self):
        """Test LLM response caching."""
        from orchestration.cache import CacheManager
        
        cache = CacheManager()
        key = cache.get_llm_cache_key("test text", "model")
        
        # Cache a response
        cache.cache_llm_response(key, {"result": "test"})
        
        # Retrieve it
        cached = cache.get_cached_llm_response(key)
        
        assert cached is not None
        assert cached["result"] == "test"
    
    def test_tts_cache(self):
        """Test TTS audio caching."""
        from orchestration.cache import CacheManager
        
        cache = CacheManager()
        key = cache.get_tts_cache_key("test text", "en")
        
        # Cache audio
        audio_data = b"fake audio data"
        cache.cache_tts_audio(key, audio_data)
        
        # Retrieve it
        cached = cache.get_cached_tts_audio(key)
        
        assert cached == audio_data


class TestOrchestrator:
    """Test service orchestration."""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator can be initialized."""
        from orchestration.orchestrator import ServiceOrchestrator
        
        # Initialize with empty lists (no actual services)
        orchestrator = ServiceOrchestrator(
            stt_engines=[],
            llm_processors=[],
            tts_engines=[]
        )
        
        assert orchestrator is not None
        stats = orchestrator.get_stats()
        assert "stt" in stats
        assert "llm" in stats
        assert "tts" in stats


class TestPipeline:
    """Test voice pipeline (without external services)."""
    
    def test_pipeline_initialization(self):
        """Test pipeline can be initialized."""
        from orchestration.pipeline import VoicePipeline
        from orchestration.orchestrator import ServiceOrchestrator
        from dialogue.manager import DialogueManager
        from orchestration.order_manager import OrderManager
        from orchestration.cache import CacheManager
        
        orchestrator = ServiceOrchestrator(
            stt_engines=[],
            llm_processors=[],
            tts_engines=[]
        )
        dialogue = DialogueManager()
        orders = OrderManager()
        cache = CacheManager()
        
        pipeline = VoicePipeline(
            orchestrator=orchestrator,
            dialogue_manager=dialogue,
            order_manager=orders,
            cache_manager=cache,
            enable_vad=False,
            enable_audio_processing=False
        )
        
        assert pipeline is not None
        stats = pipeline.get_system_stats()
        assert "active_sessions" in stats
        assert "orders" in stats


class TestAPIStructure:
    """Test API structure (without starting server)."""
    
    def test_api_import(self):
        """Test that API module can be imported."""
        from api.main import app
        
        assert app is not None
        assert app.title == "Multilingual Voice Order System"
    
    def test_api_routes(self):
        """Test that API routes are defined."""
        from api.main import app
        
        routes = [route.path for route in app.routes]
        
        assert "/health" in routes
        assert "/process/text" in routes
        assert "/process/audio" in routes
        assert "/orders" in routes


class TestDataModels:
    """Test data models and structures."""
    
    def test_order_item_model(self):
        """Test OrderItem model."""
        from llm.base import OrderItem
        
        item = OrderItem(name="pizza", quantity=2, unit="pieces")
        
        assert item.name == "pizza"
        assert item.quantity == 2
        assert item.unit == "pieces"
    
    def test_intent_enum(self):
        """Test Intent enum."""
        from llm.base import Intent
        
        assert Intent.PLACE_ORDER.value == "place_order"
        assert Intent.CANCEL_ORDER.value == "cancel_order"
        assert Intent.MODIFY_ORDER.value == "modify_order"
    
    def test_structured_order_data(self):
        """Test StructuredOrderData model."""
        from llm.base import StructuredOrderData, Intent, OrderItem
        
        data = StructuredOrderData(
            intent=Intent.PLACE_ORDER,
            items=[OrderItem(name="pizza", quantity=2)],
            confidence=0.95
        )
        
        assert data.intent == Intent.PLACE_ORDER
        assert len(data.items) == 1
        assert data.confidence == 0.95


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
