"""
Property-based tests for semantic equivalence.

Tests Property 5: Semantic equivalence
Validates Requirements 12.5, 2.3

These tests verify that:
1. Different phrasings of the same order produce equivalent StructuredOrderData
2. Paraphrased utterances extract the same intent and items
3. Order of words doesn't affect extracted data (within reason)
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from typing import List, Tuple

from llm.base import StructuredOrderData, Intent, OrderItem


# Strategy for generating order items
def order_item_strategy():
    """Generate valid order items."""
    return st.builds(
        OrderItem,
        name=st.sampled_from([
            "pizza", "burger", "dosa", "biryani", "coffee", "tea",
            "samosa", "pasta", "sandwich", "salad"
        ]),
        quantity=st.integers(min_value=1, max_value=10),
        unit=st.sampled_from([None, "pieces", "kg", "liters"]),
        special_instructions=st.one_of(st.none(), st.just("extra cheese"), st.just("no onions"))
    )


# Strategy for generating structured order data
def structured_order_data_strategy():
    """Generate valid StructuredOrderData."""
    return st.builds(
        StructuredOrderData,
        intent=st.sampled_from([Intent.PLACE_ORDER, Intent.MODIFY_ORDER, Intent.CANCEL_ORDER]),
        items=st.lists(order_item_strategy(), min_size=1, max_size=5),
        delivery_time=st.one_of(st.none(), st.just("2024-01-15T19:00:00Z")),
        special_instructions=st.one_of(st.none(), st.just("ring doorbell")),
        order_id=st.one_of(st.none(), st.just("ORD-123")),
        confidence=st.floats(min_value=0.0, max_value=1.0),
        missing_fields=st.lists(st.text(min_size=1, max_size=20), max_size=3)
    )


def normalize_order_data(data: StructuredOrderData) -> dict:
    """
    Normalize StructuredOrderData for comparison.
    
    Extracts the essential semantic content, ignoring:
    - Confidence scores (may vary slightly)
    - Missing fields (may differ in phrasing detection)
    - Exact timestamp format (as long as time is equivalent)
    """
    return {
        "intent": data.intent.value,
        "items": sorted([
            {
                "name": item.name.lower().strip(),
                "quantity": item.quantity,
                "unit": item.unit if item.unit else "",  # Normalize None to empty string
            }
            for item in data.items
        ], key=lambda x: (x["name"], x["quantity"], x["unit"])),
        "has_delivery_time": data.delivery_time is not None,
        "has_special_instructions": data.special_instructions is not None,
        "has_order_id": data.order_id is not None,
    }


def are_semantically_equivalent(data1: StructuredOrderData, data2: StructuredOrderData) -> bool:
    """
    Check if two StructuredOrderData objects are semantically equivalent.
    
    Semantic equivalence means:
    - Same intent
    - Same items (name, quantity, unit) regardless of order
    - Same presence/absence of delivery time, special instructions, order_id
    """
    norm1 = normalize_order_data(data1)
    norm2 = normalize_order_data(data2)
    
    return norm1 == norm2


@given(data=structured_order_data_strategy())
def test_identity_is_semantically_equivalent(data: StructuredOrderData):
    """
    Property 5a: Identity - An order is semantically equivalent to itself.
    
    This is the reflexive property of semantic equivalence.
    """
    assert are_semantically_equivalent(data, data), \
        "Order should be semantically equivalent to itself"


@given(
    data1=structured_order_data_strategy(),
    data2=structured_order_data_strategy()
)
def test_semantic_equivalence_is_symmetric(
    data1: StructuredOrderData,
    data2: StructuredOrderData
):
    """
    Property 5b: Symmetry - If A is equivalent to B, then B is equivalent to A.
    
    This is the symmetric property of semantic equivalence.
    """
    if are_semantically_equivalent(data1, data2):
        assert are_semantically_equivalent(data2, data1), \
            "Semantic equivalence should be symmetric"


@given(data=structured_order_data_strategy())
def test_reordered_items_are_semantically_equivalent(data: StructuredOrderData):
    """
    Property 5c: Item order invariance.
    
    Validates that the order of items in the list doesn't affect
    semantic equivalence (e.g., "pizza and burger" vs "burger and pizza").
    """
    if len(data.items) < 2:
        return  # Skip if only one item
    
    # Create a copy with reversed item order
    data_reversed = StructuredOrderData(
        intent=data.intent,
        items=list(reversed(data.items)),
        delivery_time=data.delivery_time,
        special_instructions=data.special_instructions,
        order_id=data.order_id,
        confidence=data.confidence,
        missing_fields=data.missing_fields,
    )
    
    assert are_semantically_equivalent(data, data_reversed), \
        "Orders with reordered items should be semantically equivalent"


@given(data=structured_order_data_strategy())
def test_confidence_variation_preserves_semantic_equivalence(data: StructuredOrderData):
    """
    Property 5d: Confidence invariance.
    
    Validates that different confidence scores don't affect semantic equivalence.
    The semantic content is the same regardless of how confident the system is.
    """
    # Create copies with different confidence scores
    data_low_conf = StructuredOrderData(
        intent=data.intent,
        items=data.items,
        delivery_time=data.delivery_time,
        special_instructions=data.special_instructions,
        order_id=data.order_id,
        confidence=0.3,
        missing_fields=data.missing_fields,
    )
    
    data_high_conf = StructuredOrderData(
        intent=data.intent,
        items=data.items,
        delivery_time=data.delivery_time,
        special_instructions=data.special_instructions,
        order_id=data.order_id,
        confidence=0.9,
        missing_fields=data.missing_fields,
    )
    
    assert are_semantically_equivalent(data_low_conf, data_high_conf), \
        "Orders with different confidence should be semantically equivalent"


@given(data=structured_order_data_strategy())
def test_case_insensitive_item_names(data: StructuredOrderData):
    """
    Property 5e: Case insensitivity.
    
    Validates that item names are compared case-insensitively
    (e.g., "Pizza" vs "pizza" vs "PIZZA").
    """
    # Create a copy with different case for item names
    items_different_case = [
        OrderItem(
            name=item.name.upper() if i % 2 == 0 else item.name.lower(),
            quantity=item.quantity,
            unit=item.unit,
            special_instructions=item.special_instructions,
        )
        for i, item in enumerate(data.items)
    ]
    
    data_different_case = StructuredOrderData(
        intent=data.intent,
        items=items_different_case,
        delivery_time=data.delivery_time,
        special_instructions=data.special_instructions,
        order_id=data.order_id,
        confidence=data.confidence,
        missing_fields=data.missing_fields,
    )
    
    assert are_semantically_equivalent(data, data_different_case), \
        "Orders with different case item names should be semantically equivalent"


# Integration tests with actual paraphrased utterances
# These would require an actual LLM to run, so they're marked as integration tests

@pytest.mark.integration
@pytest.mark.asyncio
class TestSemanticEquivalenceIntegration:
    """
    Integration tests for semantic equivalence with actual LLM processing.
    
    These tests require a running Ollama instance and are slower.
    Run with: pytest -m integration
    """
    
    # Paraphrased utterance pairs that should produce equivalent orders
    PARAPHRASE_PAIRS = [
        # English variations
        (
            "I want to order 2 pizzas for delivery at 7pm",
            "Can I get 2 pizzas delivered at 7 in the evening?"
        ),
        (
            "Order 3 burgers and 2 cokes",
            "I'd like 3 burgers and 2 cokes please"
        ),
        # Hindi variations
        (
            "मुझे 2 डोसा चाहिए",
            "2 डोसा ऑर्डर करना है"
        ),
        # Code-mixed variations
        (
            "2 pizza order karna hai",
            "I want to order 2 pizzas"
        ),
        # Different word order
        (
            "Deliver 1 biryani at 6pm",
            "At 6pm, deliver 1 biryani"
        ),
    ]
    
    @pytest.mark.parametrize("utterance1,utterance2", PARAPHRASE_PAIRS)
    async def test_paraphrased_utterances_produce_equivalent_orders(
        self,
        utterance1: str,
        utterance2: str
    ):
        """
        Property 5f: Paraphrase equivalence (integration test).
        
        Validates that paraphrased utterances produce semantically
        equivalent StructuredOrderData.
        
        Requires: Running Ollama instance
        """
        from llm.ollama_processor import OllamaLLMProcessor
        
        processor = OllamaLLMProcessor()
        
        # Check if Ollama is available
        if not await processor.health_check():
            pytest.skip("Ollama not available")
        
        try:
            # Process both utterances
            response1 = await processor.process_utterance(utterance1)
            response2 = await processor.process_utterance(utterance2)
            
            # Check semantic equivalence
            assert are_semantically_equivalent(
                response1.structured_data,
                response2.structured_data
            ), f"Paraphrased utterances should produce equivalent orders:\n" \
               f"  '{utterance1}' -> {normalize_order_data(response1.structured_data)}\n" \
               f"  '{utterance2}' -> {normalize_order_data(response2.structured_data)}"
        
        finally:
            await processor.close()
    
    @pytest.mark.parametrize("base_utterance,variations", [
        (
            "Order 2 pizzas",
            [
                "I want 2 pizzas",
                "Can I get 2 pizzas?",
                "2 pizzas please",
                "I'd like to order 2 pizzas",
            ]
        ),
    ])
    async def test_multiple_variations_produce_equivalent_orders(
        self,
        base_utterance: str,
        variations: List[str]
    ):
        """
        Property 5g: Multiple variation equivalence (integration test).
        
        Validates that multiple variations of the same order all produce
        semantically equivalent results.
        """
        from llm.ollama_processor import OllamaLLMProcessor
        
        processor = OllamaLLMProcessor()
        
        if not await processor.health_check():
            pytest.skip("Ollama not available")
        
        try:
            # Process base utterance
            base_response = await processor.process_utterance(base_utterance)
            base_data = base_response.structured_data
            
            # Process all variations
            for variation in variations:
                var_response = await processor.process_utterance(variation)
                var_data = var_response.structured_data
                
                assert are_semantically_equivalent(base_data, var_data), \
                    f"Variation should be equivalent to base:\n" \
                    f"  Base: '{base_utterance}' -> {normalize_order_data(base_data)}\n" \
                    f"  Variation: '{variation}' -> {normalize_order_data(var_data)}"
        
        finally:
            await processor.close()


# Unit tests for the normalization function itself

def test_normalize_order_data_handles_empty_items():
    """Test that normalization handles orders with no items."""
    data = StructuredOrderData(
        intent=Intent.CHECK_STATUS,
        items=[],
        order_id="ORD-123",
        confidence=0.8,
        missing_fields=[],
    )
    
    normalized = normalize_order_data(data)
    assert normalized["items"] == []
    assert normalized["intent"] == "check_status"


def test_normalize_order_data_sorts_items():
    """Test that normalization sorts items consistently."""
    data = StructuredOrderData(
        intent=Intent.PLACE_ORDER,
        items=[
            OrderItem(name="Burger", quantity=2),
            OrderItem(name="Pizza", quantity=1),
            OrderItem(name="Burger", quantity=1),
        ],
        confidence=0.9,
        missing_fields=[],
    )
    
    normalized = normalize_order_data(data)
    
    # Items should be sorted by name, then quantity
    assert normalized["items"][0]["name"] == "burger"
    assert normalized["items"][0]["quantity"] == 1
    assert normalized["items"][1]["name"] == "burger"
    assert normalized["items"][1]["quantity"] == 2
    assert normalized["items"][2]["name"] == "pizza"


def test_are_semantically_equivalent_with_different_intents():
    """Test that orders with different intents are not equivalent."""
    data1 = StructuredOrderData(
        intent=Intent.PLACE_ORDER,
        items=[OrderItem(name="pizza", quantity=2)],
        confidence=0.9,
        missing_fields=[],
    )
    
    data2 = StructuredOrderData(
        intent=Intent.MODIFY_ORDER,
        items=[OrderItem(name="pizza", quantity=2)],
        confidence=0.9,
        missing_fields=[],
    )
    
    assert not are_semantically_equivalent(data1, data2), \
        "Orders with different intents should not be equivalent"


def test_are_semantically_equivalent_with_different_quantities():
    """Test that orders with different quantities are not equivalent."""
    data1 = StructuredOrderData(
        intent=Intent.PLACE_ORDER,
        items=[OrderItem(name="pizza", quantity=2)],
        confidence=0.9,
        missing_fields=[],
    )
    
    data2 = StructuredOrderData(
        intent=Intent.PLACE_ORDER,
        items=[OrderItem(name="pizza", quantity=3)],
        confidence=0.9,
        missing_fields=[],
    )
    
    assert not are_semantically_equivalent(data1, data2), \
        "Orders with different quantities should not be equivalent"
