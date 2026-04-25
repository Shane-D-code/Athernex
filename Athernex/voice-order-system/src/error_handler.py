"""
Error handling utilities — Task 19.1 / 19.2
Voice error response templates + graceful degradation helpers.
"""

import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class ErrorType(str, Enum):
    STT_FAILURE       = "stt_failure"
    LLM_FAILURE       = "llm_failure"
    TTS_FAILURE       = "tts_failure"
    NETWORK_ERROR     = "network_error"
    EMPTY_AUDIO       = "empty_audio"
    LOW_CONFIDENCE    = "low_confidence"
    UNKNOWN           = "unknown"


# ── Voice-friendly error message templates ─────────────────────────────────

_TEMPLATES: dict = {
    ErrorType.STT_FAILURE: {
        "en": "Sorry, I couldn't hear you clearly. Could you please speak again?",
        "hi": "Maafi kijiye, main aapki awaaz nahi sun paya. Kya aap phir se bol sakte hain?",
        "kn": "Kshamisi, nanu neevanu spashtavagi kelisikolla. Dayavittu matte heliri?",
        "mr": "Maaf kara, mala tumchi awaaz nit aikali nahi. Krupaya punha sanga?",
    },
    ErrorType.LLM_FAILURE: {
        "en": "I'm having trouble understanding your order. Please try again.",
        "hi": "Mujhe aapka order samajhne mein takleef ho rahi hai. Kripaya dobara koshish karein.",
        "kn": "Nanu neeva heli nimma order arthamakolluttilla. Dayavittu matte prayatisiri.",
        "mr": "Mala tumcha order samjayla tras hoto ahe. Krupaya parat praytna kara.",
    },
    ErrorType.TTS_FAILURE: {
        "en": "Your order has been received. Thank you!",
        "hi": "Aapka order mil gaya hai. Shukriya!",
        "kn": "Nimma order swikarisalaagide. Dhanyavaad!",
        "mr": "Tumcha order prapt zala ahe. Dhanyawad!",
    },
    ErrorType.EMPTY_AUDIO: {
        "en": "I didn't catch that. Please speak into the microphone.",
        "hi": "Kuch sunai nahi diya. Kripaya microphone mein bolein.",
        "kn": "Yenu kelisikollalilla. Dayavittu microphone nalli heliri.",
        "mr": "Kahi aikale nahi. Krupaya microphone madhe bola.",
    },
    ErrorType.LOW_CONFIDENCE: {
        "en": "I'm not quite sure about your order. Could you say that again?",
        "hi": "Mujhe aapke order ke baare mein pakka nahi hai. Kya phir se bol sakte hain?",
        "kn": "Nanu nimma order bagge khachitavilla. Dayavittu matte heliri?",
        "mr": "Mala tumcha order nakki nahi. Krupaya parat sanga ka?",
    },
    ErrorType.UNKNOWN: {
        "en": "Something went wrong. Please try again.",
        "hi": "Kuch galat ho gaya. Kripaya dobara koshish karein.",
        "kn": "Yenu thappu aayitu. Dayavittu matte prayatisiri.",
        "mr": "Kaytari chukle. Krupaya parat praytna kara.",
    },
}


def get_error_message(error_type: ErrorType, language: str = "en") -> str:
    """Return a voice-friendly error message in the user's language."""
    lang = language if language in ("en", "hi", "kn", "mr") else "en"
    template = _TEMPLATES.get(error_type, _TEMPLATES[ErrorType.UNKNOWN])
    return template.get(lang, template["en"])


# ── Graceful degradation ───────────────────────────────────────────────────

class DegradationLevel(str, Enum):
    FULL      = "full"       # All components working
    NO_TTS    = "no_tts"     # TTS down — return text only
    NO_LLM    = "no_llm"     # LLM down — rule-based intent detection
    MINIMAL   = "minimal"    # Only STT working — transcription only


def rule_based_intent(text: str) -> dict:
    """
    Fallback intent detection when LLM is unavailable.
    Covers the most common ordering patterns via keyword matching.
    Task 19.2 — rule-based degradation.
    """
    text_lower = text.lower()

    cancel_kw  = ["cancel", "ruk", "band", "nahi chahiye", "mat lao", "drop"]
    modify_kw  = ["change", "badlo", "update", "add more", "zyada", "thoda"]
    confirm_kw = ["yes", " haan", " ha ", "theek", "confirm", "proceed"]
    status_kw  = ["status", "kahan", "kitna", "where", "how long", "kitni der"]

    if any(k in text_lower for k in cancel_kw):
        intent, confidence = "cancel_order", 0.80
    elif any(k in text_lower for k in confirm_kw):
        intent, confidence = "confirm_order", 0.78
    elif any(k in text_lower for k in modify_kw):
        intent, confidence = "modify_order", 0.72
    elif any(k in text_lower for k in status_kw):
        intent, confidence = "check_status", 0.75
    else:
        intent, confidence = "place_order", 0.65

    return {
        "intent": intent,
        "confidence": confidence,
        "mode": "rule_based_fallback",
        "items": [],
    }


def get_tts_quality_fallback(primary: str) -> str:
    """Return next-lower TTS quality level for graceful degradation."""
    chain = ["edge_neural", "edge_standard", "pyttsx3"]
    try:
        idx = chain.index(primary)
        return chain[idx + 1] if idx + 1 < len(chain) else chain[-1]
    except ValueError:
        return "pyttsx3"


class ErrorHandler:
    """
    Central error handler — decides recovery strategy and generates
    voice error messages. Task 19.1 + 19.2.
    """

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries
        self._retry_counts: dict = {}

    def get_error_response(
        self,
        session_id: str,
        error_type: ErrorType,
        language: str = "en",
    ) -> dict:
        """Return error message text and whether to retry or escalate."""
        count = self._retry_counts.get(session_id, 0) + 1
        self._retry_counts[session_id] = count

        should_escalate = count > self.max_retries
        message = get_error_message(error_type, language)

        if should_escalate:
            message = (
                "I'm having repeated trouble. Let me connect you to a team member."
                if language == "en"
                else "Mujhe baar baar takleef ho rahi hai. Main aapko team member se connect karta hoon."
            )
            logger.warning("Escalating session %s after %d failures (%s)", session_id, count, error_type)

        return {
            "error_type": error_type.value,
            "message": message,
            "retry_count": count,
            "should_escalate": should_escalate,
            "should_retry": not should_escalate,
        }

    def reset_retries(self, session_id: str):
        self._retry_counts.pop(session_id, None)


# Singleton
_handler: Optional[ErrorHandler] = None

def get_error_handler() -> ErrorHandler:
    global _handler
    if _handler is None:
        _handler = ErrorHandler()
    return _handler
