"""
Property-based tests for context preservation.

Tests Property 6: Context preservation
Validates Requirements 11.1, 11.2

These tests verify that:
1. Information from earlier turns is preserved in dialogue state
2. Slot updates don't lose unrelated information
3. Original Structured_Order_Data is maintained during clarification dialogues
4. New information is properly merged with existing data
"""

import pytest
from hypothesis import given, strategies as st, assume
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from dialogue.tracker import DialogueStateTracker
from dialogue.state import DialogueState, SlotValue, AnaphoraContext
from llm.base import StructuredOrderData, Intent, OrderItem


# Strategy for generating slot names
slot_name_strategy = st.sampled_from([
    "order_id", "items", "delivery_time", "special_instructions",
    "customer_name", "phone_number", "address", "payment_method",
    "total_amount", "delivery_fee", "restaurant_id"
])

# Strategy for generating slot values
slot_value_strategy = st.one_of(
    st.text(min_size=1, max_size=50),
    st.integers(min_value=1, max_value=1000),
    st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5)
)

# Strategy for generating confidence scores
confidence_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# Strategy for generating slot dictionaries
slots_dict_strategy = st.dictionaries(
    slot_name_strategy,
    slot_value_strategy,
    min_size=1,
    max_size=8
)

# Strategy for generating user utterances
utterance_strategy = st.text(
    min_size=5, 
    max_size=200,
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P', 'Z'))
)

# Strategy for generating system responses
system_response_strategy = st.one_of(
    st.none(),
    st.text(min_size=10, max_size=100)
)

# Strategy for generating extracted data
extracted_data_strategy = st.one_of(
    st.none(),
    st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(st.text(min_size=1, max_size=50), st.integers(min_value=1, max_value=100)),
        min_size=1,
        max_size=5
    )
)


@given(
    initial_slots=slots_dict_strategy,
    initial_confidence=confidence_strategy,
    additional_slots=slots_dict_strategy,
    additional_confidence=confidence_strategy
)
def test_slot_updates_preserve_unrelated_information(
    initial_slots: Dict[str, Any],
    initial_confidence: float,
    additional_slots: Dict[str, Any],
    additional_confidence: float
):
    """
    **Validates: Requirements 11.1, 11.2**
    
    Property 6a: Slot updates don't lose unrelated information.
    
    When new slots are added or existing slots are updated, unrelated
    slot information should be preserved.
    """
    # Arrange
    tracker = DialogueStateTracker()
    session = tracker.create_session()
    
    # Set initial slots
    tracker.merge_slots(session.session_id, initial_slots, initial_confidence)
    
    # Get slots that won't be updated
    unrelated_slots = {k: v for k, v in initial_slots.items() if k not in additional_slots}
    
    # Act - Add additional slots
    tracker.merge_slots(session.session_id, additional_slots, additional_confidence)
    
    # Assert - Unrelated slots should be preserved
    updated_session = tracker.get_session(session.session_id)
    assert updated_session is not None
    
    for slot_name, expected_value in unrelated_slots.items():
        slot = updated_session.get_slot(slot_name)
        assert slot is not None, f"Unrelated slot '{slot_name}' was lost"
        assert slot.value == expected_value, \
            f"Unrelated slot '{slot_name}' value changed: {slot.value} != {expected_value}"
        assert slot.confidence == initial_confidence, \
            f"Unrelated slot '{slot_name}' confidence changed"


