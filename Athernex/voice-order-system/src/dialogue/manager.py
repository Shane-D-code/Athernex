"""
Dialogue State Manager for multi-turn conversations.

Tracks session state, slot-value pairs, anaphora resolution,
and context summarization across conversation turns.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from llm.base import Intent, OrderItem

logger = logging.getLogger(__name__)


class DialogueState(str, Enum):
    """States in the order dialogue flow."""
    GREETING = "greeting"
    AWAITING_ORDER = "awaiting_order"
    CLARIFYING = "clarifying"
    CONFIRMING = "confirming"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class DialogueContext:
    """Context maintained across dialogue turns."""
    session_id: str
    state: DialogueState = DialogueState.GREETING
    turn_count: int = 0
    last_user_utterance: Optional[str] = None
    last_bot_response: Optional[str] = None
    current_intent: Optional[Intent] = None
    current_items: List[OrderItem] = field(default_factory=list)
    current_delivery_time: Optional[str] = None
    current_order_id: Optional[str] = None
    special_instructions: Optional[str] = None
    pending_clarification: Optional[str] = None
    slots_filled: Dict[str, bool] = field(default_factory=dict)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    language: str = "en"

    def to_llm_context(self) -> Dict[str, Any]:
        """Export context for LLM prompting."""
        return {
            "turn_count": self.turn_count,
            "current_intent": self.current_intent.value if self.current_intent else None,
            "current_items": [
                {"name": item.name, "quantity": item.quantity, "unit": item.unit}
                for item in self.current_items
            ],
            "delivery_time": self.current_delivery_time,
            "order_id": self.current_order_id,
            "special_instructions": self.special_instructions,
            "pending_clarification": self.pending_clarification,
            "language": self.language,
            "last_bot_response": self.last_bot_response,
        }

    def add_turn(self, user_utterance: str, bot_response: str, structured_data: Optional[Any] = None):
        """Record a dialogue turn."""
        self.turn_count += 1
        self.last_user_utterance = user_utterance
        self.last_bot_response = bot_response
        self.last_activity = time.time()
        
        self.conversation_history.append({
            "turn": self.turn_count,
            "user": user_utterance,
            "bot": bot_response,
            "structured_data": structured_data,
            "timestamp": time.time(),
        })

    def update_from_structured_data(self, data: Any):
        """Update context from LLM structured output."""
        if hasattr(data, 'intent') and data.intent:
            self.current_intent = data.intent
        if hasattr(data, 'items') and data.items:
            self.current_items = data.items
        if hasattr(data, 'delivery_time') and data.delivery_time:
            self.current_delivery_time = data.delivery_time
        if hasattr(data, 'order_id') and data.order_id:
            self.current_order_id = data.order_id
        if hasattr(data, 'special_instructions') and data.special_instructions:
            self.special_instructions = data.special_instructions

    def is_expired(self, timeout_seconds: float = 300.0) -> bool:
        """Check if session has expired due to inactivity."""
        return (time.time() - self.last_activity) > timeout_seconds

    def get_summary(self) -> str:
        """Get a concise summary of the dialogue for context windows."""
        items_str = ", ".join([f"{i.quantity}x {i.name}" for i in self.current_items]) if self.current_items else "none"
        return (
            f"State: {self.state.value}, Intent: {self.current_intent.value if self.current_intent else 'none'}, "
            f"Items: {items_str}, Delivery: {self.current_delivery_time or 'not set'}, "
            f"Turns: {self.turn_count}"
        )


class DialogueManager:
    """
    Manages dialogue states and session contexts.
    
    Handles:
    - Session lifecycle (create, update, expire)
    - Slot filling tracking
    - Anaphora resolution ("add one more", "cancel it")
    - State transitions based on intent and confidence
    """

    def __init__(self, session_timeout_seconds: float = 300.0):
        self.sessions: Dict[str, DialogueContext] = {}
        self.session_timeout = session_timeout_seconds
        logger.info("DialogueManager initialized with timeout=%.0fs", session_timeout_seconds)

    def create_session(self, session_id: str, language: str = "en") -> DialogueContext:
        """Create a new dialogue session."""
        context = DialogueContext(session_id=session_id, language=language)
        self.sessions[session_id] = context
        logger.info("Created session %s (language=%s)", session_id, language)
        return context

    def get_session(self, session_id: str) -> Optional[DialogueContext]:
        """Get existing session or None if expired/unknown."""
        context = self.sessions.get(session_id)
        if context is None:
            return None
        if context.is_expired(self.session_timeout):
            logger.info("Session %s expired, removing", session_id)
            del self.sessions[session_id]
            return None
        return context

    def get_or_create_session(self, session_id: str, language: str = "en") -> DialogueContext:
        """Get existing session or create new one."""
        context = self.get_session(session_id)
        if context is None:
            context = self.create_session(session_id, language)
        return context

    def update_session(
        self,
        session_id: str,
        user_utterance: str,
        bot_response: str,
        structured_data: Optional[Any] = None,
        new_state: Optional[DialogueState] = None,
    ) -> DialogueContext:
        """Update session with a new dialogue turn."""
        context = self.get_or_create_session(session_id)
        context.add_turn(user_utterance, bot_response, structured_data)
        
        if structured_data:
            context.update_from_structured_data(structured_data)
        
        if new_state:
            context.state = new_state
        else:
            # Auto-transition based on intent
            context.state = self._infer_state(context, structured_data)
        
        logger.debug("Updated session %s: %s", session_id, context.get_summary())
        return context

    def _infer_state(self, context: DialogueContext, structured_data: Optional[Any]) -> DialogueState:
        """Infer dialogue state from context and structured data."""
        if structured_data is None:
            return context.state
        
        intent = getattr(structured_data, 'intent', None)
        missing = getattr(structured_data, 'missing_fields', [])
        confidence = getattr(structured_data, 'confidence', 0.0)
        
        if intent == Intent.CANCEL_ORDER:
            return DialogueState.CANCELLED
        
        if intent == Intent.CONFIRM_ORDER:
            return DialogueState.COMPLETED
        
        if missing and confidence < 0.85:
            return DialogueState.CLARIFYING
        
        if intent == Intent.PLACE_ORDER and not missing:
            return DialogueState.CONFIRMING
        
        if intent in (Intent.MODIFY_ORDER, Intent.CHECK_STATUS):
            return DialogueState.PROCESSING
        
        return DialogueState.AWAITING_ORDER

    def resolve_anaphora(self, context: DialogueContext, utterance: str) -> str:
        """
        Resolve anaphoric references in user utterance.
        
        Examples:
        - "add one more" -> "add one more {last_item}"
        - "cancel it" -> "cancel order {order_id}"
        """
        utterance_lower = utterance.lower().strip()
        
        # Resolve "it"/"that" to last mentioned item
        if any(word in utterance_lower for word in ["it", "that", "this"]):
            if context.current_items:
                last_item = context.current_items[-1].name
                # Simple replacement for common patterns
                if "cancel" in utterance_lower:
                    if context.current_order_id:
                        utterance = utterance.replace("it", f"order {context.current_order_id}")
                    elif context.current_items:
                        utterance = utterance.replace("it", f"{last_item} order")
                elif "add" in utterance_lower or "remove" in utterance_lower:
                    utterance = utterance.replace("one more", f"one more {last_item}")
                    utterance = utterance.replace("it", last_item)
        
        # Resolve "another one" / "one more"
        if "one more" in utterance_lower or "another" in utterance_lower:
            if context.current_items:
                last_item = context.current_items[-1].name
                utterance = utterance.replace("one more", f"one more {last_item}")
                utterance = utterance.replace("another", f"another {last_item}")
        
        logger.debug("Anaphora resolved: '%s' -> '%s'", context.last_user_utterance or "", utterance)
        return utterance

    def get_clarification_prompt(self, context: DialogueContext, missing_fields: List[str]) -> str:
        """Generate a context-aware clarification prompt."""
        if not missing_fields:
            return "Could you please provide more details?"
        
        field_prompts = {
            "items": "What would you like to order?",
            "delivery_time": "When would you like the delivery?",
            "order_id": "Which order number are you referring to?",
            "quantity": "How many would you like?",
            "special_instructions": "Any special instructions?",
        }
        
        # Prioritize missing fields
        for field in missing_fields:
            if field in field_prompts:
                return field_prompts[field]
        
        return f"Could you please provide the {missing_fields[0]}?"

    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions and return count removed."""
        expired = [
            sid for sid, ctx in self.sessions.items()
            if ctx.is_expired(self.session_timeout)
        ]
        for sid in expired:
            del self.sessions[sid]
        if expired:
            logger.info("Cleaned up %d expired sessions", len(expired))
        return len(expired)

    def get_active_session_count(self) -> int:
        """Get number of active (non-expired) sessions."""
        self.cleanup_expired_sessions()
        return len(self.sessions)

