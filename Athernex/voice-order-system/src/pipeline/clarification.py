"""
Clarification dialogue flow manager.

Detects when clarification is needed, generates targeted questions,
waits for customer response, and merges the clarification with the
original order data.

Validates Requirements 3.1, 3.2, 3.3, 3.4, 7.7.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from confidence.analyzer import ClarificationRecommendation
from llm.base import StructuredOrderData, Intent

logger = logging.getLogger(__name__)

MAX_CLARIFICATION_ROUNDS = 2


@dataclass
class ClarificationContext:
    """Tracks state across clarification rounds."""
    session_id: str
    original_data: StructuredOrderData
    rounds: int = 0
    resolved: bool = False
    final_data: Optional[StructuredOrderData] = None


class ClarificationManager:
    """
    Manages multi-round clarification dialogues.

    Requirements:
    - 3.1: Trigger clarification when STT confidence below threshold
    - 3.2: Trigger clarification when LLM clarity below threshold
    - 3.3: Flag specific low-confidence words for clarification
    - 3.4: Trigger clarification for missing required fields
    - 7.7: Wait for customer response and resume from Confidence Analyzer
    """

    def __init__(self, max_rounds: int = MAX_CLARIFICATION_ROUNDS):
        self.max_rounds = max_rounds
        self._active: Dict[str, ClarificationContext] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start_clarification(
        self,
        session_id: str,
        original_data: StructuredOrderData,
        recommendation: ClarificationRecommendation,
    ) -> str:
        """
        Begin a clarification dialogue for a session.

        Args:
            session_id: Active session ID
            original_data: The partially-understood order data
            recommendation: Clarification recommendation from ConfidenceAnalyzer

        Returns:
            The clarification question to speak to the customer
        """
        ctx = ClarificationContext(
            session_id=session_id,
            original_data=original_data,
        )
        self._active[session_id] = ctx

        question = self._build_question(recommendation, original_data)
        logger.info(
            "Clarification started for session %s (round 1): '%s'",
            session_id, question,
        )
        return question

    def apply_clarification(
        self,
        session_id: str,
        clarification_data: StructuredOrderData,
        recommendation: ClarificationRecommendation,
    ) -> tuple[bool, Optional[str], Optional[StructuredOrderData]]:
        """
        Apply a clarification response and decide whether to proceed or ask again.

        Args:
            session_id: Active session ID
            clarification_data: Structured data extracted from clarification response
            recommendation: New confidence recommendation after clarification

        Returns:
            (resolved, follow_up_question, merged_data)
            - resolved: True if confidence is now sufficient
            - follow_up_question: Next question if another round is needed
            - merged_data: Merged StructuredOrderData if resolved
        """
        ctx = self._active.get(session_id)
        if ctx is None:
            logger.warning("No active clarification for session %s", session_id)
            return True, None, clarification_data

        ctx.rounds += 1
        merged = self._merge_data(ctx.original_data, clarification_data)

        if not recommendation.should_clarify:
            # Confidence is now sufficient
            ctx.resolved = True
            ctx.final_data = merged
            del self._active[session_id]
            logger.info("Clarification resolved for session %s after %d round(s)", session_id, ctx.rounds)
            return True, None, merged

        if ctx.rounds >= self.max_rounds:
            # Give up after max rounds — proceed with best effort
            logger.warning(
                "Max clarification rounds (%d) reached for session %s — proceeding",
                self.max_rounds, session_id,
            )
            ctx.resolved = True
            ctx.final_data = merged
            del self._active[session_id]
            return True, None, merged

        # Another round needed
        question = self._build_question(recommendation, merged)
        logger.info(
            "Clarification round %d for session %s: '%s'",
            ctx.rounds + 1, session_id, question,
        )
        ctx.original_data = merged  # update with merged data for next round
        return False, question, None

    def is_active(self, session_id: str) -> bool:
        """Return True if a clarification dialogue is in progress."""
        return session_id in self._active

    def cancel(self, session_id: str) -> None:
        """Cancel an active clarification (e.g. on barge-in)."""
        self._active.pop(session_id, None)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_question(
        self,
        recommendation: ClarificationRecommendation,
        data: StructuredOrderData,
    ) -> str:
        """Build a targeted clarification question."""
        if recommendation.suggested_question:
            return recommendation.suggested_question

        # Fallback question generation
        if recommendation.missing_fields:
            field = recommendation.missing_fields[0]
            questions = {
                "items": "What would you like to order?",
                "delivery_time": "When would you like the delivery?",
                "order_id": "Which order number are you referring to?",
                "quantity": "How many would you like?",
            }
            return questions.get(field, f"Could you please provide the {field}?")

        if recommendation.low_confidence_items:
            words = ", ".join(recommendation.low_confidence_items[:2])
            return f"I didn't quite catch '{words}'. Could you repeat that?"

        return "I'm sorry, could you please repeat your order?"

    @staticmethod
    def _merge_data(
        original: StructuredOrderData,
        clarification: StructuredOrderData,
    ) -> StructuredOrderData:
        """
        Merge clarification data into original order data.

        Clarification values override original only when they are non-empty.
        """
        from copy import deepcopy
        merged = deepcopy(original)

        if clarification.items:
            merged.items = clarification.items
        if clarification.delivery_time:
            merged.delivery_time = clarification.delivery_time
        if clarification.special_instructions:
            merged.special_instructions = clarification.special_instructions
        if clarification.order_id:
            merged.order_id = clarification.order_id

        # Remove fields that were clarified from missing_fields
        clarified = set()
        if clarification.items:
            clarified.add("items")
        if clarification.delivery_time:
            clarified.add("delivery_time")
        if clarification.special_instructions:
            clarified.add("special_instructions")

        merged.missing_fields = [f for f in merged.missing_fields if f not in clarified]

        # Use higher confidence
        merged.confidence = max(original.confidence, clarification.confidence)

        return merged
