"""
FastAPI application for the Voice Order System.

Provides:
- REST API endpoints for text and audio processing
- WebSocket endpoint for real-time streaming
- Health checks and monitoring
- OpenAPI documentation

Task 22: API Layer implementation.
"""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel, Field

from config import settings
from utils.logging_config import setup_logging
from orchestration.orchestrator import ServiceOrchestrator
from orchestration.pipeline import VoicePipeline, PipelineResult
from orchestration.order_manager import OrderManager
from orchestration.cache import CacheManager
from dialogue.manager import DialogueManager
from stt.whisper_engine import WhisperSTTEngine
from stt.vosk_engine import VoskSTTEngine
from llm.ollama_processor import OllamaLLMProcessor
from llm.huggingface_processor import HuggingFaceLLMProcessor
from tts.edge_engine import EdgeTTSEngine
from tts.piper_engine import PiperTTSEngine

logger = logging.getLogger(__name__)

# Global pipeline instance
pipeline: Optional[VoicePipeline] = None


# Pydantic models for API
class TextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, description="User text input")
    session_id: Optional[str] = Field(None, description="Session ID for continuity")
    language: Optional[str] = Field("en", description="Language code (en, hi, kn, mr)")


class AudioRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Session ID for continuity")
    sample_rate: int = Field(16000, description="Audio sample rate in Hz")


class PipelineResponse(BaseModel):
    success: bool
    session_id: str
    user_text: Optional[str] = None
    bot_text: Optional[str] = None
    language: str = "en"
    intent: Optional[str] = None
    confidence: float = 0.0
    order_id: Optional[str] = None
    clarification_needed: bool = False
    processing_time_ms: float = 0.0
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    services: dict = {}
    system_stats: dict = {}


class OrderResponse(BaseModel):
    order_id: str
    status: str
    items: list = []
    delivery_time: Optional[str] = None
    total_items: int = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global pipeline
    
    # Startup
    setup_logging()
    logger.info("Starting Voice Order System API...")
    
    # Initialize services
    stt_engines = []
    try:
        stt_engines.append(WhisperSTTEngine(base_url=settings.whisper_endpoint))
    except Exception as e:
        logger.warning("Whisper not available: %s", e)
    
    try:
        stt_engines.append(VoskSTTEngine(language="hi"))
    except Exception as e:
        logger.warning("Vosk not available: %s", e)
    
    llm_processors = []
    try:
        llm_processors.append(OllamaLLMProcessor(
            base_url=settings.ollama_endpoint,
            model=settings.ollama_model,
        ))
    except Exception as e:
        logger.warning("Ollama not available: %s", e)
    
    if settings.hf_api_key:
        try:
            llm_processors.append(HuggingFaceLLMProcessor(api_key=settings.hf_api_key))
        except Exception as e:
            logger.warning("HuggingFace not available: %s", e)
    
    tts_engines = []
    try:
        tts_engines.append(EdgeTTSEngine())
    except Exception as e:
        logger.warning("Edge TTS not available: %s", e)
    
    try:
        tts_engines.append(PiperTTSEngine())
    except Exception as e:
        logger.warning("Piper TTS not available: %s", e)
    
    # Initialize orchestrator and pipeline
    if not stt_engines:
        logger.warning("No STT engines available")
    if not llm_processors:
        logger.warning("No LLM processors available")
    if not tts_engines:
        logger.warning("No TTS engines available")
    
    orchestrator = ServiceOrchestrator(
        stt_engines=stt_engines,
        llm_processors=llm_processors,
        tts_engines=tts_engines,
        rate_limits={
            "stt": settings.rate_limit_whisper,
            "llm": settings.rate_limit_ollama,
            "tts": settings.rate_limit_piper,
        }
    )
    
    dialogue_manager = DialogueManager()
    order_manager = OrderManager()
    cache_manager = CacheManager(
        llm_cache_size=settings.llm_cache_size,
        tts_cache_size=settings.tts_cache_size,
        cache_ttl_seconds=settings.cache_ttl_seconds,
    )
    
    pipeline = VoicePipeline(
        orchestrator=orchestrator,
        dialogue_manager=dialogue_manager,
        order_manager=order_manager,
        cache_manager=cache_manager,
    )
    
    logger.info("Voice Order System API ready")
    yield
    
    # Shutdown
    logger.info("Shutting down Voice Order System API...")
    if pipeline:
        await pipeline.orchestrator.close_all()


