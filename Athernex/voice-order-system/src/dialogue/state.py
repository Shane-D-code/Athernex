"""
Dialogue state data models for conversation tracking.

Implements slot-value pairs, conversation history, and anaphora context
for multi-turn dialogue management.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

from pydantic import BaseModel, Field


class SlotValue(BaseModel):
    """A slot-value pair with confidence and update tracking."""
    value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    last_updated_turn: int
    source: str = "user"  # "user" or "system"


class ConversationTurn(BaseModel):
    """A single turn in the conversation."""
    turn: int
    user_utterance: str
    system_response: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class AnaphoraContext(BaseModel):
    """Context for resolving anaphoric references."""
    last_mentioned_order: Optional[str] = None
    last_mentioned_item: Optional[str] = None
    last_mentioned_time: Optional[str] = None
    last_mentioned_quantity: Optional[int] = None
    last_mentioned_location: Optional[str] = None


class DialogueState(BaseModel):
    """
    Complete dialogue state for a conversation session.
    
    Tracks:
    - Session metadata (ID, timestamps, expiration)
    - Slot-value pairs with confidence scores
    - Conversation history
    - Anaphora context for reference resolution
    """
    
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    turn_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(minutes=5)
    )
    
    # Slot-value pairs
    slots: Dict[str, SlotValue] = Field(default_factory=dict)
    
    # Conversation history
    conversation_history: List[ConversationTurn] = Field(default_factory=list)
    
    # Anaphora resolution context
    anaphora_context: AnaphoraContext = Field(default_factory=AnaphoraContext)
    
    # Session metadata
    language: Optional[str] = None
    is_code_mixed: bool = False
    total_tokens: int = 0
    
    def is_expired(self) -> bool:
        """Check if the session has expired."""
        return datetime.utcnow() > self.expires_at
    
    def should_expire_by_turns(self, max_turns: int = 10) -> bool:
        """Check if session should expire based on turn count."""
        return self.turn_count >= max_turns
    
    def should_summarize(self, max_tokens: int = 8000) -> bool:
        """Check if conversation history should be summarized."""
        return self.total_tokens > max_tokens
    
    def extend_expiration(self, minutes: int = 5):
        """Extend the session expiration time."""
        self.expires_at = datetime.utcnow() + timedelta(minutes=minutes)
        self.last_updated = datetime.utcnow()
    
    def add_turn(
        self,
        user_utterance: str,
        system_response: Optional[str] = None,
        extracted_data: Optional[Dict[str, Any]] = None,
        confidence: float = 0.0,
    ):
        """Add a new conversation turn."""
        self.turn_count += 1
        turn = ConversationTurn(
            turn=self.turn_count,
            user_utterance=user_utterance,
            system_response=system_response,
            extracted_data=extracted_data,
            confidence=confidence,
        )
        self.conversation_history.append(turn)
        self.last_updated = datetime.utcnow()
        
        # Estimate token count (rough approximation: 1 token ≈ 4 characters)
        turn_tokens = (len(user_utterance) + len(system_response or "")) // 4
        self.total_tokens += turn_tokens
    
    def get_slot(self, slot_name: str) -> Optional[SlotValue]:
        """Get a slot value by name."""
        return self.slots.get(slot_name)
    
    def set_slot(
        self,
        slot_name: str,
        value: Any,
        confidence: float,
        source: str = "user"
    ):
        """Set or update a slot value."""
        self.slots[slot_name] = SlotValue(
            value=value,
            confidence=confidence,
            last_updated_turn=self.turn_count,
            source=source,
        )
        self.last_updated = datetime.utcnow()
    
    def update_slot(
        self,
        slot_name: str,
        value: Any,
        confidence: float,
        source: str = "user"
    ):
        """Update an existing slot or create if doesn't exist."""
        existing = self.slots.get(slot_name)
        
        # Only update if new confidence is higher or slot doesn't exist
        if existing is None or confidence >= existing.confidence:
            self.set_slot(slot_name, value, confidence, source)
    
    def get_recent_turns(self, n: int = 3) -> List[ConversationTurn]:
        """Get the N most recent conversation turns."""
        return self.conversation_history[-n:] if self.conversation_history else []
    
    def get_context_summary(self) -> str:
        """Get a summary of the current dialogue context."""
        summary_parts = []
        
        if self.slots:
            summary_parts.append("Current slots:")
            for slot_name, slot_value in self.slots.items():
                summary_parts.append(
                    f"  - {slot_name}: {slot_value.value} "
                    f"(confidence: {slot_value.confidence:.2f}, "
                    f"turn: {slot_value.last_updated_turn})"
                )
        
        if self.conversation_history:
            recent_turns = self.get_recent_turns(3)
            summary_parts.append(f"\nRecent turns ({len(recent_turns)}):")
            for turn in recent_turns:
                summary_parts.append(f"  Turn {turn.turn}: {turn.user_utterance[:50]}...")
        
        return "\n".join(summary_parts) if summary_parts else "Empty dialogue state"
    
    def clear_slots(self):
        """Clear all slot values."""
        self.slots.clear()
        self.last_updated = datetime.utcnow()
    
    def reset_session(self):
        """Reset the session to initial state."""
        self.turn_count = 0
        self.slots.clear()
        self.conversation_history.clear()
        self.anaphora_context = AnaphoraContext()
        self.total_tokens = 0
        self.created_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(minutes=5)