@given(
    initial_slots=slots_dict_strategy,
    initial_confidence=confidence_strategy,
    turns_data=st.lists(
        st.tuples(utterance_strategy, system_response_strategy, extracted_data_strategy, confidence_strategy),
        min_size=1,
        max_size=5
    )
)
def test_conversation_turns_preserve_earlier_information(
    initial_slots: Dict[str, Any],
    initial_confidence: float,
    turns_data: List[tuple]
):
    """
    **Validates: Requirements 11.1, 11.2**
    
    Property 6b: Information from earlier turns is preserved in dialogue state.
    
    When new conversation turns are added, information from earlier turns
    should remain accessible in the dialogue state.
    """
    # Arrange
    tracker = DialogueStateTracker()
    session = tracker.create_session()
    
    # Set initial slots
    tracker.merge_slots(session.session_id, initial_slots, initial_confidence)
    
    # Act - Add multiple conversation turns
    for user_utterance, system_response, extracted_data, turn_confidence in turns_data:
        tracker.update_session(
            session.session_id,
            user_utterance,
            system_response,
            extracted_data,
            turn_confidence
        )
    
    # Assert - Initial slots should still be preserved
    updated_session = tracker.get_session(session.session_id)
    assert updated_session is not None
    
    for slot_name, expected_value in initial_slots.items():
        slot = updated_session.get_slot(slot_name)
        assert slot is not None, f"Initial slot '{slot_name}' was lost after {len(turns_data)} turns"
        assert slot.value == expected_value, \
            f"Initial slot '{slot_name}' value changed after conversation turns"
    
    # Verify all turns are preserved
    assert len(updated_session.conversation_history) == len(turns_data)
    
    for i, (expected_utterance, expected_response, _, expected_confidence) in enumerate(turns_data):
        turn = updated_session.conversation_history[i]
        assert turn.user_utterance == expected_utterance
        assert turn.system_response == expected_response
        assert turn.confidence == expected_confidence


@given(
    original_slots=slots_dict_strategy,
    original_confidence=confidence_strategy,
    clarification_slots=slots_dict_strategy,
    clarification_confidence=confidence_strategy
)
def test_clarification_dialogue_maintains_original_data(
    original_slots: Dict[str, Any],
    original_confidence: float,
    clarification_slots: Dict[str, Any],
    clarification_confidence: float
):
    """
    **Validates: Requirements 11.1, 11.2**
    
    Property 6c: Original Structured_Order_Data is maintained during clarification dialogues.
    
    When a clarification dialogue begins, the original order data should be preserved
    and new information should be merged without losing existing data.
    """
    # Arrange
    tracker = DialogueStateTracker()
    session = tracker.create_session()
    
    # Set original order data
    tracker.merge_slots(session.session_id, original_slots, original_confidence, "user")
    
    # Simulate clarification dialogue by adding clarification turn
    tracker.update_session(
        session.session_id,
        "Can you clarify the delivery time?",
        "What time would you like your order delivered?",
        {"intent": "clarify_delivery_time"},
        0.9
    )
    
    # Act - Provide clarification information
    tracker.merge_slots(session.session_id, clarification_slots, clarification_confidence, "user")
    
    # Assert - Original data should be maintained
    updated_session = tracker.get_session(session.session_id)
    assert updated_session is not None
    
    # Check that original slots are preserved (unless explicitly updated)
    for slot_name, expected_value in original_slots.items():
        slot = updated_session.get_slot(slot_name)
        assert slot is not None, f"Original slot '{slot_name}' was lost during clarification"
        
        if slot_name in clarification_slots:
            # If slot was updated during clarification, check confidence-based merging
            if clarification_confidence >= original_confidence:
                assert slot.value == clarification_slots[slot_name], \
                    f"Slot '{slot_name}' should be updated with clarification value"
            else:
                assert slot.value == expected_value, \
                    f"Slot '{slot_name}' should keep original value (higher confidence)"
        else:
            # Unrelated slots should remain unchanged
            assert slot.value == expected_value, \
                f"Unrelated slot '{slot_name}' changed during clarification"


