"""
Property-based tests for clarification threshold consistency.

Tests Property 2: Clarification threshold consistency
Validates Requirements 3.1, 3.2, 3.7

These tests verify that:
1. Scores below threshold always trigger clarification
2. Scores above threshold never trigger clarification
3. Intent-specific thresholds are consistently applied
"""

import pytest
from hypothesis import given, strategies as st, assume
from typing import List

from confidence.analyzer import ConfidenceAnalyzer, ClarificationRecommendation
from llm.base import StructuredOrderData, Intent


# Strategy for generating valid confidence scores
confidence_score = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# Strategy for generating intents
intent_strategy = st.sampled_from(list(Intent))

# Strategy for generating missing fields
missing_fields = st.lists(
    st.sampled_from(["items", "delivery_time", "order_id", "special_instructions"]),
    min_size=0,
    max_size=4,
    unique=True
)

# Strategy for generating low-confidence words
low_confidence_words = st.lists(
    st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('L',))),
    min_size=0,
    max_size=10
)


@given(
    stt_confidence=confidence_score,
    llm_confidence=confidence_score,
    low_conf_words=low_confidence_words,
    missing=missing_fields,
    intent=intent_strategy
)
def test_scores_below_threshold_always_trigger_clarification(
    stt_confidence: float,
    llm_confidence: float,
    low_conf_words: List[str],
    missing: List[str],
    intent: Intent
):
    """
    Property 2a: Scores below threshold always trigger clarification.
    
    Validates:
    - Requirement 3.1: STT confidence below threshold triggers clarification
    - Requirement 3.2: LLM clarity below threshold triggers clarification
    - Requirement 3.7: Intent-specific thresholds are applied
    
    This is a critical safety property ensuring the system asks for
    clarification when confidence is insufficient.
    """
    # Arrange
    analyzer = ConfidenceAnalyzer()
    
    # Calculate what the final score will be
    base_score = (analyzer.stt_weight * stt_confidence + 
                  analyzer.llm_weight * llm_confidence)
    word_penalty = len(low_conf_words) * analyzer.low_confidence_word_penalty
    field_penalty = len(missing) * analyzer.missing_field_penalty
    final_score = max(0.0, base_score - word_penalty - field_penalty)
    
    # Get intent-specific threshold
    threshold = analyzer.intent_thresholds.get(intent.value, 0.75)
    
    # Only test cases where final score is below threshold
    assume(final_score < threshold)
    
    structured_data = StructuredOrderData(
        intent=intent,
        confidence=llm_confidence,
        missing_fields=missing
    )
    
    # Act
    result = analyzer.analyze(
        stt_confidence=stt_confidence,
        llm_response=structured_data,
        low_confidence_words=low_conf_words
    )
    
    # Assert - MUST trigger clarification
    assert result.should_clarify is True, \
        f"Score {final_score:.3f} below threshold {threshold:.3f} must trigger clarification"
    
    # Verify reason is provided
    assert result.reason is not None and len(result.reason) > 0, \
        "Clarification must include a reason"
    
    # Verify suggested question is provided
    assert result.suggested_question is not None and len(result.suggested_question) > 0, \
        "Clarification must include a suggested question"


