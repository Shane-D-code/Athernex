"""
Property-based tests for round-trip consistency.

Tests Property 4: Round-trip consistency
Validates Requirements 12.1, 4.1

These tests verify that:
1. Serializing StructuredOrderData to JSON then deserializing produces equivalent data
2. All fields are preserved through the round-trip
3. Various order configurations maintain data integrity
"""

import json
import pytest
from hypothesis import given, strategies as st
from typing import List, Optional
from dataclasses import asdict

from llm.base import StructuredOrderData, Intent, OrderItem


# Strategy for generating valid intents
intent_strategy = st.sampled_from(list(Intent))

# Strategy for generating order items
order_item_strategy = st.builds(
    OrderItem,
    name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'P'))),
    quantity=st.integers(min_value=1, max_value=100),
    unit=st.one_of(st.none(), st.sampled_from(["kg", "g", "L", "ml", "piece", "dozen", "box"])),
    special_instructions=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)

# Strategy for generating lists of order items
items_list_strategy = st.lists(order_item_strategy, min_size=0, max_size=10)

# Strategy for generating ISO 8601 timestamps
from datetime import datetime, timezone

timestamp_strategy = st.one_of(
    st.none(),
    st.datetimes().map(lambda dt: dt.isoformat())
)

# Strategy for generating confidence scores
confidence_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# Strategy for generating missing fields
missing_fields_strategy = st.lists(
    st.sampled_from(["items", "delivery_time", "order_id", "special_instructions"]),
    min_size=0,
    max_size=4,
    unique=True
)

# Strategy for generating order IDs
order_id_strategy = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))
)

# Strategy for generating special instructions
special_instructions_strategy = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=200)
)


@given(
    intent=intent_strategy,
    items=items_list_strategy,
    delivery_time=timestamp_strategy,
    special_instructions=special_instructions_strategy,
    order_id=order_id_strategy,
    confidence=confidence_strategy,
    missing_fields=missing_fields_strategy
)
def test_structured_order_data_round_trip_preserves_all_fields(
    intent: Intent,
    items: List[OrderItem],
    delivery_time: Optional[str],
    special_instructions: Optional[str],
    order_id: Optional[str],
    confidence: float,
    missing_fields: List[str]
):
    """
    **Validates: Requirements 12.1, 4.1**
    
    Property 4a: Serializing StructuredOrderData to JSON then deserializing
    produces equivalent data.
    
    This is a critical data integrity property ensuring no information is lost
    during serialization/deserialization cycles.
    """
    # Arrange - Create original StructuredOrderData
    original = StructuredOrderData(
        intent=intent,
        items=items,
        delivery_time=delivery_time,
        special_instructions=special_instructions,
        order_id=order_id,
        confidence=confidence,
        missing_fields=missing_fields
    )
    
    # Act - Serialize to JSON
    json_str = json.dumps(asdict(original), default=str)
    
    # Deserialize back from JSON
    data_dict = json.loads(json_str)
    
    # Reconstruct StructuredOrderData
    reconstructed_items = [
        OrderItem(**item_dict) for item_dict in data_dict.get("items", [])
    ]
    
    reconstructed = StructuredOrderData(
        intent=Intent(data_dict["intent"]),
        items=reconstructed_items,
        delivery_time=data_dict.get("delivery_time"),
        special_instructions=data_dict.get("special_instructions"),
        order_id=data_dict.get("order_id"),
        confidence=data_dict.get("confidence", 0.0),
        missing_fields=data_dict.get("missing_fields", [])
    )
    
    # Assert - All fields should be equivalent
    assert reconstructed.intent == original.intent, \
        f"Intent mismatch: {reconstructed.intent} != {original.intent}"
    
    assert reconstructed.confidence == original.confidence, \
        f"Confidence mismatch: {reconstructed.confidence} != {original.confidence}"
    
    assert reconstructed.delivery_time == original.delivery_time, \
        f"Delivery time mismatch: {reconstructed.delivery_time} != {original.delivery_time}"
    
    assert reconstructed.special_instructions == original.special_instructions, \
        f"Special instructions mismatch"
    
    assert reconstructed.order_id == original.order_id, \
        f"Order ID mismatch: {reconstructed.order_id} != {original.order_id}"
    
    assert reconstructed.missing_fields == original.missing_fields, \
        f"Missing fields mismatch: {reconstructed.missing_fields} != {original.missing_fields}"
    
    # Verify items list
    assert len(reconstructed.items) == len(original.items), \
        f"Items count mismatch: {len(reconstructed.items)} != {len(original.items)}"
    
    for i, (rec_item, orig_item) in enumerate(zip(reconstructed.items, original.items)):
        assert rec_item.name == orig_item.name, \
            f"Item {i} name mismatch: {rec_item.name} != {orig_item.name}"
        assert rec_item.quantity == orig_item.quantity, \
            f"Item {i} quantity mismatch: {rec_item.quantity} != {orig_item.quantity}"
        assert rec_item.unit == orig_item.unit, \
            f"Item {i} unit mismatch: {rec_item.unit} != {orig_item.unit}"
        assert rec_item.special_instructions == orig_item.special_instructions, \
            f"Item {i} special instructions mismatch"