@given(
    base_slots=slots_dict_strategy,
    base_confidence=confidence_strategy,
    update_slots=slots_dict_strategy,
    update_confidence=confidence_strategy
)
def test_confidence_based_slot_merging_preserves_high_confidence_data(
    base_slots: Dict[str, Any],
    base_confidence: float,
    update_slots: Dict[str, Any],
    update_confidence: float
):
    """
    **Validates: Requirements 11.1, 11.2**
    
    Property 6d: Confidence-based merging preserves high-confidence information.
    
    When merging new information, slots with higher confidence should be preserved,
    and lower confidence updates should not overwrite them.
    """
    # Arrange
    tracker = DialogueStateTracker()
    session = tracker.create_session()
    
    # Set base slots
    tracker.merge_slots(session.session_id, base_slots, base_confidence)
    
    # Act - Attempt to update with new slots
    tracker.merge_slots(session.session_id, update_slots, update_confidence)
    
    # Assert - Check confidence-based merging behavior
    updated_session = tracker.get_session(session.session_id)
    assert updated_session is not None
    
    for slot_name, base_value in base_slots.items():
        slot = updated_session.get_slot(slot_name)
        assert slot is not None
        
        if slot_name in update_slots:
            update_value = update_slots[slot_name]
            
            if update_confidence >= base_confidence:
                # Higher or equal confidence should update the slot
                assert slot.value == update_value, \
                    f"Slot '{slot_name}' should be updated (confidence {update_confidence} >= {base_confidence})"
                assert slot.confidence == update_confidence
            else:
                # Lower confidence should not update the slot
                assert slot.value == base_value, \
                    f"Slot '{slot_name}' should preserve original value (confidence {base_confidence} > {update_confidence})"
                assert slot.confidence == base_confidence
        else:
            # Slots not in update should remain unchanged
            assert slot.value == base_value
            assert slot.confidence == base_confidence


@given(
    session_slots=slots_dict_strategy,
    slot_confidence=confidence_strategy,
    anaphora_updates=st.dictionaries(
        st.sampled_from(["last_mentioned_order", "last_mentioned_item", "last_mentioned_time"]),
        st.text(min_size=1, max_size=50),
        min_size=1,
        max_size=3
    )
)
def test_anaphora_context_updates_preserve_slot_data(
    session_slots: Dict[str, Any],
    slot_confidence: float,
    anaphora_updates: Dict[str, str]
):
    """
    **Validates: Requirements 11.1, 11.2**
    
    Property 6e: Anaphora context updates preserve existing slot data.
    
    When anaphora context is updated for reference resolution,
    existing slot-value pairs should remain unchanged.
    """
    # Arrange
    tracker = DialogueStateTracker()
    session = tracker.create_session()
    
    # Set initial slots
    tracker.merge_slots(session.session_id, session_slots, slot_confidence)
    
    # Act - Update anaphora context
    tracker.update_anaphora_context(
        session.session_id,
        order_id=anaphora_updates.get("last_mentioned_order"),
        item=anaphora_updates.get("last_mentioned_item"),
        time=anaphora_updates.get("last_mentioned_time")
    )
    
    # Assert - Slots should be preserved
    updated_session = tracker.get_session(session.session_id)
    assert updated_session is not None
    
    for slot_name, expected_value in session_slots.items():
        slot = updated_session.get_slot(slot_name)
        assert slot is not None, f"Slot '{slot_name}' was lost during anaphora context update"
        assert slot.value == expected_value, \
            f"Slot '{slot_name}' value changed during anaphora context update"
        assert slot.confidence == slot_confidence, \
            f"Slot '{slot_name}' confidence changed during anaphora context update"


@given(
    initial_slots=slots_dict_strategy,
    slot_confidence=confidence_strategy,
    num_turns=st.integers(min_value=1, max_value=8)
)
def test_multi_turn_conversation_preserves_context_across_turns(
    initial_slots: Dict[str, Any],
    slot_confidence: float,
    num_turns: int
):
    """
    **Validates: Requirements 11.1, 11.2**
    
    Property 6f: Multi-turn conversations preserve context across all turns.
    
    Information should be preserved across multiple conversation turns,
    maintaining consistency throughout the dialogue.
    """
    # Arrange
    tracker = DialogueStateTracker()
    session = tracker.create_session()
    
    # Set initial context
    tracker.merge_slots(session.session_id, initial_slots, slot_confidence)
    
    # Act - Add multiple turns
    for turn_num in range(num_turns):
        tracker.update_session(
            session.session_id,
            f"User utterance {turn_num + 1}",
            f"System response {turn_num + 1}",
            {"turn": turn_num + 1},
            0.8
        )
    
    # Assert - Initial slots should still be preserved
    updated_session = tracker.get_session(session.session_id)
    assert updated_session is not None
    
    # Check slot preservation
    for slot_name, expected_value in initial_slots.items():
        slot = updated_session.get_slot(slot_name)
        assert slot is not None, f"Slot '{slot_name}' was lost after {num_turns} turns"
        assert slot.value == expected_value, \
            f"Slot '{slot_name}' value changed after {num_turns} turns"
    
    # Check conversation history
    assert len(updated_session.conversation_history) == num_turns
    assert updated_session.turn_count == num_turns
    
    # Verify turn ordering is preserved
    for i, turn in enumerate(updated_session.conversation_history):
        assert turn.turn == i + 1, f"Turn order not preserved: expected {i + 1}, got {turn.turn}"
        assert turn.user_utterance == f"User utterance {i + 1}"


