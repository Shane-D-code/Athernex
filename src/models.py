"""
Core data models for the voice pipeline.
Pydantic models used across all components for type safety and validation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class SupportedLanguage(str, Enum):
    HINDI = "hi"
    KANNADA = "kn"
    MARATHI = "mr"
    ENGLISH = "en"


class OrderIntent(str, Enum):
    PLACE_ORDER = "place_order"
    MODIFY_ORDER = "modify_order"
    CANCEL_ORDER = "cancel_order"
    CHECK_STATUS = "check_status"
    CONFIRM_ORDER = "confirm_order"
    REQUEST_INFO = "request_information"
    OOS_INTENT = "oos_intent"


class EmotionState(str, Enum):
    NEUTRAL = "neutral"
    HAPPY = "happy"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"
    CONFUSED = "confused"


class ClarificationReason(str, Enum):
    LOW_WORD_CONFIDENCE = "low_word_confidence"
    MISSING_INFORMATION = "missing_information"
    LOW_OVERALL_CONFIDENCE = "low_overall_confidence"


# ──────────────────────────────────────────────
# STT Models
# ──────────────────────────────────────────────

class WordResult(BaseModel):
    """Word-level transcription result with confidence and language."""
    word: str
    confidence: float = Field(ge=0.0, le=1.0)
    language: SupportedLanguage = SupportedLanguage.ENGLISH
    start_time: float = 0.0
    end_time: float = 0.0


class STTResult(BaseModel):
    """Output from the STT Engine."""
    transcription: str
    words: list[WordResult] = []
    utterance_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    detected_languages: list[SupportedLanguage] = []
    dominant_language: SupportedLanguage = SupportedLanguage.ENGLISH
    is_code_mixed: bool = False
    processing_time_ms: float = 0.0


# ──────────────────────────────────────────────
# LLM / Order Models
# ──────────────────────────────────────────────

class OrderItem(BaseModel):
    """Individual order item."""
    name: str
    quantity: int = Field(ge=1, default=1)
    variant: Optional[str] = None
    special_instructions: Optional[str] = None


class StructuredOrderData(BaseModel):
    """Structured order data extracted by LLM Processor."""
    intent: OrderIntent
    items: Optional[list[OrderItem]] = None
    delivery_time: Optional[str] = None  # ISO 8601 absolute timestamp
    customer_actions: Optional[list[str]] = None
    special_instructions: Optional[str] = None
    missing_fields: list[str] = []


class LLMResult(BaseModel):
    """Output from the LLM Processor."""
    intent: OrderIntent
    order_data: StructuredOrderData
    clarity_score: float = Field(ge=0.0, le=1.0, default=0.0)
    response_text: str = ""
    response_language: SupportedLanguage = SupportedLanguage.ENGLISH
    processing_time_ms: float = 0.0


# ──────────────────────────────────────────────
# Confidence Models
# ──────────────────────────────────────────────

class ConfidenceDecision(BaseModel):
    """Confidence analysis decision."""
    stt_confidence: float = Field(ge=0.0, le=1.0)
    llm_clarity: float = Field(ge=0.0, le=1.0)
    final_confidence: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(ge=0.0, le=1.0)
    decision: str  # "proceed" or "clarify"
    flagged_words: list[WordResult] = []
    missing_fields: list[str] = []
    clarification_reason: Optional[ClarificationReason] = None
    clarification_prompt: Optional[str] = None


# ──────────────────────────────────────────────
# Pipeline Models
# ──────────────────────────────────────────────

class PipelineResult(BaseModel):
    """End-to-end pipeline result."""
    stt_result: STTResult
    llm_result: LLMResult
    confidence_decision: ConfidenceDecision
    response_audio: Optional[bytes] = None
    response_text: str = ""
    response_language: SupportedLanguage = SupportedLanguage.ENGLISH
    total_processing_time_ms: float = 0.0
    cache_hit: bool = False
    fallback_used: bool = False

    model_config = {"arbitrary_types_allowed": True}


class PipelineMetrics(BaseModel):
    """Monitoring metrics for a single pipeline request."""
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stt_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    confidence_latency_ms: float = 0.0
    tts_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    stt_confidence: float = 0.0
    llm_clarity: float = 0.0
    final_confidence: float = 0.0
    intent: Optional[OrderIntent] = None
    detected_languages: list[SupportedLanguage] = []
    dominant_language: Optional[SupportedLanguage] = None
    clarification_triggered: bool = False
    cache_hit: bool = False
    fallback_used: bool = False
    error_occurred: bool = False
    error_details: Optional[str] = None