@given(
    intent=intent_strategy,
    score_offset=st.floats(min_value=0.0, max_value=0.15, allow_nan=False, allow_infinity=False)
)
def test_scores_above_threshold_never_trigger_clarification(
    intent: Intent,
    score_offset: float
):
    """
    Property 2b: Scores above threshold never trigger clarification.
    
    Validates:
    - Requirement 3.1: STT confidence above threshold does not trigger clarification
    - Requirement 3.2: LLM clarity above threshold does not trigger clarification
    - Requirement 3.7: Intent-specific thresholds are applied
    
    This ensures the system doesn't unnecessarily ask for clarification
    when confidence is sufficient.
    """
    # Arrange
    analyzer = ConfidenceAnalyzer()
    
    # Get intent-specific threshold
    threshold = analyzer.intent_thresholds.get(intent.value, 0.75)
    
    # Create a score above the threshold (no penalties)
    target_score = min(1.0, threshold + score_offset)
    
    # Set stt = llm to achieve target score
    stt_confidence = target_score
    llm_confidence = target_score
    
    structured_data = StructuredOrderData(
        intent=intent,
        confidence=llm_confidence,
        missing_fields=[]  # No penalties
    )
    
    # Act
    result = analyzer.analyze(
        stt_confidence=stt_confidence,
        llm_response=structured_data,
        low_confidence_words=[]  # No penalties
    )
    
    # Calculate final score
    final_score = analyzer.stt_weight * stt_confidence + analyzer.llm_weight * llm_confidence
    
    # Assert - MUST NOT trigger clarification
    assert result.should_clarify is False, \
        f"Score {final_score:.3f} above threshold {threshold:.3f} must not trigger clarification"
    
    # Verify no suggested question when clarification not needed
    assert result.suggested_question is None, \
        "No suggested question should be provided when clarification not needed"


@given(intent=intent_strategy)
def test_threshold_boundary_below(intent: Intent):
    """
    Property 2c: Score exactly at threshold - epsilon triggers clarification.
    
    Tests the boundary condition just below the threshold.
    """
    # Arrange
    analyzer = ConfidenceAnalyzer()
    threshold = analyzer.intent_thresholds.get(intent.value, 0.75)
    
    # Create a score just below threshold
    epsilon = 0.001
    target_score = threshold - epsilon
    
    # We need to find stt and llm values that produce this target score
    # Using: target = 0.4 * stt + 0.6 * llm
    # Let's set stt = llm for simplicity: target = stt
    stt_confidence = max(0.0, min(1.0, target_score))
    llm_confidence = max(0.0, min(1.0, target_score))
    
    structured_data = StructuredOrderData(
        intent=intent,
        confidence=llm_confidence,
        missing_fields=[]
    )
    
    # Act
    result = analyzer.analyze(
        stt_confidence=stt_confidence,
        llm_response=structured_data,
        low_confidence_words=[]
    )
    
    # Calculate actual final score
    final_score = analyzer.stt_weight * stt_confidence + analyzer.llm_weight * llm_confidence
    
    # Assert
    if final_score < threshold:
        assert result.should_clarify is True, \
            f"Score {final_score:.3f} just below threshold {threshold:.3f} must trigger clarification"


@given(intent=intent_strategy)
def test_threshold_boundary_above(intent: Intent):
    """
    Property 2d: Score exactly at threshold triggers no clarification.
    
    Tests the boundary condition at or just above the threshold.
    """
    # Arrange
    analyzer = ConfidenceAnalyzer()
    threshold = analyzer.intent_thresholds.get(intent.value, 0.75)
    
    # Create a score at or just above threshold
    epsilon = 0.001
    target_score = threshold + epsilon
    
    # We need to find stt and llm values that produce this target score
    # Using: target = 0.4 * stt + 0.6 * llm
    # Let's set stt = llm for simplicity: target = stt
    stt_confidence = max(0.0, min(1.0, target_score))
    llm_confidence = max(0.0, min(1.0, target_score))
    
    structured_data = StructuredOrderData(
        intent=intent,
        confidence=llm_confidence,
        missing_fields=[]
    )
    
    # Act
    result = analyzer.analyze(
        stt_confidence=stt_confidence,
        llm_response=structured_data,
        low_confidence_words=[]
    )
    
    # Calculate actual final score
    final_score = analyzer.stt_weight * stt_confidence + analyzer.llm_weight * llm_confidence
    
    # Assert
    if final_score >= threshold:
        assert result.should_clarify is False, \
            f"Score {final_score:.3f} at/above threshold {threshold:.3f} must not trigger clarification"


