"""
Confidence Analyzer for combined STT + LLM confidence scoring.

Implements weighted combination with penalties for low-confidence words
and missing fields. Generates clarification recommendations.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Dict

from llm.base import StructuredOrderData, Intent

logger = logging.getLogger(__name__)


@dataclass
class ClarificationRecommendation:
    """Recommendation for clarification dialogue."""
    should_clarify: bool
    reason: str
    missing_fields: List[str]
    low_confidence_items: List[str]
    suggested_question: Optional[str] = None


class ConfidenceAnalyzer:
    """
    Analyzes combined STT + LLM confidence and recommends clarifications.
    
    Formula: combined_score = 0.4 * STT + 0.6 * LLM
    Penalties:
    - Low-confidence words (<0.4): -0.1 per word
    - Missing required fields: -0.15 per field
    
    Intent-specific thresholds determine when to ask for clarification.
    """

    def __init__(self, intent_thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize confidence analyzer.

        Args:
            intent_thresholds: Dict mapping intent names to confidence thresholds
        """
        self.intent_thresholds = intent_thresholds or {
            "place_order": 0.85,
            "modify_order": 0.80,
            "cancel_order": 0.90,
            "confirm_order": 0.85,
            "check_status": 0.70,
            "request_information": 0.70,
        }
        
        # Weights for combined scoring
        self.stt_weight = 0.4
        self.llm_weight = 0.6
        
        # Penalties
        self.low_confidence_word_penalty = 0.1
        self.missing_field_penalty = 0.15
        
        logger.info("ConfidenceAnalyzer initialized with thresholds: %s", self.intent_thresholds)

    def analyze(
        self,
        stt_confidence: float,
        llm_response: StructuredOrderData,
        low_confidence_words: List[str],
    ) -> ClarificationRecommendation:
        """
        Analyze combined confidence and generate clarification recommendation.

        Args:
            stt_confidence: STT utterance-level confidence (0.0-1.0)
            llm_response: Structured order data from LLM
            low_confidence_words: List of words with confidence <0.4

        Returns:
            ClarificationRecommendation with decision and details
        """
        # Calculate base combined score
        combined_score = (
            self.stt_weight * stt_confidence +
            self.llm_weight * llm_response.confidence
        )

        # Apply penalties
        word_penalty = len(low_confidence_words) * self.low_confidence_word_penalty
        field_penalty = len(llm_response.missing_fields) * self.missing_field_penalty
        
        final_score = max(0.0, combined_score - word_penalty - field_penalty)

        # Get intent-specific threshold
        intent_name = llm_response.intent.value
        threshold = self.intent_thresholds.get(intent_name, 0.75)

        # Determine if clarification is needed
        should_clarify = final_score < threshold

        # Generate reason and suggested question
        reason = self._generate_reason(
            final_score, threshold, low_confidence_words, llm_response.missing_fields
        )
        
        suggested_question = self._generate_question(
            llm_response.intent, llm_response.missing_fields, low_confidence_words
        ) if should_clarify else None

        logger.debug(
            "Confidence analysis: STT=%.2f, LLM=%.2f, Combined=%.2f, Final=%.2f, Threshold=%.2f, Clarify=%s",
            stt_confidence, llm_response.confidence, combined_score, final_score, threshold, should_clarify
        )

        return ClarificationRecommendation(
            should_clarify=should_clarify,
            reason=reason,
            missing_fields=llm_response.missing_fields,
            low_confidence_items=low_confidence_words,
            suggested_question=suggested_question,
        )

    def _generate_reason(
        self,
        final_score: float,
        threshold: float,
        low_confidence_words: List[str],
        missing_fields: List[str],
    ) -> str:
        """Generate human-readable reason for clarification decision."""
        if final_score >= threshold:
            return f"Confidence sufficient (score={final_score:.2f}, threshold={threshold:.2f})"

        reasons = []
        if low_confidence_words:
            reasons.append(f"unclear words: {', '.join(low_confidence_words[:3])}")
        if missing_fields:
            reasons.append(f"missing: {', '.join(missing_fields)}")
        
        reason_text = "; ".join(reasons) if reasons else "low confidence"
        return f"Clarification needed ({reason_text}, score={final_score:.2f} < {threshold:.2f})"

    def _generate_question(
        self,
        intent: Intent,
        missing_fields: List[str],
        low_confidence_words: List[str],
    ) -> str:
        """Generate suggested clarification question."""
        if missing_fields:
            # Ask about missing fields
            if "items" in missing_fields:
                return "What would you like to order?"
            elif "delivery_time" in missing_fields:
                return "When would you like the delivery?"
            elif "order_id" in missing_fields:
                return "Which order number are you referring to?"
            else:
                return f"Could you please provide the {missing_fields[0]}?"
        
        elif low_confidence_words:
            # Ask for confirmation of unclear words
            return f"Did you say '{' '.join(low_confidence_words[:2])}'? Please confirm."
        
        else:
            # Generic clarification
            return "Could you please repeat that?"