@given(
    slots_batch1=slots_dict_strategy,
    confidence1=confidence_strategy,
    slots_batch2=slots_dict_strategy,
    confidence2=confidence_strategy,
    slots_batch3=slots_dict_strategy,
    confidence3=confidence_strategy
)
def test_incremental_information_merging_preserves_all_data(
    slots_batch1: Dict[str, Any],
    confidence1: float,
    slots_batch2: Dict[str, Any],
    confidence2: float,
    slots_batch3: Dict[str, Any],
    confidence3: float
):
    """
    **Validates: Requirements 11.1, 11.2**
    
    Property 6g: Incremental information merging preserves all accumulated data.
    
    When information is provided incrementally across multiple interactions,
    all previously provided information should be preserved.
    """
    # Arrange
    tracker = DialogueStateTracker()
    session = tracker.create_session()
    
    # Act - Add information incrementally
    tracker.merge_slots(session.session_id, slots_batch1, confidence1)
    tracker.merge_slots(session.session_id, slots_batch2, confidence2)
    tracker.merge_slots(session.session_id, slots_batch3, confidence3)
    
    # Assert - All information should be preserved (subject to confidence rules)
    updated_session = tracker.get_session(session.session_id)
    assert updated_session is not None
    
    # Collect all unique slot names
    all_slot_names = set(slots_batch1.keys()) | set(slots_batch2.keys()) | set(slots_batch3.keys())
    
    for slot_name in all_slot_names:
        slot = updated_session.get_slot(slot_name)
        assert slot is not None, f"Slot '{slot_name}' was lost during incremental merging"
        
        # Determine expected value based on confidence-based merging
        expected_value = None
        expected_confidence = 0.0
        
        # Check each batch in order, keeping highest confidence
        for batch, confidence in [(slots_batch1, confidence1), (slots_batch2, confidence2), (slots_batch3, confidence3)]:
            if slot_name in batch and confidence >= expected_confidence:
                expected_value = batch[slot_name]
                expected_confidence = confidence
        
        assert slot.value == expected_value, \
            f"Slot '{slot_name}' has incorrect value after incremental merging"
        assert slot.confidence == expected_confidence, \
            f"Slot '{slot_name}' has incorrect confidence after incremental merging"


