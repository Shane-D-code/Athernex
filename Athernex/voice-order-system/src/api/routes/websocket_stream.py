"""
WebSocket endpoint for real-time bidirectional audio streaming.

Protocol:
  Client → Server: JSON control messages + binary audio chunks
  Server → Client: JSON status messages + binary audio response chunks

Message format (client → server):
  {"type": "start", "session_id": "...", "sample_rate": 16000}
  {"type": "audio_chunk"}  followed by binary frame
  {"type": "end_of_speech"}
  {"type": "ping"}

Message format (server → client):
  {"type": "ready"}
  {"type": "partial_transcription", "text": "..."}
  {"type": "result", "transcription": "...", "response_text": "...", "intent": "..."}
  {"type": "audio_chunk"}  followed by binary audio frame
  {"type": "error", "message": "..."}
  {"type": "pong"}
"""

import asyncio
import base64
import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from api.dependencies import get_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/voice")
async def voice_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice streaming.
    Handles the full duplex audio session lifecycle.
    """
    await websocket.accept()
    session_id: Optional[str] = None
    audio_buffer = bytearray()
    sample_rate = 16000

    logger.info("WebSocket connection opened")

    try:
        pipeline = get_pipeline()
    except RuntimeError as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        await websocket.close()
        return

    try:
        while True:
            # Receive either text (control) or bytes (audio)
            try:
                message = await asyncio.wait_for(
                    websocket.receive(), timeout=30.0
                )
            except asyncio.TimeoutError:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json({"type": "ping"})
                continue

            # ── Binary frame: audio chunk ──────────────────────────────────
            if "bytes" in message and message["bytes"]:
                audio_buffer.extend(message["bytes"])
                continue

            # ── Text frame: control message ────────────────────────────────
            if "text" in message and message["text"]:
                try:
                    ctrl = json.loads(message["text"])
                except json.JSONDecodeError:
                    await websocket.send_json(
                        {"type": "error", "message": "Invalid JSON control message"}
                    )
                    continue

                msg_type = ctrl.get("type")

                if msg_type == "start":
                    session_id = ctrl.get("session_id") or str(uuid.uuid4())
                    sample_rate = ctrl.get("sample_rate", 16000)
                    audio_buffer = bytearray()
                    await websocket.send_json(
                        {"type": "ready", "session_id": session_id}
                    )
                    logger.info("WS session started: %s", session_id)

                elif msg_type == "end_of_speech":
                    if not audio_buffer:
                        await websocket.send_json(
                            {"type": "error", "message": "No audio received"}
                        )
                        continue

                    if not session_id:
                        session_id = str(uuid.uuid4())

                    # Send interim acknowledgement
                    await websocket.send_json({"type": "processing"})

                    try:
                        result = await pipeline.process_audio(
                            audio_bytes=bytes(audio_buffer),
                            session_id=session_id,
                            sample_rate=sample_rate,
                        )

                        # Send result metadata
                        await websocket.send_json({
                            "type": "result",
                            "session_id": session_id,
                            "transcription": result.transcription or "",
                            "response_text": result.response_text or "",
                            "intent": result.structured_data.intent.value if result.structured_data else None,
                            "clarification_needed": result.clarification_needed,
                            "clarification_question": result.clarification_question,
                            "language": result.language,
                            "latency": {
                                "stt_ms": round(result.latency.stt_ms, 1),
                                "llm_ms": round(result.latency.llm_ms, 1),
                                "total_ms": round(result.latency.total_ms, 1),
                            },
                            "error": result.error,
                        })

                        # Stream audio response as binary
                        if result.audio_response:
                            chunk_size = 4096
                            audio = result.audio_response
                            await websocket.send_json({"type": "audio_start"})
                            for i in range(0, len(audio), chunk_size):
                                await websocket.send_bytes(audio[i:i + chunk_size])
                            await websocket.send_json({"type": "audio_end"})

                    except Exception as e:
                        logger.error("WS pipeline error: %s", e, exc_info=True)
                        await websocket.send_json(
                            {"type": "error", "message": str(e)}
                        )

                    # Reset buffer for next utterance
                    audio_buffer = bytearray()

                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})

                elif msg_type == "reset":
                    audio_buffer = bytearray()
                    session_id = None
                    await websocket.send_json({"type": "reset_ok"})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: session=%s", session_id)
    except Exception as e:
        logger.error("WebSocket error: %s", e, exc_info=True)
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_json({"type": "error", "message": str(e)})