@given(intent=intent_strategy)
def test_minimal_structured_order_data_round_trip(intent: Intent):
    """
    **Validates: Requirements 12.1, 4.1**
    
    Property 4b: Minimal StructuredOrderData (only required fields) round-trips correctly.
    
    Tests the simplest case with only intent and default values.
    """
    # Arrange
    original = StructuredOrderData(intent=intent)
    
    # Act
    json_str = json.dumps(asdict(original), default=str)
    data_dict = json.loads(json_str)
    
    reconstructed = StructuredOrderData(
        intent=Intent(data_dict["intent"]),
        items=[OrderItem(**item) for item in data_dict.get("items", [])],
        delivery_time=data_dict.get("delivery_time"),
        special_instructions=data_dict.get("special_instructions"),
        order_id=data_dict.get("order_id"),
        confidence=data_dict.get("confidence", 0.0),
        missing_fields=data_dict.get("missing_fields", [])
    )
    
    # Assert
    assert reconstructed.intent == original.intent
    assert reconstructed.items == original.items == []
    assert reconstructed.delivery_time == original.delivery_time is None
    assert reconstructed.special_instructions == original.special_instructions is None
    assert reconstructed.order_id == original.order_id is None
    assert reconstructed.confidence == original.confidence == 0.0
    assert reconstructed.missing_fields == original.missing_fields == []


@given(items=items_list_strategy)
def test_order_items_round_trip_preserves_order(items: List[OrderItem]):
    """
    **Validates: Requirements 12.1, 4.1**
    
    Property 4c: Order items list preserves order and all item details.
    
    Verifies that the order of items in the list is maintained and all
    item properties are preserved.
    """
    # Arrange
    original = StructuredOrderData(
        intent=Intent.PLACE_ORDER,
        items=items
    )
    
    # Act
    json_str = json.dumps(asdict(original), default=str)
    data_dict = json.loads(json_str)
    
    reconstructed_items = [
        OrderItem(**item_dict) for item_dict in data_dict.get("items", [])
    ]
    
    # Assert - Order and content preserved
    assert len(reconstructed_items) == len(items)
    
    for i, (rec_item, orig_item) in enumerate(zip(reconstructed_items, items)):
        assert rec_item.name == orig_item.name, f"Item {i} name not preserved"
        assert rec_item.quantity == orig_item.quantity, f"Item {i} quantity not preserved"
        assert rec_item.unit == orig_item.unit, f"Item {i} unit not preserved"
        assert rec_item.special_instructions == orig_item.special_instructions, \
            f"Item {i} special instructions not preserved"


@given(
    intent=intent_strategy,
    confidence=confidence_strategy
)
def test_confidence_score_precision_preserved(intent: Intent, confidence: float):
    """
    **Validates: Requirements 12.1, 4.1**
    
    Property 4d: Confidence scores maintain precision through round-trip.
    
    Verifies that floating-point confidence values are preserved with
    acceptable precision (within floating-point tolerance).
    """
    # Arrange
    original = StructuredOrderData(
        intent=intent,
        confidence=confidence
    )
    
    # Act
    json_str = json.dumps(asdict(original), default=str)
    data_dict = json.loads(json_str)
    
    reconstructed = StructuredOrderData(
        intent=Intent(data_dict["intent"]),
        items=[],
        confidence=data_dict.get("confidence", 0.0)
    )
    
    # Assert - Confidence preserved within floating-point tolerance
    assert abs(reconstructed.confidence - original.confidence) < 1e-10, \
        f"Confidence precision lost: {reconstructed.confidence} != {original.confidence}"