@pytest.mark.parametrize("intent_name,expected_threshold", [
    ("place_order", 0.85),
    ("modify_order", 0.80),
    ("cancel_order", 0.90),
    ("confirm_order", 0.85),
    ("check_status", 0.70),
    ("request_information", 0.70),
])
def test_intent_specific_thresholds_are_applied(intent_name: str, expected_threshold: float):
    """
    Property 2e: Intent-specific thresholds are correctly applied.
    
    Validates Requirement 3.7: Intent-specific clarification thresholds.
    
    Different intents have different risk levels:
    - cancel_order: 0.90 (highest - irreversible action)
    - place_order: 0.85 (high - creates commitment)
    - confirm_order: 0.85 (high - finalizes order)
    - modify_order: 0.80 (medium - changes existing order)
    - check_status: 0.70 (low - read-only)
    - request_information: 0.70 (low - informational)
    """
    # Arrange
    analyzer = ConfidenceAnalyzer()
    
    # Verify threshold is configured correctly
    assert analyzer.intent_thresholds[intent_name] == expected_threshold, \
        f"Intent {intent_name} should have threshold {expected_threshold}"
    
    # Test with score just below threshold
    intent = Intent[intent_name.upper()]
    below_threshold = expected_threshold - 0.01
    
    structured_data = StructuredOrderData(
        intent=intent,
        confidence=below_threshold,
        missing_fields=[]
    )
    
    result_below = analyzer.analyze(
        stt_confidence=below_threshold,
        llm_response=structured_data,
        low_confidence_words=[]
    )
    
    # Should trigger clarification
    assert result_below.should_clarify is True, \
        f"Score below {intent_name} threshold should trigger clarification"
    
    # Test with score just above threshold
    above_threshold = min(1.0, expected_threshold + 0.01)
    
    structured_data_above = StructuredOrderData(
        intent=intent,
        confidence=above_threshold,
        missing_fields=[]
    )
    
    result_above = analyzer.analyze(
        stt_confidence=above_threshold,
        llm_response=structured_data_above,
        low_confidence_words=[]
    )
    
    # Should not trigger clarification
    assert result_above.should_clarify is False, \
        f"Score above {intent_name} threshold should not trigger clarification"


@given(
    stt_confidence=confidence_score,
    llm_confidence=confidence_score,
    intent=intent_strategy
)
def test_threshold_consistency_across_multiple_calls(
    stt_confidence: float,
    llm_confidence: float,
    intent: Intent
):
    """
    Property 2f: Threshold decision is consistent across multiple calls.
    
    Validates that the same inputs always produce the same clarification decision.
    This is an idempotence property for the threshold check.
    """
    # Arrange
    analyzer = ConfidenceAnalyzer()
    
    structured_data = StructuredOrderData(
        intent=intent,
        confidence=llm_confidence,
        missing_fields=[]
    )
    
    # Act - Call analyzer multiple times with same inputs
    result1 = analyzer.analyze(
        stt_confidence=stt_confidence,
        llm_response=structured_data,
        low_confidence_words=[]
    )
    
    result2 = analyzer.analyze(
        stt_confidence=stt_confidence,
        llm_response=structured_data,
        low_confidence_words=[]
    )
    
    result3 = analyzer.analyze(
        stt_confidence=stt_confidence,
        llm_response=structured_data,
        low_confidence_words=[]
    )
    
    # Assert - All results should be identical
    assert result1.should_clarify == result2.should_clarify == result3.should_clarify, \
        "Clarification decision must be consistent across multiple calls"
    
    assert result1.reason == result2.reason == result3.reason, \
        "Clarification reason must be consistent across multiple calls"


@given(intent=intent_strategy)
def test_zero_confidence_always_triggers_clarification(intent: Intent):
    """
    Property 2g: Zero confidence always triggers clarification regardless of threshold.
    
    This is a safety property ensuring the system never proceeds with
    zero confidence.
    """
    # Arrange
    analyzer = ConfidenceAnalyzer()
    
    structured_data = StructuredOrderData(
        intent=intent,
        confidence=0.0,
        missing_fields=[]
    )
    
    # Act
    result = analyzer.analyze(
        stt_confidence=0.0,
        llm_response=structured_data,
        low_confidence_words=[]
    )
    
    # Assert - Must always trigger clarification
    assert result.should_clarify is True, \
        "Zero confidence must always trigger clarification"


