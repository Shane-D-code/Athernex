"""Unit tests for dialogue state data models."""

import pytest
from datetime import datetime, timedelta

from dialogue.state import (
    DialogueState,
    SlotValue,
    ConversationTurn,
    AnaphoraContext,
    DialogueStateSnapshot,
)


def test_dialogue_state_initialization():
    """Test that DialogueState initializes with correct defaults."""
    state = DialogueState()
    
    assert state.session_id is not None
    assert state.turn_count == 0
    assert state.created_at is not None
    assert state.last_updated is not None
    assert state.expires_at > datetime.utcnow()
    assert len(state.slots) == 0
    assert len(state.conversation_history) == 0
    assert state.anaphora_context is not None


def test_dialogue_state_add_turn():
    """Test adding conversation turns."""
    state = DialogueState()
    
    state.add_turn(
        user_utterance="I want to order 2 pizzas",
        system_response="Sure, 2 pizzas. When would you like delivery?",
        extracted_data={"intent": "place_order", "items": ["pizza"]},
        confidence=0.9,
    )
    
    assert state.turn_count == 1
    assert len(state.conversation_history) == 1
    
    turn = state.conversation_history[0]
    assert turn.turn == 1
    assert turn.user_utterance == "I want to order 2 pizzas"
    assert turn.system_response == "Sure, 2 pizzas. When would you like delivery?"
    assert turn.confidence == 0.9


def test_dialogue_state_set_slot():
    """Test setting slot values."""
    state = DialogueState()
    state.turn_count = 1
    
    state.set_slot("intent", "place_order", confidence=0.9)
    state.set_slot("items", ["pizza", "burger"], confidence=0.85)
    
    assert len(state.slots) == 2
    assert state.slots["intent"].value == "place_order"
    assert state.slots["intent"].confidence == 0.9
    assert state.slots["intent"].last_updated_turn == 1
    assert state.slots["items"].value == ["pizza", "burger"]


def test_dialogue_state_update_slot():
    """Test updating slot values with confidence comparison."""
    state = DialogueState()
    state.turn_count = 1
    
    # Set initial slot
    state.set_slot("intent", "place_order", confidence=0.7)
    
    # Update with higher confidence - should update
    state.turn_count = 2
    state.update_slot("intent", "modify_order", confidence=0.9)
    assert state.slots["intent"].value == "modify_order"
    assert state.slots["intent"].confidence == 0.9
    assert state.slots["intent"].last_updated_turn == 2
    
    # Update with lower confidence - should not update
    state.turn_count = 3
    state.update_slot("intent", "cancel_order", confidence=0.5)
    assert state.slots["intent"].value == "modify_order"  # Unchanged
    assert state.slots["intent"].confidence == 0.9  # Unchanged


def test_dialogue_state_get_slot():
    """Test retrieving slot values."""
    state = DialogueState()
    state.turn_count = 1
    
    state.set_slot("delivery_time", "2024-01-15T19:00:00Z", confidence=0.8)
    
    slot = state.get_slot("delivery_time")
    assert slot is not None
    assert slot.value == "2024-01-15T19:00:00Z"
    assert slot.confidence == 0.8
    
    # Non-existent slot
    slot = state.get_slot("nonexistent")
    assert slot is None


def test_dialogue_state_expiration():
    """Test session expiration logic."""
    state = DialogueState()
    
    # Should not be expired initially
    assert not state.is_expired()
    
    # Manually set expiration to past
    state.expires_at = datetime.utcnow() - timedelta(minutes=1)
    assert state.is_expired()
    
    # Extend expiration
    state.extend_expiration(minutes=10)
    assert not state.is_expired()
    assert state.expires_at > datetime.utcnow()


def test_dialogue_state_should_expire_by_turns():
    """Test turn-based expiration."""
    state = DialogueState()
    
    assert not state.should_expire_by_turns(max_turns=10)
    
    # Add 10 turns
    for i in range(10):
        state.add_turn(f"utterance {i}", f"response {i}")
    
    assert state.should_expire_by_turns(max_turns=10)


def test_dialogue_state_should_summarize():
    """Test token-based summarization trigger."""
    state = DialogueState()
    
    assert not state.should_summarize(max_tokens=8000)
    
    # Manually set high token count
    state.total_tokens = 9000
    assert state.should_summarize(max_tokens=8000)


