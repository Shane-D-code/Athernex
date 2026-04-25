"""Unit tests for DialogueStateTracker class."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from dialogue.tracker import DialogueStateTracker
from dialogue.state import DialogueState, SlotValue


class TestDialogueStateTracker:
    """Test suite for DialogueStateTracker functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tracker = DialogueStateTracker(
            max_turns=10,
            max_duration_minutes=5,
            max_tokens=8000,
        )
    
    def test_initialization(self):
        """Test DialogueStateTracker initialization."""
        assert self.tracker.max_turns == 10
        assert self.tracker.max_duration_minutes == 5
        assert self.tracker.max_tokens == 8000
        assert len(self.tracker._sessions) == 0
    
    def test_create_session_with_defaults(self):
        """Test creating a session with default parameters."""
        state = self.tracker.create_session()
        
        assert state.session_id is not None
        assert state.turn_count == 0
        assert state.language is None
        assert state.is_code_mixed is False
        assert len(state.slots) == 0
        assert len(state.conversation_history) == 0
        
        # Verify session is stored
        assert state.session_id in self.tracker._sessions
    
    def test_create_session_with_custom_params(self):
        """Test creating a session with custom parameters."""
        session_id = "test-session-123"
        state = self.tracker.create_session(
            session_id=session_id,
            language="en",
            is_code_mixed=True,
        )
        
        assert state.session_id == session_id
        assert state.language == "en"
        assert state.is_code_mixed is True
        
        # Verify session is stored with correct ID
        assert session_id in self.tracker._sessions
        assert self.tracker._sessions[session_id] == state
    
    def test_create_session_duplicate_id(self):
        """Test creating a session with duplicate ID returns existing session."""
        session_id = "duplicate-session"
        
        # Create first session
        state1 = self.tracker.create_session(session_id=session_id, language="en")
        
        # Try to create with same ID
        state2 = self.tracker.create_session(session_id=session_id, language="es")
        
        # Should return the same session
        assert state1 is state2
        assert state1.language == "en"  # Original language preserved
    
    def test_get_session_existing(self):
        """Test retrieving an existing session."""
        # Create session
        original_state = self.tracker.create_session(language="fr")
        session_id = original_state.session_id
        
        # Retrieve session
        retrieved_state = self.tracker.get_session(session_id)
        
        assert retrieved_state is not None
        assert retrieved_state is original_state
        assert retrieved_state.session_id == session_id
    
    def test_get_session_nonexistent(self):
        """Test retrieving a non-existent session."""
        result = self.tracker.get_session("nonexistent-session")
        assert result is None
    
    def test_get_session_expired_by_time(self):
        """Test that expired sessions are automatically removed."""
        # Create session
        state = self.tracker.create_session()
        session_id = state.session_id
        
        # Manually expire the session
        state.expires_at = datetime.utcnow() - timedelta(minutes=1)
        
        # Try to retrieve - should return None and remove session
        result = self.tracker.get_session(session_id)
        
        assert result is None
        assert session_id not in self.tracker._sessions
    
    def test_get_session_expired_by_turns(self):
        """Test that sessions expire after max turns."""
        # Create session
        state = self.tracker.create_session()
        session_id = state.session_id
        
        # Add max turns
        for i in range(self.tracker.max_turns):
            state.add_turn(f"utterance {i}", f"response {i}")
        
        # Try to retrieve - should return None and remove session
        result = self.tracker.get_session(session_id)
        
        assert result is None
        assert session_id not in self.tracker._sessions
    
    def test_get_or_create_session_existing(self):
        """Test get_or_create with existing session."""
        # Create session
        original_state = self.tracker.create_session(language="en")
        session_id = original_state.session_id
        
        # Get or create with same ID
        retrieved_state = self.tracker.get_or_create_session(
            session_id=session_id,
            language="es"  # Different language
        )
        
        # Should return existing session
        assert retrieved_state is original_state
        assert retrieved_state.language == "en"  # Original language preserved
    
    def test_get_or_create_session_new(self):
        """Test get_or_create with new session."""
        session_id = "new-session"
        
        # Get or create new session
        state = self.tracker.get_or_create_session(
            session_id=session_id,
            language="de",
            is_code_mixed=True
        )
        
        assert state.session_id == session_id
        assert state.language == "de"
        assert state.is_code_mixed is True
        assert session_id in self.tracker._sessions
    
    def test_update_session_success(self):
        """Test updating a session with new conversation turn."""
        # Create session
        state = self.tracker.create_session()
        session_id = state.session_id
        
        # Update session
        updated_state = self.tracker.update_session(
            session_id=session_id,
            user_utterance="I want to order pizza",
            system_response="Sure, how many pizzas?",
            extracted_data={"intent": "place_order", "items": ["pizza"]},
            confidence=0.9
        )
        
        assert updated_state is state
        assert updated_state.turn_count == 1
        assert len(updated_state.conversation_history) == 1
        
        turn = updated_state.conversation_history[0]
        assert turn.user_utterance == "I want to order pizza"
        assert turn.system_response == "Sure, how many pizzas?"
        assert turn.confidence == 0.9
    
    def test_update_session_nonexistent(self):
        """Test updating a non-existent session raises error."""
        with pytest.raises(ValueError, match="Session .* not found or expired"):
            self.tracker.update_session(
                session_id="nonexistent",
                user_utterance="test",
            )
    
    def test_update_session_extends_expiration(self):
        """Test that updating a session extends its expiration."""
        # Create session
        state = self.tracker.create_session()
        session_id = state.session_id
        original_expiration = state.expires_at
        
        # Wait a bit and update
        import time
        time.sleep(0.01)
        
        self.tracker.update_session(
            session_id=session_id,
            user_utterance="test utterance"
        )
        
        # Expiration should be extended
        assert state.expires_at > original_expiration
    
    def test_update_session_triggers_summarization(self):
        """Test that updating triggers summarization when token limit exceeded."""
        # Create session
        state = self.tracker.create_session()
        session_id = state.session_id
        
        # Manually set high token count
        state.total_tokens = 9000  # Above max_tokens=8000
        
        # Mock the summarization method
        with patch.object(self.tracker, '_summarize_context') as mock_summarize:
            self.tracker.update_session(
                session_id=session_id,
                user_utterance="test utterance"
            )
            
            mock_summarize.assert_called_once_with(state)
    
    def test_merge_slots_new_slots(self):
        """Test merging new slots into empty session."""
        # Create session
        state = self.tracker.create_session()
        session_id = state.session_id
        
        # Merge new slots
        new_slots = {
            "intent": "place_order",
            "items": ["pizza", "burger"],
            "quantity": 2
        }
        
        updated_state = self.tracker.merge_slots(
            session_id=session_id,
            new_slots=new_slots,
            confidence=0.8
        )
        
        assert updated_state is state
        assert len(updated_state.slots) == 3
        assert updated_state.slots["intent"].value == "place_order"
        assert updated_state.slots["intent"].confidence == 0.8
        assert updated_state.slots["items"].value == ["pizza", "burger"]
        assert updated_state.slots["quantity"].value == 2
    
    def test_merge_slots_confidence_based_update(self):
        """Test that slots are only updated when new confidence is higher."""
        # Create session with existing slots
        state = self.tracker.create_session()
        session_id = state.session_id
        
        # Set initial slot with high confidence
        state.set_slot("intent", "place_order", confidence=0.9)
        
        # Try to merge with lower confidence - should not update
        self.tracker.merge_slots(
            session_id=session_id,
            new_slots={"intent": "cancel_order"},
            confidence=0.7
        )
        
        assert state.slots["intent"].value == "place_order"  # Unchanged
        assert state.slots["intent"].confidence == 0.9  # Unchanged
        
        # Try to merge with higher confidence - should update
        self.tracker.merge_slots(
            session_id=session_id,
            new_slots={"intent": "modify_order"},
            confidence=0.95
        )
        
        assert state.slots["intent"].value == "modify_order"  # Updated
        assert state.slots["intent"].confidence == 0.95  # Updated
    
    def test_merge_slots_skip_none_values(self):
        """Test that None values are skipped during merging."""
        # Create session
        state = self.tracker.create_session()
        session_id = state.session_id
        
        # Merge slots with None values
        new_slots = {
            "intent": "place_order",
            "items": None,  # Should be skipped
            "quantity": 2
        }
        
        self.tracker.merge_slots(
            session_id=session_id,
            new_slots=new_slots,
            confidence=0.8
        )
        
        assert len(state.slots) == 2  # Only 2 slots, None was skipped
        assert "intent" in state.slots
        assert "quantity" in state.slots
        assert "items" not in state.slots
    
    def test_merge_slots_nonexistent_session(self):
        """Test merging slots for non-existent session raises error."""
        with pytest.raises(ValueError, match="Session .* not found or expired"):
            self.tracker.merge_slots(
                session_id="nonexistent",
                new_slots={"intent": "test"}
            )
    
    def test_delete_session_existing(self):
        """Test deleting an existing session."""
        # Create session
        state = self.tracker.create_session()
        session_id = state.session_id
        
        # Verify session exists
        assert session_id in self.tracker._sessions
        
        # Delete session
        result = self.tracker.delete_session(session_id)
        
        assert result is True
        assert session_id not in self.tracker._sessions
    
    def test_delete_session_nonexistent(self):
        """Test deleting a non-existent session."""
        result = self.tracker.delete_session("nonexistent")
        assert result is False
    
    def test_cleanup_expired_sessions(self):
        """Test cleaning up expired sessions."""
        # Create multiple sessions
        state1 = self.tracker.create_session()
        state2 = self.tracker.create_session()
        state3 = self.tracker.create_session()
        
        # Expire two sessions
        state1.expires_at = datetime.utcnow() - timedelta(minutes=1)
        state2.turn_count = self.tracker.max_turns  # Expire by turns
        # state3 remains valid
        
        # Cleanup expired sessions
        deleted_count = self.tracker.cleanup_expired_sessions()
        
        assert deleted_count == 2
        assert state1.session_id not in self.tracker._sessions
        assert state2.session_id not in self.tracker._sessions
        assert state3.session_id in self.tracker._sessions
    
    def test_get_active_session_count(self):
        """Test getting active session count."""
        assert self.tracker.get_active_session_count() == 0
        
        # Create sessions
        self.tracker.create_session()
        self.tracker.create_session()
        
        assert self.tracker.get_active_session_count() == 2
    
    def test_get_all_session_ids(self):
        """Test getting all session IDs."""
        assert self.tracker.get_all_session_ids() == []
        
        # Create sessions
        state1 = self.tracker.create_session()
        state2 = self.tracker.create_session()
        
        session_ids = self.tracker.get_all_session_ids()
        assert len(session_ids) == 2
        assert state1.session_id in session_ids
        assert state2.session_id in session_ids
    
    def test_summarize_context_keeps_recent_turns(self):
        """Test that context summarization keeps recent turns."""
        # Create session with many turns
        state = self.tracker.create_session()
        
        # Add 6 turns
        for i in range(6):
            state.add_turn(f"utterance {i}", f"response {i}")
        
        # Summarize context
        self.tracker._summarize_context(state)
        
        # Should keep only 3 most recent turns
        assert len(state.conversation_history) == 3
        assert state.conversation_history[0].turn == 4  # Turn 4, 5, 6 kept
        assert state.conversation_history[1].turn == 5
        assert state.conversation_history[2].turn == 6
    
    def test_summarize_context_no_effect_on_few_turns(self):
        """Test that summarization has no effect when few turns exist."""
        # Create session with few turns
        state = self.tracker.create_session()
        
        # Add only 2 turns
        state.add_turn("utterance 1", "response 1")
        state.add_turn("utterance 2", "response 2")
        
        original_history = state.conversation_history.copy()
        
        # Summarize context
        self.tracker._summarize_context(state)
        
        # History should be unchanged
        assert len(state.conversation_history) == 2
        assert state.conversation_history == original_history
    
    def test_update_anaphora_context(self):
        """Test updating anaphora context."""
        # Create session
        state = self.tracker.create_session()
        session_id = state.session_id
        
        # Update anaphora context
        updated_state = self.tracker.update_anaphora_context(
            session_id=session_id,
            order_id="ORD-123",
            item="pizza",
            time="2024-01-15T19:00:00Z",
            quantity=2,
            location="downtown"
        )
        
        assert updated_state is state
        assert state.anaphora_context.last_mentioned_order == "ORD-123"
        assert state.anaphora_context.last_mentioned_item == "pizza"
        assert state.anaphora_context.last_mentioned_time == "2024-01-15T19:00:00Z"
        assert state.anaphora_context.last_mentioned_quantity == 2
        assert state.anaphora_context.last_mentioned_location == "downtown"
    
    def test_update_anaphora_context_partial(self):
        """Test updating anaphora context with partial data."""
        # Create session
        state = self.tracker.create_session()
        session_id = state.session_id
        
        # Set initial context
        state.anaphora_context.last_mentioned_order = "ORD-123"
        state.anaphora_context.last_mentioned_item = "pizza"
        
        # Update only some fields
        self.tracker.update_anaphora_context(
            session_id=session_id,
            item="burger",  # Update item
            quantity=3      # Add quantity
            # Don't update order_id
        )
        
        # Check that only specified fields were updated
        assert state.anaphora_context.last_mentioned_order == "ORD-123"  # Unchanged
        assert state.anaphora_context.last_mentioned_item == "burger"    # Updated
        assert state.anaphora_context.last_mentioned_quantity == 3       # Added
    
    def test_update_anaphora_context_nonexistent_session(self):
        """Test updating anaphora context for non-existent session."""
        with pytest.raises(ValueError, match="Session .* not found or expired"):
            self.tracker.update_anaphora_context(
                session_id="nonexistent",
                order_id="ORD-123"
            )
    
    def test_get_context_for_llm(self):
        """Test getting formatted context for LLM processing."""
        # Create session with data
        state = self.tracker.create_session(language="en", is_code_mixed=True)
        session_id = state.session_id
        
        # Add conversation turns
        state.add_turn("I want pizza", "How many pizzas?")
        state.add_turn("Two pizzas", "What size?")
        state.add_turn("Large pizzas", "Got it, 2 large pizzas")
        
        # Add slots
        state.set_slot("intent", "place_order", confidence=0.9)
        state.set_slot("items", ["pizza"], confidence=0.8)
        state.set_slot("quantity", 2, confidence=0.85)
        
        # Set anaphora context
        state.anaphora_context.last_mentioned_order = "ORD-123"
        state.anaphora_context.last_mentioned_item = "pizza"
        state.anaphora_context.last_mentioned_time = "19:00"
        
        # Get context for LLM
        context = self.tracker.get_context_for_llm(session_id)
        
        # Verify structure
        assert context["session_id"] == session_id
        assert context["turn_count"] == 3
        assert context["language"] == "en"
        assert context["is_code_mixed"] is True
        
        # Verify conversation (should include all 3 turns since <= 3)
        assert len(context["conversation"]) == 3
        assert context["conversation"][0]["turn"] == 1
        assert context["conversation"][0]["user"] == "I want pizza"
        assert context["conversation"][2]["turn"] == 3
        
        # Verify slots
        assert len(context["slots"]) == 3
        assert context["slots"]["intent"]["value"] == "place_order"
        assert context["slots"]["intent"]["confidence"] == 0.9
        
        # Verify anaphora context
        assert context["anaphora_context"]["last_order"] == "ORD-123"
        assert context["anaphora_context"]["last_item"] == "pizza"
        assert context["anaphora_context"]["last_time"] == "19:00"
    
    def test_get_context_for_llm_nonexistent_session(self):
        """Test getting context for non-existent session returns empty dict."""
        context = self.tracker.get_context_for_llm("nonexistent")
        assert context == {}
    
    def test_get_context_for_llm_limits_recent_turns(self):
        """Test that LLM context limits to 3 most recent turns."""
        # Create session with many turns
        state = self.tracker.create_session()
        session_id = state.session_id
        
        # Add 5 turns
        for i in range(5):
            state.add_turn(f"utterance {i}", f"response {i}")
        
        # Get context
        context = self.tracker.get_context_for_llm(session_id)
        
        # Should only include 3 most recent turns
        assert len(context["conversation"]) == 3
        assert context["conversation"][0]["turn"] == 3  # Turns 3, 4, 5
        assert context["conversation"][1]["turn"] == 4
        assert context["conversation"][2]["turn"] == 5


