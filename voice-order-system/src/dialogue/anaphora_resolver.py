"""
Anaphora Resolution Module

This module implements anaphora resolution to handle pronouns and references
like "it", "that order", "the same time" in user utterances.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

from .state import AnaphoraContext

logger = logging.getLogger(__name__)


@dataclass
class AnaphoricExpression:
    """Represents a detected anaphoric expression."""
    expression: str
    position: int
    type: str  # "order", "item", "time", "quantity", "location"
    span: Tuple[int, int]  # Start and end positions


class AnaphoraResolver:
    """
    Resolves anaphoric references in user utterances using dialogue context.
    
    Supports multilingual anaphora patterns and handles different entity types
    including orders, items, times, quantities, and locations.
    """
    
    def __init__(self):
        """Initialize the anaphora resolver with multilingual patterns."""
        self.anaphora_patterns = self._load_anaphora_patterns()
        
    def _load_anaphora_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Load anaphora patterns for different languages and entity types.
        
        Returns:
            Dictionary mapping languages to entity types to pattern lists
        """
        return {
            "english": {
                "order": [
                    r"\bthat order\b", r"\bthe order\b", 
                    r"\bthat one\b", r"\bthe previous one\b",
                    r"\bmy order\b", r"\bthis order\b"
                ],
                "item": [
                    r"\bit\b", r"\bthat\b", r"\bthe same\b", 
                    r"\bthat item\b", r"\bthis one\b", r"\bthe same one\b"
                ],
                "time": [
                    r"\bthen\b", r"\bthat time\b", r"\bthe same time\b", 
                    r"\bat that time\b", r"\bthe usual time\b"
                ],
                "quantity": [
                    r"\bthe same amount\b", r"\bthat many\b", r"\bthe same quantity\b"
                ],
                "location": [
                    r"\bthere\b", r"\bthat place\b", r"\bthe same location\b"
                ]
            },
            "hindi": {
                "order": [
                    r"\bयह\b", r"\bवह ऑर्डर\b", r"\bयह ऑर्डर\b", 
                    r"\bवह वाला\b", r"\bपिछला वाला\b"
                ],
                "item": [
                    r"\bयह\b", r"\bवह\b", r"\bवही\b", 
                    r"\bवह चीज़\b", r"\bयह वाला\b"
                ],
                "time": [
                    r"\bतब\b", r"\bउस समय\b", r"\bवही समय\b", 
                    r"\bउस वक्त\b"
                ],
                "quantity": [
                    r"\bउतना ही\b", r"\bवही मात्रा\b", r"\bइतना ही\b"
                ],
                "location": [
                    r"\bवहाँ\b", r"\bउस जगह\b", r"\bवही स्थान\b"
                ]
            }
        }
    
    def resolve_references(
        self, 
        utterance: str, 
        anaphora_context: AnaphoraContext,
        language: str = "english"
    ) -> Tuple[str, AnaphoraContext]:
        """
        Main method to resolve anaphoric references in an utterance.
        
        Args:
            utterance: User utterance containing potential anaphoric expressions
            anaphora_context: Current anaphora context from dialogue state
            language: Language of the utterance (default: "english")
            
        Returns:
            Tuple of (resolved_utterance, updated_anaphora_context)
        """
        logger.debug(f"Resolving anaphora in utterance: '{utterance}' (language: {language})")
        
        # Detect anaphoric expressions
        anaphora_found = self.detect_anaphora(utterance, language)
        
        if not anaphora_found:
            logger.debug("No anaphoric expressions found")
            # Still extract entities to update context
            new_entities = self.extract_entities(utterance)
            updated_context = self.update_context(anaphora_context, new_entities)
            return utterance, updated_context
        
        logger.debug(f"Found {len(anaphora_found)} anaphoric expressions")
        
        # Resolve each anaphoric expression
        resolved_utterance = utterance
        for anaphora in sorted(anaphora_found, key=lambda x: x.position, reverse=True):
            replacement = self._get_replacement(anaphora, anaphora_context)
            if replacement:
                # Replace from end to start to maintain positions
                start, end = anaphora.span
                resolved_utterance = (
                    resolved_utterance[:start] + 
                    replacement + 
                    resolved_utterance[end:]
                )
                logger.debug(f"Resolved '{anaphora.expression}' -> '{replacement}'")
        
        # Extract entities from the original utterance to update context
        new_entities = self.extract_entities(utterance)
        updated_context = self.update_context(anaphora_context, new_entities)
        
        logger.debug(f"Final resolved utterance: '{resolved_utterance}'")
        return resolved_utterance, updated_context
    
    def detect_anaphora(self, utterance: str, language: str = "english") -> List[AnaphoricExpression]:
        """
        Detect anaphoric expressions in the utterance.
        
        Args:
            utterance: User utterance to analyze
            language: Language of the utterance
            
        Returns:
            List of detected anaphoric expressions
        """
        anaphora_found = []
        
        # Get patterns for the specified language, fallback to English
        lang_patterns = self.anaphora_patterns.get(language, self.anaphora_patterns["english"])
        
        for entity_type, patterns in lang_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, utterance, re.IGNORECASE)
                for match in matches:
                    anaphora_found.append(AnaphoricExpression(
                        expression=match.group(),
                        position=match.start(),
                        type=entity_type,
                        span=(match.start(), match.end())
                    ))
        
        # Remove overlapping matches, keeping the longest ones
        anaphora_found = self._remove_overlaps(anaphora_found)
        
        return anaphora_found
    
    def extract_entities(self, utterance: str) -> Dict[str, Any]:
        """
        Extract entities from the utterance to update anaphora context.
        
        Args:
            utterance: User utterance to analyze
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        
        # Extract order IDs (simple pattern matching)
        order_patterns = [
            r"order\s+#?([A-Z0-9]+)",
            r"order\s+number\s+([A-Z0-9]+)"
        ]
        for pattern in order_patterns:
            match = re.search(pattern, utterance, re.IGNORECASE)
            if match:
                order_id = match.group(1)
                # Skip if it's just "number" (common false positive)
                if order_id.lower() != "number":
                    entities["order_id"] = order_id
                    break
        
        # Extract item names (look for food items after common keywords)
        item_patterns = [
            r"(?:want|order|get|have)\s+(?:a|an|some|the)?\s*(\d+\s+)?([a-zA-Z]+)(?:\s+(?:please|for|at|with|to)|$)",
            r"(\d+\s+)?(pizza|burger|sandwich|coffee|tea|drink|meal|burgers|pizzas)s?\b",
        ]
        for pattern in item_patterns:
            match = re.search(pattern, utterance, re.IGNORECASE)
            if match:
                # Get the item name (last group that's not a number)
                groups = match.groups()
                item = groups[-1] if groups else None
                if item and len(item) > 1:  # Avoid single characters
                    entities["item_name"] = item
                    break
        
        # Extract time references
        time_patterns = [
            r"at\s+(\d{1,2}:\d{2})",
            r"at\s+(\d{1,2}\s*(?:am|pm))",
            r"(?:in|after)\s+(\d+)\s*(?:minutes?|mins?)",
            r"(?:at|around)\s+(\w+\s*(?:o'clock|am|pm))"
        ]
        for pattern in time_patterns:
            match = re.search(pattern, utterance, re.IGNORECASE)
            if match:
                entities["time"] = match.group(1)
                break
        
        # Extract quantities
        quantity_patterns = [
            r"(\d+)\s*(?:pieces?|items?|orders?|pizzas?|burgers?)",
            r"(\d+)\s+(?:of|x)\s*",
            r"(?:want|order|get|make)\s+(?:that\s+)?(\d+)\s*"
        ]
        for pattern in quantity_patterns:
            match = re.search(pattern, utterance, re.IGNORECASE)
            if match:
                try:
                    entities["quantity"] = int(match.group(1))
                    break
                except ValueError:
                    continue
        
        # Extract locations
        location_patterns = [
            r"(?:to|at|deliver to|delivery to)\s+([a-zA-Z\s]+?)(?:\s+(?:at|please|thanks|address|and)|$)",
            r"address\s+is\s+([a-zA-Z0-9\s,]+)",
        ]
        for pattern in location_patterns:
            match = re.search(pattern, utterance, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                # Skip time-related phrases
                if (location and len(location) > 2 and 
                    not re.search(r'\b(?:time|o\'?clock|am|pm|minutes?|hours?)\b', location, re.IGNORECASE)):
                    entities["location"] = location
                    break
        
        logger.debug(f"Extracted entities: {entities}")
        return entities
    
    def update_context(
        self, 
        anaphora_context: AnaphoraContext, 
        entities: Dict[str, Any]
    ) -> AnaphoraContext:
        """
        Update anaphora context with newly extracted entities.
        
        Args:
            anaphora_context: Current anaphora context
            entities: Newly extracted entities
            
        Returns:
            Updated anaphora context
        """
        # Create a copy to avoid modifying the original
        updated_context = AnaphoraContext(
            last_mentioned_order=anaphora_context.last_mentioned_order,
            last_mentioned_item=anaphora_context.last_mentioned_item,
            last_mentioned_time=anaphora_context.last_mentioned_time,
            last_mentioned_quantity=anaphora_context.last_mentioned_quantity,
            last_mentioned_location=anaphora_context.last_mentioned_location
        )
        
        # Update with new entities
        if "order_id" in entities:
            updated_context.last_mentioned_order = entities["order_id"]
        if "item_name" in entities:
            updated_context.last_mentioned_item = entities["item_name"]
        if "time" in entities:
            updated_context.last_mentioned_time = entities["time"]
        if "quantity" in entities:
            updated_context.last_mentioned_quantity = entities["quantity"]
        if "location" in entities:
            updated_context.last_mentioned_location = entities["location"]
        
        return updated_context
    
    def _get_replacement(
        self, 
        anaphora: AnaphoricExpression, 
        context: AnaphoraContext
    ) -> Optional[str]:
        """
        Get the replacement text for an anaphoric expression.
        
        Args:
            anaphora: The anaphoric expression to resolve
            context: Current anaphora context
            
        Returns:
            Replacement text or None if no resolution available
        """
        if anaphora.type == "order" and context.last_mentioned_order:
            return f"order {context.last_mentioned_order}"
        elif anaphora.type == "item" and context.last_mentioned_item:
            return context.last_mentioned_item
        elif anaphora.type == "time" and context.last_mentioned_time:
            return context.last_mentioned_time
        elif anaphora.type == "quantity" and context.last_mentioned_quantity:
            return str(context.last_mentioned_quantity)
        elif anaphora.type == "location" and context.last_mentioned_location:
            return context.last_mentioned_location
        
        logger.warning(f"Could not resolve anaphora '{anaphora.expression}' of type '{anaphora.type}'")
        return None
    
    def _remove_overlaps(self, anaphora_list: List[AnaphoricExpression]) -> List[AnaphoricExpression]:
        """
        Remove overlapping anaphoric expressions, keeping the longest ones.
        
        Args:
            anaphora_list: List of detected anaphoric expressions
            
        Returns:
            List with overlaps removed
        """
        if not anaphora_list:
            return anaphora_list
        
        # Sort by position
        sorted_anaphora = sorted(anaphora_list, key=lambda x: x.position)
        
        result = []
        for current in sorted_anaphora:
            # Check if current overlaps with any in result
            overlaps = False
            for existing in result:
                if (current.span[0] < existing.span[1] and 
                    current.span[1] > existing.span[0]):
                    # There's an overlap
                    if len(current.expression) > len(existing.expression):
                        # Current is longer, replace existing
                        result.remove(existing)
                        result.append(current)
                    overlaps = True
                    break
            
            if not overlaps:
                result.append(current)
        
        return result