@dataclass
class DialogueStateSnapshot:
    """
    A lightweight snapshot of dialogue state for serialization.
    
    Used for saving/loading dialogue state to/from storage.
    """
    session_id: str
    turn_count: int
    created_at: str
    last_updated: str
    expires_at: str
    slots: Dict[str, Dict[str, Any]]
    conversation_history: List[Dict[str, Any]]
    anaphora_context: Dict[str, Optional[str]]
    language: Optional[str]
    is_code_mixed: bool
    total_tokens: int
    
    @classmethod
    def from_dialogue_state(cls, state: DialogueState) -> "DialogueStateSnapshot":
        """Create a snapshot from a DialogueState."""
        return cls(
            session_id=state.session_id,
            turn_count=state.turn_count,
            created_at=state.created_at.isoformat(),
            last_updated=state.last_updated.isoformat(),
            expires_at=state.expires_at.isoformat(),
            slots={
                name: {
                    "value": slot.value,
                    "confidence": slot.confidence,
                    "last_updated_turn": slot.last_updated_turn,
                    "source": slot.source,
                }
                for name, slot in state.slots.items()
            },
            conversation_history=[
                {
                    "turn": turn.turn,
                    "user_utterance": turn.user_utterance,
                    "system_response": turn.system_response,
                    "extracted_data": turn.extracted_data,
                    "timestamp": turn.timestamp.isoformat(),
                    "confidence": turn.confidence,
                }
                for turn in state.conversation_history
            ],
            anaphora_context={
                "last_mentioned_order": state.anaphora_context.last_mentioned_order,
                "last_mentioned_item": state.anaphora_context.last_mentioned_item,
                "last_mentioned_time": state.anaphora_context.last_mentioned_time,
                "last_mentioned_quantity": state.anaphora_context.last_mentioned_quantity,
                "last_mentioned_location": state.anaphora_context.last_mentioned_location,
            },
            language=state.language,
            is_code_mixed=state.is_code_mixed,
            total_tokens=state.total_tokens,
        )
    
    def to_dialogue_state(self) -> DialogueState:
        """Restore a DialogueState from this snapshot."""
        state = DialogueState(
            session_id=self.session_id,
            turn_count=self.turn_count,
            created_at=datetime.fromisoformat(self.created_at),
            last_updated=datetime.fromisoformat(self.last_updated),
            expires_at=datetime.fromisoformat(self.expires_at),
            language=self.language,
            is_code_mixed=self.is_code_mixed,
            total_tokens=self.total_tokens,
        )
        
        # Restore slots
        for name, slot_data in self.slots.items():
            state.slots[name] = SlotValue(**slot_data)
        
        # Restore conversation history
        for turn_data in self.conversation_history:
            turn_data["timestamp"] = datetime.fromisoformat(turn_data["timestamp"])
            state.conversation_history.append(ConversationTurn(**turn_data))
        
        # Restore anaphora context
        state.anaphora_context = AnaphoraContext(**self.anaphora_context)
        
        return state