@given(missing_fields=missing_fields_strategy)
def test_missing_fields_list_preserved(missing_fields: List[str]):
    """
    **Validates: Requirements 12.1, 4.1**
    
    Property 4e: Missing fields list is preserved through round-trip.
    
    Verifies that the list of missing fields (used for clarification)
    is correctly preserved.
    """
    # Arrange
    original = StructuredOrderData(
        intent=Intent.PLACE_ORDER,
        missing_fields=missing_fields
    )
    
    # Act
    json_str = json.dumps(asdict(original), default=str)
    data_dict = json.loads(json_str)
    
    reconstructed = StructuredOrderData(
        intent=Intent(data_dict["intent"]),
        items=[],
        missing_fields=data_dict.get("missing_fields", [])
    )
    
    # Assert
    assert reconstructed.missing_fields == original.missing_fields, \
        f"Missing fields not preserved: {reconstructed.missing_fields} != {original.missing_fields}"


def test_all_intents_serialize_correctly():
    """
    **Validates: Requirements 12.1, 4.1**
    
    Property 4f: All intent types serialize and deserialize correctly.
    
    Verifies that every supported intent can be serialized and deserialized.
    """
    for intent in Intent:
        # Arrange
        original = StructuredOrderData(intent=intent)
        
        # Act
        json_str = json.dumps(asdict(original), default=str)
        data_dict = json.loads(json_str)
        
        reconstructed = StructuredOrderData(
            intent=Intent(data_dict["intent"]),
            items=[]
        )
        
        # Assert
        assert reconstructed.intent == original.intent, \
            f"Intent {intent} not preserved through round-trip"


@given(
    intent=intent_strategy,
    items=items_list_strategy,
    delivery_time=timestamp_strategy,
    special_instructions=special_instructions_strategy,
    order_id=order_id_strategy,
    confidence=confidence_strategy,
    missing_fields=missing_fields_strategy
)
def test_multiple_round_trips_are_idempotent(
    intent: Intent,
    items: List[OrderItem],
    delivery_time: Optional[str],
    special_instructions: Optional[str],
    order_id: Optional[str],
    confidence: float,
    missing_fields: List[str]
):
    """
    **Validates: Requirements 12.1, 4.1**
    
    Property 4g: Multiple round-trips produce identical results (idempotence).
    
    Verifies that serializing and deserializing multiple times doesn't
    introduce any data drift or corruption.
    """
    # Arrange
    original = StructuredOrderData(
        intent=intent,
        items=items,
        delivery_time=delivery_time,
        special_instructions=special_instructions,
        order_id=order_id,
        confidence=confidence,
        missing_fields=missing_fields
    )
    
    # Act - Perform 3 round-trips
    current = original
    for i in range(3):
        json_str = json.dumps(asdict(current), default=str)
        data_dict = json.loads(json_str)
        
        reconstructed_items = [
            OrderItem(**item_dict) for item_dict in data_dict.get("items", [])
        ]
        
        current = StructuredOrderData(
            intent=Intent(data_dict["intent"]),
            items=reconstructed_items,
            delivery_time=data_dict.get("delivery_time"),
            special_instructions=data_dict.get("special_instructions"),
            order_id=data_dict.get("order_id"),
            confidence=data_dict.get("confidence", 0.0),
            missing_fields=data_dict.get("missing_fields", [])
        )
    
    # Assert - Final result equals original
    assert current.intent == original.intent
    assert current.confidence == original.confidence
    assert current.delivery_time == original.delivery_time
    assert current.special_instructions == original.special_instructions
    assert current.order_id == original.order_id
    assert current.missing_fields == original.missing_fields
    assert len(current.items) == len(original.items)
    
    for rec_item, orig_item in zip(current.items, original.items):
        assert rec_item.name == orig_item.name
        assert rec_item.quantity == orig_item.quantity
        assert rec_item.unit == orig_item.unit
        assert rec_item.special_instructions == orig_item.special_instructions


@given(
    name=st.text(min_size=1, max_size=100),
    quantity=st.integers(min_value=1, max_value=1000),
    unit=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    special_instructions=st.one_of(st.none(), st.text(min_size=0, max_size=200))
)
def test_order_item_round_trip(
    name: str,
    quantity: int,
    unit: Optional[str],
    special_instructions: Optional[str]
):
    """
    **Validates: Requirements 12.1, 4.1**
    
    Property 4h: Individual OrderItem objects round-trip correctly.
    
    Tests that OrderItem (a component of StructuredOrderData) maintains
    data integrity through serialization.
    """
    # Arrange
    original_item = OrderItem(
        name=name,
        quantity=quantity,
        unit=unit,
        special_instructions=special_instructions
    )
    
    # Act
    item_dict = asdict(original_item)
    json_str = json.dumps(item_dict, default=str)
    reconstructed_dict = json.loads(json_str)
    reconstructed_item = OrderItem(**reconstructed_dict)
    
    # Assert
    assert reconstructed_item.name == original_item.name
    assert reconstructed_item.quantity == original_item.quantity
    assert reconstructed_item.unit == original_item.unit
    assert reconstructed_item.special_instructions == original_item.special_instructions


