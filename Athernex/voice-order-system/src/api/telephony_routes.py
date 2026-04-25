"""
Telephony API routes for phone call handling.

Provides Twilio webhook endpoints for incoming/outgoing calls.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Form, HTTPException, Response
from pydantic import BaseModel

from telephony.twilio_handler import get_twilio_handler
from orchestration.pipeline import VoicePipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/twilio", tags=["telephony"])

# Global pipeline instance (injected from main.py)
pipeline: Optional[VoicePipeline] = None


def set_pipeline(p: VoicePipeline):
    """Set the pipeline instance for telephony routes."""
    global pipeline
    pipeline = p


class OutboundCallRequest(BaseModel):
    """Request to make an outbound call."""
    phone_number: str
    greeting_text: str = "नमस्ते! आपका स्वागत है।"
    language: str = "hi"


@router.post("/incoming-call")
async def handle_incoming_call(
    From: str = Form(None),
    To: str = Form(None),
    CallSid: str = Form(None)
):
    """
    Handle incoming phone call.
    
    Twilio calls this webhook when someone calls your number.
    """
    logger.info("Incoming call from %s to %s (CallSid: %s)", From, To, CallSid)
    
    try:
        handler = get_twilio_handler()
        
        # Create greeting response
        greeting_messages = {
            "hi": "नमस्ते! आपका स्वागत है। आप क्या ऑर्डर करना चाहेंगे?",
            "en": "Hello! Welcome. What would you like to order?",
            "kn": "ನಮಸ್ಕಾರ! ಸ್ವಾಗತ. ನೀವು ಏನು ಆರ್ಡರ್ ಮಾಡಲು ಬಯಸುತ್ತೀರಿ?",
            "mr": "नमस्कार! स्वागत आहे. तुम्हाला काय ऑर्डर करायचे आहे?",
        }
        
        # Default to Hindi
        greeting = greeting_messages["hi"]
        
        twiml = handler.create_greeting_response(greeting, language="hi")
        
        return Response(content=twiml, media_type="text/xml")
        
    except Exception as e:
        logger.error("Error handling incoming call: %s", e)
        
        # Return error response
        handler = get_twilio_handler()
        twiml = handler.create_error_response(
            "क्षमा करें, कुछ गलत हो गया। कृपया दोबारा कॉल करें।",
            language="hi"
        )
        return Response(content=twiml, media_type="text/xml")


@router.post("/process-speech")
async def process_speech(
    SpeechResult: str = Form(None),
    CallSid: str = Form(None),
    Confidence: float = Form(0.0),
    From: str = Form(None)
):
    """
    Process transcribed speech from Twilio.
    
    Twilio calls this webhook after transcribing user's speech.
    """
    logger.info(
        "Processing speech from %s (CallSid: %s, Confidence: %.2f): %s",
        From, CallSid, Confidence, SpeechResult
    )
    
    try:
        handler = get_twilio_handler()
        
        # Check if speech was detected
        if not SpeechResult or SpeechResult.strip() == "":
            logger.warning("No speech detected for CallSid: %s", CallSid)
            twiml = handler.create_no_speech_response(language="hi")
            return Response(content=twiml, media_type="text/xml")
        
        # Check if pipeline is available
        if pipeline is None:
            logger.error("Pipeline not initialized")
            twiml = handler.create_error_response(
                "सिस्टम तैयार नहीं है। कृपया बाद में कॉल करें।",
                language="hi"
            )
            return Response(content=twiml, media_type="text/xml")
        
        # Process through pipeline (text mode)
        result = await pipeline.process_text(
            text=SpeechResult,
            session_id=CallSid,  # Use CallSid as session ID
            language=None  # Let pipeline detect language
        )
        
        if not result.success:
            logger.error("Pipeline processing failed: %s", result.error)
            twiml = handler.create_error_response(
                "क्षमा करें, मुझे समझ नहीं आया। कृपया दोबारा बोलें।",
                language="hi"
            )
            return Response(content=twiml, media_type="text/xml")
        
        # Determine if conversation should continue
        continue_conversation = True
        is_final = False
        
        # Check if order is complete
        if result.order_id and not result.clarification_needed:
            # Order confirmed, end call
            is_final = True
            continue_conversation = False
        
        # Generate TwiML response
        twiml = handler.create_speech_response(
            bot_text=result.bot_text,
            continue_conversation=continue_conversation,
            language=result.language,
            is_final=is_final
        )
        
        logger.info(
            "Response generated for CallSid %s: %s",
            CallSid, result.bot_text[:50]
        )
        
        return Response(content=twiml, media_type="text/xml")
        
    except Exception as e:
        logger.error("Error processing speech: %s", e, exc_info=True)
        
        handler = get_twilio_handler()
        twiml = handler.create_error_response(
            "क्षमा करें, कुछ गलत हो गया। कृपया दोबारा कॉल करें।",
            language="hi"
        )
        return Response(content=twiml, media_type="text/xml")


@router.post("/make-outbound-call")
async def make_outbound_call(request: OutboundCallRequest):
    """
    Make an outbound call to a customer.
    
    Use this to proactively call customers (e.g., order confirmation).
    """
    try:
        handler = get_twilio_handler()
        
        result = handler.make_outbound_call(
            to_number=request.phone_number,
            greeting_text=request.greeting_text,
            language=request.language
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error("Error making outbound call: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/call-status/{call_sid}")
async def get_call_status(call_sid: str):
    """Get status of a call."""
    try:
        handler = get_twilio_handler()
        status = handler.get_call_status(call_sid)
        
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        
        return status
        
    except Exception as e:
        logger.error("Error getting call status: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hangup/{call_sid}")
async def hangup_call(call_sid: str):
    """Hang up an active call."""
    try:
        handler = get_twilio_handler()
        success = handler.hangup_call(call_sid)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to hang up call")
        
        return {"success": True, "call_sid": call_sid}
        
    except Exception as e:
        logger.error("Error hanging up call: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_telephony():
    """Test endpoint to verify telephony routes are working."""
    try:
        handler = get_twilio_handler()
        return {
            "status": "ok",
            "phone_number": handler.phone_number,
            "base_url": handler.base_url
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "note": "Twilio handler not initialized. Set credentials in config."
        }
