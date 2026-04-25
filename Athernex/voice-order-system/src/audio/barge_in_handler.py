"""
Conversation context preservation for barge-in events.

Saves interrupted state and restarts pipeline with new input.
Validates Requirements 15.4, 15.5.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class InterruptedTurnState:
    """Snapshot of pipeline state at the moment of barge-in."""
    session_id: str
    interrupted_response: Optional[str] = None   # TTS text that was cut off
    partial_order_data: Optional[Dict[str, Any]] = None
    was_confirmation: bool = False               # True if barge-in during confirmation


class BargeInHandler:
    """
    Preserves conversation context when a barge-in occurs and
    restarts pipeline processing with the new user input.

    Requirements:
    - 15.4: Preserve interrupted conversation context
    - 15.5: Restart confirmation process when barge-in during confirmation
    """

    def __init__(self, tracker=None):
        """
        Args:
            tracker: Optional DialogueStateTracker instance for session management
        """
        self._tracker = tracker
        self._interrupted_states: Dict[str, InterruptedTurnState] = {}

    def save_interrupted_state(
        self,
        session_id: str,
        interrupted_response: Optional[str] = None,
        partial_order_data: Optional[Dict[str, Any]] = None,
        was_confirmation: bool = False,
    ) -> InterruptedTurnState:
        """
        Save the state of the pipeline at the moment of barge-in.

        Args:
            session_id: Active session ID
            interrupted_response: The TTS text that was being spoken
            partial_order_data: Any order data extracted so far
            was_confirmation: Whether the interruption happened during confirmation

        Returns:
            The saved InterruptedTurnState
        """
        state = InterruptedTurnState(
            session_id=session_id,
            interrupted_response=interrupted_response,
            partial_order_data=partial_order_data,
            was_confirmation=was_confirmation,
        )
        self._interrupted_states[session_id] = state
        logger.info(
            "Saved interrupted state for session %s (was_confirmation=%s)",
            session_id, was_confirmation,
        )
        return state

    def get_interrupted_state(self, session_id: str) -> Optional[InterruptedTurnState]:
        """Retrieve the saved interrupted state for a session."""
        return self._interrupted_states.get(session_id)

    def clear_interrupted_state(self, session_id: str) -> None:
        """Clear the interrupted state after it has been handled."""
        self._interrupted_states.pop(session_id, None)

    def handle_barge_in(
        self,
        session_id: str,
        new_audio: Optional[bytes] = None,
        interrupted_response: Optional[str] = None,
        partial_order_data: Optional[Dict[str, Any]] = None,
        was_confirmation: bool = False,
    ) -> Dict[str, Any]:
        """
        Handle a barge-in event: save state and prepare for pipeline restart.

        Args:
            session_id: Active session ID
            new_audio: The audio captured at barge-in onset
            interrupted_response: TTS text that was cut off
            partial_order_data: Partial order data from the interrupted turn
            was_confirmation: Whether barge-in occurred during order confirmation

        Returns:
            Dict with restart instructions for the pipeline:
            - restart: bool — always True
            - session_id: str
            - new_audio: bytes or None
            - was_confirmation: bool — pipeline should restart confirmation if True
            - preserved_data: dict or None — data to carry forward
        """
        self.save_interrupted_state(
            session_id=session_id,
            interrupted_response=interrupted_response,
            partial_order_data=partial_order_data,
            was_confirmation=was_confirmation,
        )

        # If we have a tracker, record the interruption as a turn
        if self._tracker is not None:
            try:
                self._tracker.update_session(
                    session_id=session_id,
                    user_utterance="[BARGE-IN]",
                    system_response=f"[INTERRUPTED: {interrupted_response or 'unknown'}]",
                )
            except Exception as e:
                logger.warning("Could not record barge-in turn: %s", e)

        logger.info(
            "Barge-in handled for session %s — pipeline will restart (was_confirmation=%s)",
            session_id, was_confirmation,
        )

        return {
            "restart": True,
            "session_id": session_id,
            "new_audio": new_audio,
            "was_confirmation": was_confirmation,
            "preserved_data": partial_order_data,
        }