# Create FastAPI app
app = FastAPI(
    title="Multilingual Voice Order System",
    description="Self-hosted multilingual voice order system supporting Hindi, Kannada, Marathi, and English",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware for Android app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Android app origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Android integration routes
from api.android_routes import router as android_router
app.include_router(android_router)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health and service status."""
    if pipeline is None:
        return HealthResponse(status="initializing", services={}, system_stats={})
    
    services = await pipeline.orchestrator.health_check_all()
    stats = pipeline.get_system_stats()
    
    # Determine overall health
    all_healthy = all(
        svc.get("healthy", False)
        for category in services.values()
        for svc in category.values()
    )
    
    status = "healthy" if all_healthy else "degraded"
    
    return HealthResponse(
        status=status,
        services=services,
        system_stats=stats,
    )


@app.get("/stats")
async def get_stats():
    """Get system statistics."""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="System initializing")
    return pipeline.get_system_stats()


@app.post("/process/text", response_model=PipelineResponse)
async def process_text(request: TextRequest):
    """
    Process text input and return structured response.
    
    This endpoint is useful for testing and text-based interfaces.
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="System initializing")
    
    session_id = request.session_id or str(uuid.uuid4())[:8]
    
    result = await pipeline.process_text(
        text=request.text,
        session_id=session_id,
        language=request.language,
    )
    
    return PipelineResponse(
        success=result.success,
        session_id=result.session_id,
        user_text=result.user_text,
        bot_text=result.bot_text,
        language=result.language,
        intent=result.intent,
        confidence=result.confidence,
        order_id=result.order_id,
        clarification_needed=result.clarification_needed,
        processing_time_ms=result.processing_time_ms,
        error=result.error,
    )


@app.post("/process/audio")
async def process_audio(
    audio: bytes,
    session_id: Optional[str] = None,
    sample_rate: int = 16000,
    return_audio: bool = True,
):
    """
    Process audio input (PCM_16 mono) and return response.
    
    If return_audio=True, returns the bot's spoken response as audio.
    Otherwise returns JSON with text and metadata.
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="System initializing")
    
    session_id = session_id or str(uuid.uuid4())[:8]
    
    result = await pipeline.process_audio(
        audio_bytes=audio,
        session_id=session_id,
        sample_rate=sample_rate,
    )
    
    if not result.success:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": result.error,
                "session_id": result.session_id,
            }
        )
    
    if return_audio and result.audio_bytes:
        content_type = "audio/mpeg" if result.audio_format == "mp3" else "audio/wav"
        return Response(
            content=result.audio_bytes,
            media_type=content_type,
            headers={
                "X-Session-ID": result.session_id,
                "X-Intent": result.intent or "unknown",
                "X-Confidence": str(result.confidence),
                "X-Processing-Time-Ms": str(result.processing_time_ms),
            }
        )
    else:
        return PipelineResponse(
            success=result.success,
            session_id=result.session_id,
            user_text=result.user_text,
            bot_text=result.bot_text,
            language=result.language,
            intent=result.intent,
            confidence=result.confidence,
            order_id=result.order_id,
            clarification_needed=result.clarification_needed,
            processing_time_ms=result.processing_time_ms,
            error=result.error,
        )


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session information including dialogue state and orders."""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="System initializing")
    
    info = pipeline.get_session_info(session_id)
    if info is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return info


@app.get("/orders")
async def list_orders(session_id: Optional[str] = None):
    """List orders, optionally filtered by session."""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="System initializing")
    
    if session_id:
        orders = pipeline.orders.get_orders_by_session(session_id)
    else:
        orders = list(pipeline.orders.orders.values())
    
    return [o.to_dict() for o in orders]


@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    """Get specific order details."""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="System initializing")
    
    order = pipeline.orders.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return OrderResponse(
        order_id=order.order_id,
        status=order.status.value,
        items=[
            {"name": i.name, "quantity": i.quantity, "unit": i.unit}
            for i in order.items
        ],
        delivery_time=order.delivery_time,
        total_items=order.total_items,
    )


@app.post("/orders/{order_id}/cancel")
async def cancel_order(order_id: str):
    """Cancel an existing order."""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="System initializing")
    
    success = pipeline.orders.cancel_order(order_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel order")
    
    return {"success": True, "order_id": order_id, "status": "cancelled"}


@app.post("/orders/{order_id}/confirm")
async def confirm_order(order_id: str):
    """Confirm a pending order."""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="System initializing")
    
    order = pipeline.orders.confirm_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"success": True, "order_id": order_id, "status": order.status.value}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time bidirectional communication.
    
    Messages:
    - Client sends: {"type": "text", "text": "...", "session_id": "..."}
    - Server responds: {"type": "response", "text": "...", "audio": "base64...", ...}
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())[:8]
    
    try:
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "message": "Voice Order System connected",
        })
        
        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type", "text")
            
            if msg_type == "text":
                text = message.get("text", "")
                client_session = message.get("session_id", session_id)
                language = message.get("language", "en")
                
                if pipeline is None:
                    await websocket.send_json({
                        "type": "error",
                        "error": "System initializing",
                    })
                    continue
                
                result = await pipeline.process_text(
                    text=text,
                    session_id=client_session,
                    language=language,
                )
                
                response = {
                    "type": "response",
                    "session_id": result.session_id,
                    "success": result.success,
                    "user_text": result.user_text,
                    "bot_text": result.bot_text,
                    "language": result.language,
                    "intent": result.intent,
                    "confidence": result.confidence,
                    "order_id": result.order_id,
                    "clarification_needed": result.clarification_needed,
                    "processing_time_ms": result.processing_time_ms,
                }
                
                # Include audio if available
                if result.audio_bytes:
                    import base64
                    response["audio"] = base64.b64encode(result.audio_bytes).decode("utf-8")
                    response["audio_format"] = result.audio_format
                
                await websocket.send_json(response)
            
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "error": f"Unknown message type: {msg_type}",
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: %s", session_id)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        try:
            await websocket.send_json({"type": "error", "error": str(e)})
        except:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

