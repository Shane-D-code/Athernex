"""
Dialogue State Tracker for managing conversation sessions.

Implements session creation, retrieval, slot merging, expiration,
and context summarization for multi-turn dialogues.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from uuid import uuid4

from .state import DialogueState, SlotValue, AnaphoraContext
from .anaphora_resolver import AnaphoraResolver

logger = logging.getLogger(__name__)


class DialogueStateTracker:
    """
    Manages dialogue states across multiple conversation sessions.
    
    Features:
    - Session creation and retrieval
    - Slot-value merging with confidence-based updates
    - Automatic session expiration (10 turns or 5 minutes)
    - Context summarization when exceeding 8000 tokens
    - Thread-safe session management
    """
    
    def __init__(
        self,
        max_turns: int = 10,
        max_duration_minutes: int = 5,
        max_tokens: int = 8000,
    ):
        """
        Initialize the dialogue state tracker.
        
        Args:
            max_turns: Maximum turns before session expiration
            max_duration_minutes: Maximum session duration in minutes
            max_tokens: Maximum tokens before context summarization
        """
        self.max_turns = max_turns
        self.max_duration_minutes = max_duration_minutes
        self.max_tokens = max_tokens
        
        # In-memory session storage (use Redis/database for production)
        self._sessions: Dict[str, DialogueState] = {}
        
        # Initialize anaphora resolver
        self.anaphora_resolver = AnaphoraResolver()
        
        logger.info(
            "DialogueStateTracker initialized: max_turns=%d, max_duration=%dm, max_tokens=%d",
            max_turns, max_duration_minutes, max_tokens
        )
    
    def create_session(
        self,
        session_id: Optional[str] = None,
        language: Optional[str] = None,
        is_code_mixed: bool = False,
    ) -> DialogueState:
        """
        Create a new dialogue session.
        
        Args:
            session_id: Optional custom session ID (generates UUID if None)
            language: Initial language for the session
            is_code_mixed: Whether the session uses code-mixed speech
            
        Returns:
            New DialogueState instance
        """
        if session_id is None:
            session_id = str(uuid4())
        
        # Check if session already exists
        if session_id in self._sessions:
            logger.warning("Session %s already exists, returning existing session", session_id)
            return self._sessions[session_id]
        
        state = DialogueState(
            session_id=session_id,
            language=language,
            is_code_mixed=is_code_mixed,
        )
        
        self._sessions[session_id] = state
        logger.info("Created new session: %s (language=%s, code_mixed=%s)", 
                   session_id, language, is_code_mixed)
        
        return state
    
    def get_session(self, session_id: str) -> Optional[DialogueState]:
        """
        Retrieve an existing dialogue session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            DialogueState if found, None otherwise
        """
        state = self._sessions.get(session_id)
        
        if state is None:
            logger.warning("Session %s not found", session_id)
            return None
        
        # Check if session has expired
        if state.is_expired():
            logger.info("Session %s has expired (time-based)", session_id)
            self.delete_session(session_id)
            return None
        
        if state.should_expire_by_turns(self.max_turns):
            logger.info("Session %s has expired (turn-based: %d turns)", 
                       session_id, state.turn_count)
            self.delete_session(session_id)
            return None
        
        return state
    
    def get_or_create_session(
        self,
        session_id: Optional[str] = None,
        language: Optional[str] = None,
        is_code_mixed: bool = False,
    ) -> DialogueState:
        """
        Get existing session or create new one if not found.
        
        Args:
            session_id: Session identifier
            language: Language for new session
            is_code_mixed: Code-mixed flag for new session
            
        Returns:
            DialogueState instance
        """
        if session_id:
            state = self.get_session(session_id)
            if state:
                return state
        
        return self.create_session(session_id, language, is_code_mixed)
    
    def update_session(
        self,
        session_id: str,
        user_utterance: str,
        system_response: Optional[str] = None,
        extracted_data: Optional[Dict[str, Any]] = None,
        confidence: float = 0.0,
    ) -> DialogueState:
        """
        Add a new conversation turn to the session.
        
        Args:
            session_id: Session identifier
            user_utterance: User's utterance
            system_response: System's response
            extracted_data: Extracted structured data
            confidence: Confidence score for this turn
            
        Returns:
            Updated DialogueState
            
        Raises:
            ValueError: If session not found
        """
        state = self.get_session(session_id)
        if state is None:
            raise ValueError(f"Session {session_id} not found or expired")
        
        # Add the turn
        state.add_turn(user_utterance, system_response, extracted_data, confidence)
        
        # Check if summarization is needed
        if state.should_summarize(self.max_tokens):
            logger.info("Session %s exceeds token limit, summarization recommended", session_id)
            self._summarize_context(state)
        
        # Extend expiration on activity
        state.extend_expiration(self.max_duration_minutes)
        
        logger.debug("Updated session %s: turn %d, tokens=%d", 
                    session_id, state.turn_count, state.total_tokens)
        
        return state
    
    def merge_slots(
        self,
        session_id: str,
        new_slots: Dict[str, Any],
        confidence: float = 0.8,
        source: str = "user",
    ) -> DialogueState:
        """
        Merge new slot values with existing session slots.
        
        Uses confidence-based merging: only updates if new confidence
        is higher than existing confidence.
        
        Args:
            session_id: Session identifier
            new_slots: Dictionary of slot_name -> value
            confidence: Confidence for new slots
            source: Source of the slots ("user" or "system")
            
        Returns:
            Updated DialogueState
            
        Raises:
            ValueError: If session not found
        """
        state = self.get_session(session_id)
        if state is None:
            raise ValueError(f"Session {session_id} not found or expired")
        
        merged_count = 0
        for slot_name, value in new_slots.items():
            # Skip None values
            if value is None:
                continue
            
            existing = state.get_slot(slot_name)
            
            # Update if slot doesn't exist or new confidence is higher
            if existing is None:
                state.set_slot(slot_name, value, confidence, source)
                merged_count += 1
                logger.debug("Set new slot %s=%s (confidence=%.2f)", 
                           slot_name, value, confidence)
            elif confidence >= existing.confidence:
                state.update_slot(slot_name, value, confidence, source)
                merged_count += 1
                logger.debug("Updated slot %s: %s -> %s (confidence %.2f -> %.2f)",
                           slot_name, existing.value, value, 
                           existing.confidence, confidence)
            else:
                logger.debug("Skipped slot %s: existing confidence %.2f > new %.2f",
                           slot_name, existing.confidence, confidence)
        
        logger.info("Merged %d slots into session %s", merged_count, session_id)
        return state
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a dialogue session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info("Deleted session %s", session_id)
            return True
        
        logger.warning("Cannot delete session %s: not found", session_id)
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.
        
        Returns:
            Number of sessions deleted
        """
        expired_ids = []
        
        for session_id, state in self._sessions.items():
            if state.is_expired() or state.should_expire_by_turns(self.max_turns):
                expired_ids.append(session_id)
        
        for session_id in expired_ids:
            self.delete_session(session_id)
        
        if expired_ids:
            logger.info("Cleaned up %d expired sessions", len(expired_ids))
        
        return len(expired_ids)
    
    def get_active_session_count(self) -> int:
        """Get the number of active sessions."""
        return len(self._sessions)
    
    def get_all_session_ids(self) -> List[str]:
        """Get all active session IDs."""
        return list(self._sessions.keys())
    
    def _summarize_context(self, state: DialogueState):
        """
        Summarize conversation history to reduce token count.
        
        Strategy:
        1. Keep the most recent 3 turns in full
        2. Summarize older turns into key points
        3. Preserve all slot values
        
        Args:
            state: DialogueState to summarize
        """
        if len(state.conversation_history) <= 3:
            return  # Nothing to summarize
        
        # Keep recent turns
        recent_turns = state.get_recent_turns(3)
        older_turns = state.conversation_history[:-3]
        
        # Create summary of older turns
        summary_points = []
        for turn in older_turns:
            if turn.extracted_data:
                intent = turn.extracted_data.get("intent", "unknown")
                summary_points.append(f"Turn {turn.turn}: {intent}")
        
        summary_text = "; ".join(summary_points) if summary_points else "Earlier conversation"
        
        # Replace conversation history with summary + recent turns
        state.conversation_history = recent_turns
        
        # Recalculate token count (rough estimate)
        state.total_tokens = len(summary_text) // 4
        for turn in recent_turns:
            turn_tokens = (len(turn.user_utterance) + len(turn.system_response or "")) // 4
            state.total_tokens += turn_tokens
        
        logger.info("Summarized session %s: %d turns -> summary + %d recent turns, tokens=%d",
                   state.session_id, len(older_turns) + len(recent_turns), 
                   len(recent_turns), state.total_tokens)
    
    def update_anaphora_context(
        self,
        session_id: str,
        order_id: Optional[str] = None,
        item: Optional[str] = None,
        time: Optional[str] = None,
        quantity: Optional[int] = None,
        location: Optional[str] = None,
    ) -> DialogueState:
        """
        Update anaphora context for reference resolution.
        
        Args:
            session_id: Session identifier
            order_id: Last mentioned order ID
            item: Last mentioned item
            time: Last mentioned time
            quantity: Last mentioned quantity
            location: Last mentioned location
            
        Returns:
            Updated DialogueState
            
        Raises:
            ValueError: If session not found
        """
        state = self.get_session(session_id)
        if state is None:
            raise ValueError(f"Session {session_id} not found or expired")
        
        if order_id is not None:
            state.anaphora_context.last_mentioned_order = order_id
        if item is not None:
            state.anaphora_context.last_mentioned_item = item
        if time is not None:
            state.anaphora_context.last_mentioned_time = time
        if quantity is not None:
            state.anaphora_context.last_mentioned_quantity = quantity
        if location is not None:
            state.anaphora_context.last_mentioned_location = location
        
        logger.debug("Updated anaphora context for session %s", session_id)
        return state
    
    def get_context_for_llm(self, session_id: str) -> Dict[str, Any]:
        """
        Get formatted context for LLM processing.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session context for LLM
        """
        state = self.get_session(session_id)
        if state is None:
            return {}
        
        # Get recent conversation
        recent_turns = state.get_recent_turns(3)
        conversation = [
            {
                "turn": turn.turn,
                "user": turn.user_utterance,
                "system": turn.system_response,
            }
            for turn in recent_turns
        ]
        
        # Get current slots
        slots = {
            name: {
                "value": slot.value,
                "confidence": slot.confidence,
            }
            for name, slot in state.slots.items()
        }
        
        return {
            "session_id": session_id,
            "turn_count": state.turn_count,
            "language": state.language,
            "is_code_mixed": state.is_code_mixed,
            "conversation": conversation,
            "slots": slots,
            "anaphora_context": {
                "last_order": state.anaphora_context.last_mentioned_order,
                "last_item": state.anaphora_context.last_mentioned_item,
                "last_time": state.anaphora_context.last_mentioned_time,
            },
        }
    
    def resolve_anaphora(
        self,
        session_id: str,
        utterance: str,
        language: str = "english"
    ) -> str:
        """
        Resolve anaphoric references in a user utterance.
        
        Args:
            session_id: Session identifier
            utterance: User utterance containing potential anaphoric expressions
            language: Language of the utterance (default: "english")
            
        Returns:
            Utterance with anaphoric references resolved
            
        Raises:
            ValueError: If session not found
        """
        state = self.get_session(session_id)
        if state is None:
            raise ValueError(f"Session {session_id} not found or expired")
        
        # Resolve anaphoric references
        resolved_utterance, updated_context = self.anaphora_resolver.resolve_references(
            utterance, state.anaphora_context, language
        )
        
        # Update the session's anaphora context
        state.anaphora_context = updated_context
        
        logger.debug(
            "Resolved anaphora for session %s: '%s' -> '%s'",
            session_id, utterance, resolved_utterance
        )
        
        return resolved_utterance