@given(intent=intent_strategy)
def test_perfect_confidence_never_triggers_clarification(intent: Intent):
    """
    Property 2h: Perfect confidence (1.0) never triggers clarification.
    
    Validates that maximum confidence with no penalties always passes
    the threshold check (assuming thresholds <= 1.0).
    """
    # Arrange
    analyzer = ConfidenceAnalyzer()
    threshold = analyzer.intent_thresholds.get(intent.value, 0.75)
    
    # Verify threshold is valid (should be <= 1.0)
    assume(threshold <= 1.0)
    
    structured_data = StructuredOrderData(
        intent=intent,
        confidence=1.0,
        missing_fields=[]
    )
    
    # Act
    result = analyzer.analyze(
        stt_confidence=1.0,
        llm_response=structured_data,
        low_confidence_words=[]
    )
    
    # Assert - Must not trigger clarification
    assert result.should_clarify is False, \
        "Perfect confidence (1.0) should never trigger clarification"


@given(intent=intent_strategy)
def test_threshold_comparison_is_strict_less_than(intent: Intent):
    """
    Property 2i: Threshold comparison uses strict less-than (<), not less-or-equal (<=).
    
    Validates that score exactly equal to threshold does NOT trigger clarification.
    This is important for boundary behavior.
    """
    # Arrange
    analyzer = ConfidenceAnalyzer()
    threshold = analyzer.intent_thresholds.get(intent.value, 0.75)
    
    # Create inputs that produce exactly the threshold score
    # Using: threshold = 0.4 * stt + 0.6 * llm
    # Set stt = llm = threshold for simplicity
    stt_confidence = threshold
    llm_confidence = threshold
    
    structured_data = StructuredOrderData(
        intent=intent,
        confidence=llm_confidence,
        missing_fields=[]
    )
    
    # Act
    result = analyzer.analyze(
        stt_confidence=stt_confidence,
        llm_response=structured_data,
        low_confidence_words=[]
    )
    
    # Calculate final score
    final_score = analyzer.stt_weight * stt_confidence + analyzer.llm_weight * llm_confidence
    
    # Assert - Score equal to threshold should NOT trigger clarification
    # (using < not <=)
    if abs(final_score - threshold) < 0.0001:
        assert result.should_clarify is False, \
            f"Score {final_score:.4f} equal to threshold {threshold:.4f} should not trigger clarification"


def test_all_intent_thresholds_are_valid():
    """
    Property 2j: All intent thresholds are in valid range [0.0, 1.0].
    
    Validates configuration sanity.
    """
    analyzer = ConfidenceAnalyzer()
    
    for intent_name, threshold in analyzer.intent_thresholds.items():
        assert 0.0 <= threshold <= 1.0, \
            f"Threshold for {intent_name} must be in [0.0, 1.0], got {threshold}"


def test_high_risk_intents_have_higher_thresholds():
    """
    Property 2k: High-risk intents have higher thresholds than low-risk intents.
    
    Validates that the threshold configuration reflects risk levels:
    - cancel_order (irreversible) > place_order (commitment) > modify_order > check_status (read-only)
    """
    analyzer = ConfidenceAnalyzer()
    
    # High-risk intents should have higher thresholds
    assert analyzer.intent_thresholds["cancel_order"] >= analyzer.intent_thresholds["place_order"], \
        "cancel_order should have threshold >= place_order"
    
    assert analyzer.intent_thresholds["place_order"] >= analyzer.intent_thresholds["modify_order"], \
        "place_order should have threshold >= modify_order"
    
    assert analyzer.intent_thresholds["modify_order"] >= analyzer.intent_thresholds["check_status"], \
        "modify_order should have threshold >= check_status"
    
    # Verify cancel_order has the highest threshold
    max_threshold = max(analyzer.intent_thresholds.values())
    assert analyzer.intent_thresholds["cancel_order"] == max_threshold, \
        "cancel_order should have the highest threshold (most risky action)"
