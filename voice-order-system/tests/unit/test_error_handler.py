"""
Unit tests for error handler and graceful degradation — Task 19.3
"""
import pytest
from error_handler import ErrorHandler, ErrorType, get_error_message, rule_based_intent, DegradationLevel


def test_error_message_english():
    msg = get_error_message(ErrorType.STT_FAILURE, "en")
    assert "speak" in msg.lower() or "hear" in msg.lower()


def test_error_message_hindi():
    msg = get_error_message(ErrorType.STT_FAILURE, "hi")
    assert len(msg) > 0
    assert msg != get_error_message(ErrorType.STT_FAILURE, "en")


def test_error_message_kannada():
    msg = get_error_message(ErrorType.EMPTY_AUDIO, "kn")
    assert len(msg) > 0


def test_error_message_unknown_lang_falls_back():
    msg = get_error_message(ErrorType.UNKNOWN, "zu")  # Zulu — not supported
    assert msg == get_error_message(ErrorType.UNKNOWN, "en")


def test_retry_tracking():
    eh = ErrorHandler(max_retries=2)
    r1 = eh.get_error_response("s1", ErrorType.STT_FAILURE)
    assert r1["should_retry"] is True
    assert r1["should_escalate"] is False

    r2 = eh.get_error_response("s1", ErrorType.STT_FAILURE)
    assert r2["should_retry"] is True

    r3 = eh.get_error_response("s1", ErrorType.STT_FAILURE)
    # 3rd failure > max_retries=2 → escalate
    assert r3["should_escalate"] is True
    assert r3["should_retry"] is False


def test_reset_clears_retries():
    eh = ErrorHandler(max_retries=1)
    eh.get_error_response("s2", ErrorType.LLM_FAILURE)
    eh.get_error_response("s2", ErrorType.LLM_FAILURE)
    eh.reset_retries("s2")
    r = eh.get_error_response("s2", ErrorType.LLM_FAILURE)
    assert r["should_retry"] is True


# ── Rule-based intent fallback (Task 19.2) ─────────────────────────────────

def test_rule_based_cancel():
    r = rule_based_intent("cancel my order please")
    assert r["intent"] == "cancel_order"
    assert r["confidence"] >= 0.7


def test_rule_based_confirm():
    r = rule_based_intent("haan theek hai, confirm karo")
    assert r["intent"] == "confirm_order"


def test_rule_based_status():
    r = rule_based_intent("where is my order, how long?")
    assert r["intent"] == "check_status"


def test_rule_based_default_place_order():
    r = rule_based_intent("mujhe ek chai chahiye")  # no 'aur' to avoid modify keyword match
    assert r["intent"] == "place_order"
    assert r["mode"] == "rule_based_fallback"


def test_rule_based_modify():
    r = rule_based_intent("add more samosas please")
    assert r["intent"] == "modify_order"