def test_dialogue_state_get_recent_turns():
    """Test retrieving recent conversation turns."""
    state = DialogueState()
    
    # Add 5 turns
    for i in range(5):
        state.add_turn(f"utterance {i}", f"response {i}")
    
    recent = state.get_recent_turns(n=3)
    assert len(recent) == 3
    assert recent[0].turn == 3
    assert recent[1].turn == 4
    assert recent[2].turn == 5


def test_dialogue_state_clear_slots():
    """Test clearing all slots."""
    state = DialogueState()
    state.turn_count = 1
    
    state.set_slot("intent", "place_order", confidence=0.9)
    state.set_slot("items", ["pizza"], confidence=0.8)
    
    assert len(state.slots) == 2
    
    state.clear_slots()
    assert len(state.slots) == 0


def test_dialogue_state_reset_session():
    """Test resetting the entire session."""
    state = DialogueState()
    
    # Add some data
    state.add_turn("utterance", "response")
    state.set_slot("intent", "place_order", confidence=0.9)
    state.anaphora_context.last_mentioned_order = "ORD-123"
    
    # Reset
    state.reset_session()
    
    assert state.turn_count == 0
    assert len(state.slots) == 0
    assert len(state.conversation_history) == 0
    assert state.anaphora_context.last_mentioned_order is None
    assert state.total_tokens == 0


def test_dialogue_state_get_context_summary():
    """Test generating context summary."""
    state = DialogueState()
    
    state.add_turn("I want pizza", "Sure, how many?")
    state.set_slot("intent", "place_order", confidence=0.9)
    
    summary = state.get_context_summary()
    
    assert "intent" in summary
    assert "place_order" in summary
    assert "Turn 1" in summary


def test_anaphora_context():
    """Test anaphora context tracking."""
    context = AnaphoraContext()
    
    assert context.last_mentioned_order is None
    assert context.last_mentioned_item is None
    assert context.last_mentioned_time is None
    
    context.last_mentioned_order = "ORD-123"
    context.last_mentioned_item = "pizza"
    
    assert context.last_mentioned_order == "ORD-123"
    assert context.last_mentioned_item == "pizza"


def test_dialogue_state_snapshot_serialization():
    """Test serializing and deserializing dialogue state."""
    # Create a state with data
    state = DialogueState()
    state.language = "en"
    state.is_code_mixed = True
    
    state.add_turn("utterance 1", "response 1", confidence=0.9)
    state.add_turn("utterance 2", "response 2", confidence=0.85)
    
    state.set_slot("intent", "place_order", confidence=0.9)
    state.set_slot("items", ["pizza", "burger"], confidence=0.8)
    
    state.anaphora_context.last_mentioned_order = "ORD-123"
    state.anaphora_context.last_mentioned_item = "pizza"
    
    # Create snapshot
    snapshot = DialogueStateSnapshot.from_dialogue_state(state)
    
    assert snapshot.session_id == state.session_id
    assert snapshot.turn_count == 2
    assert snapshot.language == "en"
    assert snapshot.is_code_mixed is True
    assert len(snapshot.slots) == 2
    assert len(snapshot.conversation_history) == 2
    assert snapshot.anaphora_context["last_mentioned_order"] == "ORD-123"
    
    # Restore from snapshot
    restored_state = snapshot.to_dialogue_state()
    
    assert restored_state.session_id == state.session_id
    assert restored_state.turn_count == state.turn_count
    assert restored_state.language == state.language
    assert restored_state.is_code_mixed == state.is_code_mixed
    assert len(restored_state.slots) == len(state.slots)
    assert len(restored_state.conversation_history) == len(state.conversation_history)
    assert restored_state.anaphora_context.last_mentioned_order == "ORD-123"
    assert restored_state.anaphora_context.last_mentioned_item == "pizza"


def test_slot_value_validation():
    """Test SlotValue validation."""
    # Valid slot
    slot = SlotValue(value="test", confidence=0.8, last_updated_turn=1)
    assert slot.confidence == 0.8
    
    # Invalid confidence (should raise validation error)
    with pytest.raises(Exception):  # Pydantic ValidationError
        SlotValue(value="test", confidence=1.5, last_updated_turn=1)
    
    with pytest.raises(Exception):
        SlotValue(value="test", confidence=-0.1, last_updated_turn=1)


def test_conversation_turn_timestamp():
    """Test that conversation turns have timestamps."""
    turn = ConversationTurn(
        turn=1,
        user_utterance="test utterance",
        system_response="test response",
    )
    
    assert turn.timestamp is not None
    assert isinstance(turn.timestamp, datetime)
    assert turn.timestamp <= datetime.utcnow()