@given(
    original_slots=slots_dict_strategy,
    original_confidence=confidence_strategy,
    partial_update=st.dictionaries(
        slot_name_strategy,
        slot_value_strategy,
        min_size=1,
        max_size=3
    ),
    update_confidence=confidence_strategy
)
def test_partial_updates_preserve_non_updated_slots(
    original_slots: Dict[str, Any],
    original_confidence: float,
    partial_update: Dict[str, Any],
    update_confidence: float
):
    """
    **Validates: Requirements 11.1, 11.2**
    
    Property 6h: Partial updates preserve non-updated slot information.
    
    When only some slots are updated, other slots should remain unchanged.
    """
    # Ensure partial update doesn't include all original slots
    assume(len(partial_update) < len(original_slots) or 
           not set(partial_update.keys()).issuperset(set(original_slots.keys())))
    
    # Arrange
    tracker = DialogueStateTracker()
    session = tracker.create_session()
    
    # Set original slots
    tracker.merge_slots(session.session_id, original_slots, original_confidence)
    
    # Act - Apply partial update
    tracker.merge_slots(session.session_id, partial_update, update_confidence)
    
    # Assert - Non-updated slots should be preserved
    updated_session = tracker.get_session(session.session_id)
    assert updated_session is not None
    
    non_updated_slots = {k: v for k, v in original_slots.items() if k not in partial_update}
    
    for slot_name, expected_value in non_updated_slots.items():
        slot = updated_session.get_slot(slot_name)
        assert slot is not None, f"Non-updated slot '{slot_name}' was lost"
        assert slot.value == expected_value, \
            f"Non-updated slot '{slot_name}' value changed unexpectedly"
        assert slot.confidence == original_confidence, \
            f"Non-updated slot '{slot_name}' confidence changed unexpectedly"


def test_empty_slot_updates_preserve_existing_data():
    """
    **Validates: Requirements 11.1, 11.2**
    
    Property 6i: Empty slot updates preserve all existing data.
    
    When an empty update is applied, all existing slot data should be preserved.
    """
    # Arrange
    tracker = DialogueStateTracker()
    session = tracker.create_session()
    
    original_slots = {
        "order_id": "ORD-123",
        "items": ["pizza", "coke"],
        "delivery_time": "18:30"
    }
    
    tracker.merge_slots(session.session_id, original_slots, 0.9)
    
    # Act - Apply empty update
    tracker.merge_slots(session.session_id, {}, 0.8)
    
    # Assert - All original data should be preserved
    updated_session = tracker.get_session(session.session_id)
    assert updated_session is not None
    
    for slot_name, expected_value in original_slots.items():
        slot = updated_session.get_slot(slot_name)
        assert slot is not None, f"Slot '{slot_name}' was lost after empty update"
        assert slot.value == expected_value, \
            f"Slot '{slot_name}' value changed after empty update"
        assert slot.confidence == 0.9, \
            f"Slot '{slot_name}' confidence changed after empty update"


@given(
    initial_slots=slots_dict_strategy,
    slot_confidence=confidence_strategy,
    context_summary_trigger=st.booleans()
)
def test_context_summarization_preserves_slot_data(
    initial_slots: Dict[str, Any],
    slot_confidence: float,
    context_summary_trigger: bool
):
    """
    **Validates: Requirements 11.1, 11.2**
    
    Property 6j: Context summarization preserves slot data.
    
    When conversation history is summarized (due to token limits),
    slot-value pairs should be preserved.
    """
    # Arrange - Use higher turn limit to avoid expiration during test
    tracker = DialogueStateTracker(max_tokens=100, max_turns=20)  # Low token limit, high turn limit
    session = tracker.create_session()
    
    # Set initial slots
    tracker.merge_slots(session.session_id, initial_slots, slot_confidence)
    
    # Act - Add many turns to trigger summarization
    if context_summary_trigger:
        for i in range(5):  # Reduced to avoid turn-based expiration
            long_utterance = "This is a very long user utterance that contains many words " * 10
            long_response = "This is a very long system response that contains many words " * 10
            tracker.update_session(
                session.session_id,
                long_utterance,
                long_response,
                {"turn": i},
                0.8
            )
    
    # Assert - Slots should be preserved even after summarization
    updated_session = tracker.get_session(session.session_id)
    assert updated_session is not None
    
    for slot_name, expected_value in initial_slots.items():
        slot = updated_session.get_slot(slot_name)
        assert slot is not None, f"Slot '{slot_name}' was lost during context summarization"
        assert slot.value == expected_value, \
            f"Slot '{slot_name}' value changed during context summarization"
        assert slot.confidence == slot_confidence, \
            f"Slot '{slot_name}' confidence changed during context summarization"


