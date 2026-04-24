"""
Unit tests for anaphora resolution functionality.
"""

import pytest
from unittest.mock import Mock

from src.dialogue.anaphora_resolver import AnaphoraResolver, AnaphoricExpression
from src.dialogue.state import AnaphoraContext


class TestAnaphoraResolver:
    """Test cases for the AnaphoraResolver class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.resolver = AnaphoraResolver()
        self.context = AnaphoraContext(
            last_mentioned_order="ORD123",
            last_mentioned_item="pizza",
            last_mentioned_time="2:30 PM",
            last_mentioned_quantity=2,
            last_mentioned_location="123 Main St"
        )
    
    def test_detect_anaphora_order_references(self):
        """Test detection of order anaphoric references."""
        utterance = "I want to cancel that order"
        anaphora_found = self.resolver.detect_anaphora(utterance)
        
        assert len(anaphora_found) == 1
        assert anaphora_found[0].expression == "that order"
        assert anaphora_found[0].type == "order"
        assert anaphora_found[0].position == 17
    
    def test_detect_anaphora_item_references(self):
        """Test detection of item anaphoric references."""
        utterance = "I want more of that"
        anaphora_found = self.resolver.detect_anaphora(utterance)
        
        assert len(anaphora_found) == 1
        assert anaphora_found[0].expression == "that"
        assert anaphora_found[0].type == "item"
    
    def test_detect_anaphora_time_references(self):
        """Test detection of time anaphoric references."""
        utterance = "Deliver it at the same time"
        anaphora_found = self.resolver.detect_anaphora(utterance)
        
        # Should find both "it" (item) and "the same time" (time)
        assert len(anaphora_found) == 2
        
        # Find the time reference
        time_anaphora = next(a for a in anaphora_found if a.type == "time")
        assert time_anaphora.expression == "the same time"
    
    def test_detect_anaphora_multiple_types(self):
        """Test detection of multiple anaphoric references in one utterance."""
        utterance = "Change that order to deliver it there"
        anaphora_found = self.resolver.detect_anaphora(utterance)
        
        # Should find "that order" (order), "it" (item), "there" (location)
        # Note: "it" might be ambiguous, but should be detected as item
        assert len(anaphora_found) >= 2  # At least order and location
        
        types_found = {a.type for a in anaphora_found}
        assert "order" in types_found
        assert "location" in types_found
    
    def test_detect_anaphora_hindi(self):
        """Test detection of Hindi anaphoric references."""
        utterance = "मैं वह ऑर्डर कैंसल करना चाहता हूं"  # "I want to cancel that order"
        anaphora_found = self.resolver.detect_anaphora(utterance, language="hindi")
        
        assert len(anaphora_found) == 1
        assert anaphora_found[0].type == "order"
    
    def test_resolve_references_order(self):
        """Test resolution of order references."""
        utterance = "Cancel that order"
        resolved, updated_context = self.resolver.resolve_references(
            utterance, self.context
        )
        
        assert resolved == "Cancel order ORD123"
        assert updated_context.last_mentioned_order == "ORD123"  # Should remain unchanged
    
    def test_resolve_references_item(self):
        """Test resolution of item references."""
        utterance = "I want more of that"
        resolved, updated_context = self.resolver.resolve_references(
            utterance, self.context
        )
        
        assert resolved == "I want more of pizza"
    
    def test_resolve_references_time(self):
        """Test resolution of time references."""
        utterance = "Deliver at the same time"
        resolved, updated_context = self.resolver.resolve_references(
            utterance, self.context
        )
        
        assert resolved == "Deliver at 2:30 PM"
    
    def test_resolve_references_quantity(self):
        """Test resolution of quantity references."""
        utterance = "I want the same amount"
        resolved, updated_context = self.resolver.resolve_references(
            utterance, self.context
        )
        
        assert resolved == "I want 2"
    
    def test_resolve_references_location(self):
        """Test resolution of location references."""
        utterance = "Deliver there"
        resolved, updated_context = self.resolver.resolve_references(
            utterance, self.context
        )
        
        assert resolved == "Deliver 123 Main St"
    
    def test_resolve_references_no_context(self):
        """Test resolution when no context is available."""
        empty_context = AnaphoraContext()
        utterance = "Cancel that order"
        
        resolved, updated_context = self.resolver.resolve_references(
            utterance, empty_context
        )
        
        # Should remain unchanged when no context available
        assert resolved == "Cancel that order"
    
    def test_resolve_references_multiple(self):
        """Test resolution of multiple references in one utterance."""
        utterance = "Change that order to deliver it there"
        resolved, updated_context = self.resolver.resolve_references(
            utterance, self.context
        )
        
        # Should resolve "that order" and "there", "it" might not be detected as item
        assert "order ORD123" in resolved
        assert "123 Main St" in resolved
    
    def test_extract_entities_order_id(self):
        """Test extraction of order IDs from utterances."""
        test_cases = [
            ("I want to check order ABC123", "ABC123"),
            ("What's the status of order #XYZ789", "XYZ789"),
            ("Order number 456 is ready", "456"),
        ]
        
        for utterance, expected_order in test_cases:
            entities = self.resolver.extract_entities(utterance)
            assert entities.get("order_id") == expected_order, f"Failed for: {utterance}"
    
    def test_extract_entities_item_name(self):
        """Test extraction of item names from utterances."""
        test_cases = [
            ("I want a pizza", "pizza"),
            ("Order some coffee please", "coffee"),
            ("Get me a burger", "burger"),
        ]
        
        for utterance, expected_item in test_cases:
            entities = self.resolver.extract_entities(utterance)
            assert expected_item in entities.get("item_name", "").lower()
    
    def test_extract_entities_time(self):
        """Test extraction of time references from utterances."""
        test_cases = [
            ("Deliver at 2:30", "2:30"),
            ("Ready at 3 PM", "3 PM"),
            ("In 15 minutes", "15"),
        ]
        
        for utterance, expected_time in test_cases:
            entities = self.resolver.extract_entities(utterance)
            time_value = entities.get("time", "")
            assert expected_time in time_value
    
    def test_extract_entities_quantity(self):
        """Test extraction of quantities from utterances."""
        test_cases = [
            ("I want 3 pizzas", 3),
            ("Order 5 items", 5),
            ("Get 2 burgers", 2),
        ]
        
        for utterance, expected_quantity in test_cases:
            entities = self.resolver.extract_entities(utterance)
            assert entities.get("quantity") == expected_quantity, f"Failed for: {utterance}"
    
    def test_extract_entities_location(self):
        """Test extraction of locations from utterances."""
        test_cases = [
            ("Deliver to Main Street", "Main Street"),
            ("Address is 123 Oak Ave", "123 Oak Ave"),
        ]
        
        for utterance, expected_location in test_cases:
            entities = self.resolver.extract_entities(utterance)
            location = entities.get("location", "")
            assert expected_location in location
    
    def test_update_context_new_entities(self):
        """Test updating anaphora context with new entities."""
        entities = {
            "order_id": "NEW123",
            "item_name": "burger",
            "time": "3:00 PM",
            "quantity": 5,
            "location": "456 Oak St"
        }
        
        updated_context = self.resolver.update_context(self.context, entities)
        
        assert updated_context.last_mentioned_order == "NEW123"
        assert updated_context.last_mentioned_item == "burger"
        assert updated_context.last_mentioned_time == "3:00 PM"
        assert updated_context.last_mentioned_quantity == 5
        assert updated_context.last_mentioned_location == "456 Oak St"
    
    def test_update_context_partial_entities(self):
        """Test updating context with only some new entities."""
        entities = {"item_name": "sandwich"}
        
        updated_context = self.resolver.update_context(self.context, entities)
        
        # Only item should be updated
        assert updated_context.last_mentioned_item == "sandwich"
        # Others should remain the same
        assert updated_context.last_mentioned_order == "ORD123"
        assert updated_context.last_mentioned_time == "2:30 PM"
    
    def test_remove_overlaps(self):
        """Test removal of overlapping anaphoric expressions."""
        anaphora_list = [
            AnaphoricExpression("it", 5, "item", (5, 7)),
            AnaphoricExpression("that order", 10, "order", (10, 20)),
            AnaphoricExpression("that", 10, "item", (10, 14)),  # Overlaps with "that order"
        ]
        
        result = self.resolver._remove_overlaps(anaphora_list)
        
        # Should keep "it" and "that order" (longer), remove "that"
        assert len(result) == 2
        expressions = [a.expression for a in result]
        assert "it" in expressions
        assert "that order" in expressions
        assert "that" not in expressions
    
    def test_end_to_end_conversation_flow(self):
        """Test complete anaphora resolution in a conversation flow."""
        # Start with empty context
        context = AnaphoraContext()
        
        # First utterance: establish entities
        utterance1 = "I want to order 2 pizzas for delivery to Main Street at 6 PM"
        resolved1, context = self.resolver.resolve_references(utterance1, context)
        
        # Context should be updated
        assert context.last_mentioned_item == "pizzas"
        assert context.last_mentioned_quantity == 2
        assert context.last_mentioned_location == "Main Street"
        assert context.last_mentioned_time == "6 PM"
        
        # Second utterance: use anaphoric references
        utterance2 = "Actually, make that 3 and deliver there at the same time"
        resolved2, context = self.resolver.resolve_references(utterance2, context)
        
        # Should resolve references
        assert "Main Street" in resolved2
        assert "6 PM" in resolved2
        # Quantity should be updated to 3
        assert context.last_mentioned_quantity == 3
    
    def test_case_insensitive_matching(self):
        """Test that anaphora detection is case insensitive."""
        utterance = "Cancel THAT ORDER"
        anaphora_found = self.resolver.detect_anaphora(utterance)
        
        assert len(anaphora_found) == 1
        assert anaphora_found[0].type == "order"
    
    def test_no_anaphora_found(self):
        """Test behavior when no anaphoric expressions are found."""
        utterance = "I want to order a pizza"
        resolved, updated_context = self.resolver.resolve_references(
            utterance, self.context
        )
        
        # Should remain unchanged
        assert resolved == utterance
        # But context should be updated with new entities
        assert updated_context.last_mentioned_item == "pizza"


class TestAnaphoricExpression:
    """Test cases for the AnaphoricExpression dataclass."""
    
    def test_anaphoric_expression_creation(self):
        """Test creation of AnaphoricExpression objects."""
        expr = AnaphoricExpression(
            expression="that order",
            position=10,
            type="order",
            span=(10, 20)
        )
        
        assert expr.expression == "that order"
        assert expr.position == 10
        assert expr.type == "order"
        assert expr.span == (10, 20)


class TestMultilingualSupport:
    """Test cases for multilingual anaphora resolution."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.resolver = AnaphoraResolver()
        self.context = AnaphoraContext(
            last_mentioned_order="ORD123",
            last_mentioned_item="पिज्जा",  # "pizza" in Hindi
            last_mentioned_time="दोपहर 2 बजे"  # "2 PM" in Hindi
        )
    
    def test_hindi_anaphora_detection(self):
        """Test detection of Hindi anaphoric expressions."""
        utterance = "मैं वह ऑर्डर कैंसल करना चाहता हूं"
        anaphora_found = self.resolver.detect_anaphora(utterance, language="hindi")
        
        assert len(anaphora_found) >= 1
        # Should find order reference
        order_refs = [a for a in anaphora_found if a.type == "order"]
        assert len(order_refs) >= 1
    
    def test_fallback_to_english_patterns(self):
        """Test fallback to English patterns for unsupported languages."""
        utterance = "Cancel that order"
        anaphora_found = self.resolver.detect_anaphora(utterance, language="unsupported")
        
        # Should still work using English patterns
        assert len(anaphora_found) == 1
        assert anaphora_found[0].type == "order"


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.resolver = AnaphoraResolver()
    
    def test_empty_utterance(self):
        """Test handling of empty utterances."""
        context = AnaphoraContext()
        resolved, updated_context = self.resolver.resolve_references("", context)
        
        assert resolved == ""
        assert updated_context == context
    
    def test_whitespace_only_utterance(self):
        """Test handling of whitespace-only utterances."""
        context = AnaphoraContext()
        resolved, updated_context = self.resolver.resolve_references("   ", context)
        
        assert resolved == "   "
    
    def test_very_long_utterance(self):
        """Test handling of very long utterances."""
        long_utterance = "I want to order " + "pizza " * 100 + "and cancel that order"
        context = AnaphoraContext(last_mentioned_order="ORD123")
        
        resolved, updated_context = self.resolver.resolve_references(long_utterance, context)
        
        # Should still resolve the anaphora at the end
        assert "order ORD123" in resolved
    
    def test_special_characters_in_utterance(self):
        """Test handling of special characters in utterances."""
        utterance = "Cancel that order!!! @#$%"
        context = AnaphoraContext(last_mentioned_order="ORD123")
        
        resolved, updated_context = self.resolver.resolve_references(utterance, context)
        
        assert "order ORD123" in resolved
        assert "!!!" in resolved  # Special characters should be preserved