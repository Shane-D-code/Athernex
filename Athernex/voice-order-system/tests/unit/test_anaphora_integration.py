"""
Integration tests for anaphora resolution with DialogueStateTracker.
"""

import pytest
from src.dialogue.tracker import DialogueStateTracker
from src.dialogue.state import AnaphoraContext


class TestAnaphoraIntegration:
    """Test anaphora resolution integration with DialogueStateTracker."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tracker = DialogueStateTracker()
    
    def test_resolve_anaphora_with_tracker(self):
        """Test anaphora resolution through DialogueStateTracker."""
        # Create a session
        state = self.tracker.create_session(
            language="english",
            is_code_mixed=False
        )
        session_id = state.session_id
        
        # Update anaphora context with some entities
        self.tracker.update_anaphora_context(
            session_id,
            order_id="ORD123",
            item="pizza",
            time="2:30 PM"
        )
        
        # Test anaphora resolution
        utterance = "Cancel that order"
        resolved = self.tracker.resolve_anaphora(session_id, utterance)
        
        assert resolved == "Cancel order ORD123"
    
    def test_resolve_anaphora_updates_context(self):
        """Test that anaphora resolution updates context with new entities."""
        # Create a session
        state = self.tracker.create_session(
            language="english",
            is_code_mixed=False
        )
        session_id = state.session_id
        
        # Resolve utterance with new entities
        utterance = "I want to order 3 burgers"
        resolved = self.tracker.resolve_anaphora(session_id, utterance)
        
        # Should remain unchanged (no anaphora)
        assert resolved == utterance
        
        # But context should be updated
        state = self.tracker.get_session(session_id)
        assert state.anaphora_context.last_mentioned_item == "burgers"
        assert state.anaphora_context.last_mentioned_quantity == 3
    
    def test_resolve_anaphora_conversation_flow(self):
        """Test anaphora resolution in a multi-turn conversation."""
        # Create a session
        state = self.tracker.create_session(
            language="english",
            is_code_mixed=False
        )
        session_id = state.session_id
        
        # First turn: establish entities
        utterance1 = "I want to order 2 pizzas for delivery to Main Street"
        resolved1 = self.tracker.resolve_anaphora(session_id, utterance1)
        assert resolved1 == utterance1  # No anaphora to resolve
        
        # Second turn: use anaphoric references
        utterance2 = "Actually, make that 3 and deliver there"
        resolved2 = self.tracker.resolve_anaphora(session_id, utterance2)
        
        # Should resolve "there" to "Main Street"
        assert "Main Street" in resolved2
        
        # Context should be updated with new quantity
        state = self.tracker.get_session(session_id)
        assert state.anaphora_context.last_mentioned_quantity == 3
    
    def test_resolve_anaphora_multilingual(self):
        """Test anaphora resolution with different languages."""
        # Create a session
        state = self.tracker.create_session(
            language="hindi",
            is_code_mixed=False
        )
        session_id = state.session_id
        
        # Update context
        self.tracker.update_anaphora_context(
            session_id,
            order_id="ORD456"
        )
        
        # Test Hindi anaphora resolution
        utterance = "मैं वह ऑर्डर कैंसल करना चाहता हूं"  # "I want to cancel that order"
        resolved = self.tracker.resolve_anaphora(session_id, utterance, language="hindi")
        
        # Should resolve the Hindi anaphoric reference
        assert "ORD456" in resolved
    
    def test_resolve_anaphora_session_not_found(self):
        """Test anaphora resolution with invalid session ID."""
        with pytest.raises(ValueError, match="Session .* not found"):
            self.tracker.resolve_anaphora("invalid_session", "test utterance")
    
    def test_get_context_includes_anaphora_context(self):
        """Test that LLM context includes anaphora context."""
        # Create a session
        state = self.tracker.create_session(
            language="english",
            is_code_mixed=False
        )
        session_id = state.session_id
        
        # Update anaphora context
        self.tracker.update_anaphora_context(
            session_id,
            order_id="ORD789",
            item="sandwich",
            time="3:00 PM"
        )
        
        # Get context for LLM
        context = self.tracker.get_context_for_llm(session_id)
        
        # Should include anaphora context
        assert "anaphora_context" in context
        assert context["anaphora_context"]["last_order"] == "ORD789"
        assert context["anaphora_context"]["last_item"] == "sandwich"
        assert context["anaphora_context"]["last_time"] == "3:00 PM"
    
    def test_anaphora_resolver_initialization(self):
        """Test that anaphora resolver is properly initialized."""
        tracker = DialogueStateTracker()
        assert tracker.anaphora_resolver is not None
        assert hasattr(tracker.anaphora_resolver, 'resolve_references')
        assert hasattr(tracker.anaphora_resolver, 'detect_anaphora')
        assert hasattr(tracker.anaphora_resolver, 'extract_entities')