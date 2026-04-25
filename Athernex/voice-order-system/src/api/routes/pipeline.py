import base64
import os
import uuid
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from typing import Optional

from api.dependencies import get_pipeline
from pipeline.voice_pipeline import VoicePipeline, PipelineResult
from monitoring.metrics_collector import get_metrics_collector
from emotion.detector import get_emotion_detector
from error_handler import get_error_handler, ErrorType

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request / Response models ─────────────────────────────────────────────────

class TranscribeResponse(BaseModel):
    transcription: str
    confidence: float
    dominant_language: str
    is_code_mixed: bool
    processing_time_ms: float


class ProcessResponse(BaseModel):
    session_id: str
    transcription: Optional[str]
    intent: Optional[str]
    response_text: str
    audio_response_b64: Optional[str] = Field(
        None, description="Base64-encoded WAV audio"
    )
    clarification_needed: bool
    clarification_question: Optional[str]
    language: str
    latency: dict
    error: Optional[str] = None
    emotion: Optional[str] = None
    emotion_confidence: Optional[float] = None
    escalate_to_human: bool = False


class SynthesizeRequest(BaseModel):
    text: str = Field(..., max_length=500)
    language: str = Field(default="en", pattern="^(hi|kn|mr|en)$")


class SynthesizeResponse(BaseModel):
    audio_b64: str = Field(..., description="Base64-encoded WAV audio")
    duration_hint: str


class ConfigResponse(BaseModel):
    stt_provider: str
    llm_provider: str
    tts_provider: str
    llm_model: str
    confidence_thresholds: dict
    context_max_turns: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    audio: UploadFile = File(..., description="Raw PCM_16 mono 16kHz audio"),
    pipeline: VoicePipeline = Depends(get_pipeline),
):
    """
    Transcribe audio to text using Whisper STT.
    Returns transcription with confidence and detected language.
    """
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    try:
        result = await pipeline.stt.transcribe(audio_bytes, 16000)
        return TranscribeResponse(
            transcription=result.text,
            confidence=result.confidence,
            dominant_language=result.language,
            is_code_mixed=False,  # Full detection happens in /process
            processing_time_ms=0.0,
        )
    except Exception as e:
        logger.error("Transcription failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")


@router.post("/process", response_model=ProcessResponse)
async def process_audio(
    audio: UploadFile = File(..., description="Raw PCM_16 mono 16kHz audio"),
    session_id: Optional[str] = Form(default=None),
    pipeline: VoicePipeline = Depends(get_pipeline),
):
    """
    Full pipeline: audio → transcription → intent → order processing → voice response.
    Maintains conversation context via session_id.
    """
    audio_bytes = await audio.read()
    if not audio_bytes:
        err = get_error_handler().get_error_response(
            session_id or "anon", ErrorType.EMPTY_AUDIO, "en"
        )
        raise HTTPException(status_code=400, detail=err["message"])

    sid = session_id or str(uuid.uuid4())

    # Emotion detection (Task 21.1) — parallel with pipeline, non-blocking
    emotion_result = get_emotion_detector().detect(audio_bytes)

    result: PipelineResult = await pipeline.process_audio(
        audio_bytes=audio_bytes,
        session_id=sid,
        sample_rate=16000,
    )

    # Record metrics (Task 18.2)
    intent = result.structured_data.intent.value if result.structured_data else None
    get_metrics_collector().record_request(
        session_id=sid,
        stt_ms=result.latency.stt_ms,
        llm_ms=result.latency.llm_ms,
        confidence_ms=result.latency.confidence_ms,
        tts_ms=result.latency.tts_ms,
        total_ms=result.latency.total_ms,
        language=result.language,
        intent=intent,
        clarification_needed=result.clarification_needed,
        error=result.error,
    )

    # Encode audio response as base64 for JSON transport
    audio_b64 = None
    if result.audio_response:
        audio_b64 = base64.b64encode(result.audio_response).decode("utf-8")

    return ProcessResponse(
        session_id=sid,
        transcription=result.transcription,
        intent=intent,
        response_text=result.response_text or "",
        audio_response_b64=audio_b64,
        clarification_needed=result.clarification_needed,
        clarification_question=result.clarification_question,
        language=result.language,
        latency={
            "stt_ms": round(result.latency.stt_ms, 1),
            "llm_ms": round(result.latency.llm_ms, 1),
            "confidence_ms": round(result.latency.confidence_ms, 1),
            "tts_ms": round(result.latency.tts_ms, 1),
            "total_ms": round(result.latency.total_ms, 1),
        },
        error=result.error,
        emotion=emotion_result.emotion.value,
        emotion_confidence=emotion_result.confidence,
        escalate_to_human=emotion_result.should_escalate,
    )


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize(
    request: SynthesizeRequest,
    pipeline: VoicePipeline = Depends(get_pipeline),
):
    """
    Text-to-speech synthesis in the specified Indian language.
    Returns base64-encoded audio.
    """
    try:
        tts_result = await pipeline.tts.synthesize(request.text, request.language)
        audio_b64 = base64.b64encode(tts_result.audio_bytes).decode("utf-8")
        return SynthesizeResponse(
            audio_b64=audio_b64,
            duration_hint=f"~{len(request.text) // 15}s",
        )
    except Exception as e:
        logger.error("Synthesis failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {e}")


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    """Return current runtime configuration (providers, models, thresholds)."""
    return ConfigResponse(
        stt_provider=os.getenv("STT_PROVIDER", "whisper"),
        llm_provider=os.getenv("LLM_PROVIDER", "ollama"),
        tts_provider=os.getenv("TTS_PROVIDER", "edge"),
        llm_model=os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M"),
        confidence_thresholds={
            "place_order": 0.85,
            "modify_order": 0.80,
            "cancel_order": 0.90,
            "confirm_order": 0.85,
            "check_status": 0.70,
            "request_information": 0.70,
        },
        context_max_turns=int(os.getenv("CONTEXT_MAX_TURNS", "10")),
    )