def test_empty_items_list_round_trip():
    """
    **Validates: Requirements 12.1, 4.1**
    
    Property 4i: Empty items list is preserved (not converted to None).
    
    Verifies that an empty list remains an empty list, not None or missing.
    """
    # Arrange
    original = StructuredOrderData(
        intent=Intent.CHECK_STATUS,
        items=[]
    )
    
    # Act
    json_str = json.dumps(asdict(original), default=str)
    data_dict = json.loads(json_str)
    
    reconstructed = StructuredOrderData(
        intent=Intent(data_dict["intent"]),
        items=[OrderItem(**item) for item in data_dict.get("items", [])]
    )
    
    # Assert
    assert reconstructed.items == []
    assert isinstance(reconstructed.items, list)


@pytest.mark.parametrize("intent,order_id", [
    (Intent.MODIFY_ORDER, "ORD-12345"),
    (Intent.CANCEL_ORDER, "ORD-67890"),
    (Intent.CHECK_STATUS, "ORD-ABCDE"),
    (Intent.CONFIRM_ORDER, "ORD-XYZ123"),
])
def test_order_id_preserved_for_order_operations(intent: Intent, order_id: str):
    """
    **Validates: Requirements 12.1, 4.1**
    
    Property 4j: Order IDs are preserved for modify/cancel/check operations.
    
    Verifies that order IDs (critical for order management operations)
    are correctly preserved through serialization.
    """
    # Arrange
    original = StructuredOrderData(
        intent=intent,
        order_id=order_id
    )
    
    # Act
    json_str = json.dumps(asdict(original), default=str)
    data_dict = json.loads(json_str)
    
    reconstructed = StructuredOrderData(
        intent=Intent(data_dict["intent"]),
        items=[],
        order_id=data_dict.get("order_id")
    )
    
    # Assert
    assert reconstructed.order_id == original.order_id == order_id, \
        f"Order ID not preserved for {intent}"


def test_json_serialization_produces_valid_json():
    """
    **Validates: Requirements 12.1, 4.1**
    
    Property 4k: Serialization produces valid, parseable JSON.
    
    Verifies that the JSON output is well-formed and can be parsed
    by standard JSON parsers.
    """
    # Arrange
    original = StructuredOrderData(
        intent=Intent.PLACE_ORDER,
        items=[
            OrderItem(name="Pizza", quantity=2, unit="piece"),
            OrderItem(name="Coke", quantity=1, unit="L")
        ],
        delivery_time="2024-01-15T18:30:00",
        special_instructions="Ring doorbell twice",
        confidence=0.95,
        missing_fields=[]
    )
    
    # Act
    json_str = json.dumps(asdict(original), default=str)
    
    # Assert - Should not raise exception
    try:
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert "intent" in parsed
        assert "items" in parsed
        assert "confidence" in parsed
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON produced: {e}")


@given(
    intent=intent_strategy,
    items=items_list_strategy
)
def test_schema_consistency_across_serialization(
    intent: Intent,
    items: List[OrderItem]
):
    """
    **Validates: Requirements 12.1, 4.1**
    
    Property 4l: Serialized JSON maintains consistent schema structure.
    
    Verifies that the JSON schema is consistent (same keys present)
    regardless of the data values.
    """
    # Arrange
    original = StructuredOrderData(
        intent=intent,
        items=items
    )
    
    # Act
    json_str = json.dumps(asdict(original), default=str)
    data_dict = json.loads(json_str)
    
    # Assert - Required keys are present
    required_keys = {"intent", "items", "confidence", "missing_fields"}
    assert required_keys.issubset(data_dict.keys()), \
        f"Missing required keys in serialized JSON: {required_keys - data_dict.keys()}"
    
    # Optional keys may or may not be present
    optional_keys = {"delivery_time", "special_instructions", "order_id"}
    all_keys = data_dict.keys()
    
    # All keys should be either required or optional
    unexpected_keys = set(all_keys) - required_keys - optional_keys
    assert len(unexpected_keys) == 0, \
        f"Unexpected keys in serialized JSON: {unexpected_keys}"