@pytest.mark.parametrize("merge_order", [
    [("high", 0.9), ("low", 0.3)],
    [("low", 0.3), ("high", 0.9)],
    [("medium", 0.6), ("high", 0.9), ("low", 0.3)],
])
def test_confidence_based_merging_order_independence(merge_order):
    """
    **Validates: Requirements 11.1, 11.2**
    
    Property 6k: Confidence-based merging produces consistent results regardless of order.
    
    The final slot values should depend only on confidence levels, not the order
    in which updates are applied.
    """
    # Arrange
    tracker = DialogueStateTracker()
    session = tracker.create_session()
    
    slot_name = "test_slot"
    
    # Act - Apply updates in the given order
    for value, confidence in merge_order:
        tracker.merge_slots(session.session_id, {slot_name: value}, confidence)
    
    # Assert - Final value should be the one with highest confidence
    updated_session = tracker.get_session(session.session_id)
    assert updated_session is not None
    
    slot = updated_session.get_slot(slot_name)
    assert slot is not None
    
    # Find expected value (highest confidence)
    expected_value, expected_confidence = max(merge_order, key=lambda x: x[1])
    
    assert slot.value == expected_value, \
        f"Final value should be '{expected_value}' (highest confidence {expected_confidence})"
    assert slot.confidence == expected_confidence


def test_session_expiration_preserves_data_until_expiry():
    """
    **Validates: Requirements 11.1, 11.2**
    
    Property 6l: Session data is preserved until expiration.
    
    Slot data should be accessible until the session expires,
    and should not be lost prematurely.
    """
    # Arrange
    tracker = DialogueStateTracker(max_turns=3, max_duration_minutes=1)
    session = tracker.create_session()
    
    test_slots = {
        "order_id": "ORD-TEST",
        "customer_name": "Test Customer"
    }
    
    tracker.merge_slots(session.session_id, test_slots, 0.9)
    
    # Act & Assert - Data should be preserved before expiration
    for turn in range(2):  # Stay under max_turns
        tracker.update_session(
            session.session_id,
            f"Turn {turn + 1}",
            f"Response {turn + 1}",
            confidence=0.8
        )
        
        # Verify data is still there
        current_session = tracker.get_session(session.session_id)
        assert current_session is not None, f"Session expired prematurely at turn {turn + 1}"
        
        for slot_name, expected_value in test_slots.items():
            slot = current_session.get_slot(slot_name)
            assert slot is not None, f"Slot '{slot_name}' lost prematurely at turn {turn + 1}"
            assert slot.value == expected_value


def test_concurrent_slot_updates_maintain_consistency():
    """
    **Validates: Requirements 11.1, 11.2**
    
    Property 6m: Concurrent slot updates maintain data consistency.
    
    When multiple slot updates occur in sequence, the final state
    should be consistent and predictable.
    """
    # Arrange
    tracker = DialogueStateTracker()
    session = tracker.create_session()
    
    # Act - Apply multiple updates to same and different slots
    updates = [
        ({"slot_a": "value1", "slot_b": "value1"}, 0.5),
        ({"slot_a": "value2"}, 0.8),  # Higher confidence, should update slot_a
        ({"slot_b": "value2"}, 0.3),  # Lower confidence, should not update slot_b
        ({"slot_c": "value1"}, 0.7),  # New slot
    ]
    
    for slots, confidence in updates:
        tracker.merge_slots(session.session_id, slots, confidence)
    
    # Assert - Final state should be consistent
    updated_session = tracker.get_session(session.session_id)
    assert updated_session is not None
    
    # slot_a should have value2 (higher confidence 0.8)
    slot_a = updated_session.get_slot("slot_a")
    assert slot_a is not None
    assert slot_a.value == "value2"
    assert slot_a.confidence == 0.8
    
    # slot_b should have value1 (original higher confidence 0.5 > 0.3)
    slot_b = updated_session.get_slot("slot_b")
    assert slot_b is not None
    assert slot_b.value == "value1"
    assert slot_b.confidence == 0.5
    
    # slot_c should have value1 (only value)
    slot_c = updated_session.get_slot("slot_c")
    assert slot_c is not None
    assert slot_c.value == "value1"
    assert slot_c.confidence == 0.7