class TestDialogueStateTrackerIntegration:
    """Integration tests for DialogueStateTracker with realistic scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tracker = DialogueStateTracker()
    
    def test_complete_order_conversation_flow(self):
        """Test a complete order conversation flow."""
        # Start conversation
        session_id = "order-session-1"
        state = self.tracker.create_session(session_id=session_id, language="en")
        
        # Turn 1: Initial order request
        self.tracker.update_session(
            session_id=session_id,
            user_utterance="I want to order 2 large pizzas",
            system_response="Great! 2 large pizzas. What toppings would you like?",
            extracted_data={"intent": "place_order", "items": ["pizza"], "quantity": 2, "size": "large"},
            confidence=0.9
        )
        
        # Merge extracted slots
        self.tracker.merge_slots(
            session_id=session_id,
            new_slots={"intent": "place_order", "items": ["pizza"], "quantity": 2, "size": "large"},
            confidence=0.9
        )
        
        # Turn 2: Add toppings
        self.tracker.update_session(
            session_id=session_id,
            user_utterance="Pepperoni and mushrooms please",
            system_response="Perfect! 2 large pepperoni and mushroom pizzas. When would you like delivery?",
            extracted_data={"toppings": ["pepperoni", "mushrooms"]},
            confidence=0.85
        )
        
        # Merge new slot data
        self.tracker.merge_slots(
            session_id=session_id,
            new_slots={"toppings": ["pepperoni", "mushrooms"]},
            confidence=0.85
        )
        
        # Turn 3: Delivery time
        self.tracker.update_session(
            session_id=session_id,
            user_utterance="7 PM tonight",
            system_response="Got it! 2 large pepperoni and mushroom pizzas for 7 PM tonight. Your total is $24.99. Confirm order?",
            extracted_data={"delivery_time": "2024-01-15T19:00:00Z"},
            confidence=0.8
        )
        
        # Merge delivery time
        self.tracker.merge_slots(
            session_id=session_id,
            new_slots={"delivery_time": "2024-01-15T19:00:00Z"},
            confidence=0.8
        )
        
        # Update anaphora context
        self.tracker.update_anaphora_context(
            session_id=session_id,
            item="pizza",
            time="2024-01-15T19:00:00Z",
            quantity=2
        )
        
        # Verify final state
        final_state = self.tracker.get_session(session_id)
        assert final_state is not None
        assert final_state.turn_count == 3
        assert len(final_state.slots) == 6  # intent, items, quantity, size, toppings, delivery_time
        assert final_state.slots["intent"].value == "place_order"
        assert final_state.slots["quantity"].value == 2
        assert final_state.slots["toppings"].value == ["pepperoni", "mushrooms"]
        
        # Verify anaphora context
        assert final_state.anaphora_context.last_mentioned_item == "pizza"
        assert final_state.anaphora_context.last_mentioned_quantity == 2
        
        # Get LLM context
        llm_context = self.tracker.get_context_for_llm(session_id)
        assert llm_context["turn_count"] == 3
        assert len(llm_context["conversation"]) == 3
        assert len(llm_context["slots"]) == 6
    
    def test_session_expiration_and_cleanup(self):
        """Test session expiration and cleanup functionality."""
        # Create multiple sessions
        session1 = self.tracker.create_session(session_id="session-1")
        session2 = self.tracker.create_session(session_id="session-2")
        session3 = self.tracker.create_session(session_id="session-3")
        
        # Add turns to session2 to make it expire by turn count
        for i in range(10):  # Max turns = 10
            session2.add_turn(f"utterance {i}", f"response {i}")
        
        # Manually expire session3 by time
        session3.expires_at = datetime.utcnow() - timedelta(minutes=1)
        
        # Verify all sessions exist initially
        assert self.tracker.get_active_session_count() == 3
        
        # Try to access expired sessions - should trigger cleanup
        result1 = self.tracker.get_session("session-1")  # Should work
        result2 = self.tracker.get_session("session-2")  # Should be None (expired by turns)
        result3 = self.tracker.get_session("session-3")  # Should be None (expired by time)
        
        assert result1 is not None
        assert result2 is None
        assert result3 is None
        
        # Only session1 should remain
        assert self.tracker.get_active_session_count() == 1
        assert "session-1" in self.tracker.get_all_session_ids()
        assert "session-2" not in self.tracker.get_all_session_ids()
        assert "session-3" not in self.tracker.get_all_session_ids()
    
    def test_slot_confidence_merging_scenarios(self):
        """Test various slot confidence merging scenarios."""
        session_id = "confidence-test"
        state = self.tracker.create_session(session_id=session_id)
        
        # Initial low-confidence extraction
        self.tracker.merge_slots(
            session_id=session_id,
            new_slots={"intent": "place_order", "items": ["pizza"], "quantity": 1},
            confidence=0.6
        )
        
        # Higher confidence update should override
        self.tracker.merge_slots(
            session_id=session_id,
            new_slots={"intent": "place_order", "items": ["burger"], "quantity": 2},
            confidence=0.9
        )
        
        # Lower confidence update should not override
        self.tracker.merge_slots(
            session_id=session_id,
            new_slots={"intent": "cancel_order", "items": ["pizza"], "quantity": 1},
            confidence=0.7
        )
        
        # Verify final state uses highest confidence values
        final_state = self.tracker.get_session(session_id)
        assert final_state.slots["intent"].value == "place_order"  # 0.9 confidence
        assert final_state.slots["items"].value == ["burger"]      # 0.9 confidence
        assert final_state.slots["quantity"].value == 2            # 0.9 confidence
        
        # Verify confidence values
        assert final_state.slots["intent"].confidence == 0.9
        assert final_state.slots["items"].confidence == 0.9
        assert final_state.slots["quantity"].confidence == 0.9