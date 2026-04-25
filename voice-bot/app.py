"""
VyapaarSetu AI - Complete Voice Order Confirmation System
Twilio + Sarvam AI (STT/TTS) + Local LLM (Ollama) + Dashboard + Android App

Architecture:
- Twilio handles telephony and call routing
- Sarvam AI provides Hindi STT and TTS
- Local Ollama LLM for conversation intelligence
- Flask serves webhooks and audio files
- SQLite database for order management
- Socket.IO for real-time dashboard updates
- REST API for dashboard and Android app
- Conversation history maintained per CallSid
"""

import os
import logging
import requests
import uuid
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from flask import Flask, request, send_from_directory, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.request_validator import RequestValidator
from twilio.rest import Client
from dotenv import load_dotenv
from functools import wraps

# Import language detector
from language_detector import detect_language, get_language_name, get_tts_language_code

# Import new modules
from models import db, Customer, Order, CallSession, AuditLog, log_audit
from extended_routes import register_extended_routes
from order_voice_flow import register_voice_routes

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vyapaarsetu.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
CORS(app, origins=["http://localhost:3000", "http://localhost:5173"])  # Allow dashboard
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Configuration from environment
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
SARVAM_API_KEY = os.getenv('SARVAM_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
LOCAL_LLM_URL = os.getenv('LOCAL_LLM_URL', 'http://localhost:11434/api/chat')
LOCAL_LLM_MODEL = os.getenv('LOCAL_LLM_MODEL', 'llama3.1:8b-instruct-q4_K_M')
BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'hi-IN')

# Validate API keys (Twilio is optional - using Android + web dashboard)
if not SARVAM_API_KEY:
    logger.warning("SARVAM_API_KEY not set - STT will not work")
if not ELEVENLABS_API_KEY:
    logger.warning("ELEVENLABS_API_KEY not set - using Sarvam TTS as fallback")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not set - will use local Ollama LLM as fallback")

# Initialize Twilio client only if credentials are present
twilio_client = None
validator = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and not TWILIO_ACCOUNT_SID.startswith('<'):
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        validator = RequestValidator(TWILIO_AUTH_TOKEN)
        logger.info("Twilio client initialized")
    except Exception as e:
        logger.warning(f"Twilio init failed (optional): {e}")
else:
    logger.info("Twilio not configured - running in Android/Web dashboard mode")

# Audio storage
AUDIO_DIR = Path(__file__).parent / 'static' / 'audio'
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Conversation history: {call_sid: [{"role": "user/assistant", "content": "..."}]}
conversation_history: Dict[str, List[Dict[str, str]]] = {}

# Sarvam AI endpoints
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"

# 11Labs TTS endpoint
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# 11Labs voice IDs (multilingual voices)
ELEVENLABS_VOICES = {
    'hi': 'pNInz6obpgDQGcFmaJgB',  # Adam - multilingual
    'en': 'EXAVITQu4vr4xnSDxMaL'   # Sarah - English
}

# Google Gemini API endpoint
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


# ============================================================================
# SECURITY: Twilio Request Validation
# ============================================================================

def validate_twilio_request(f):
    """Decorator to validate Twilio webhook requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip validation if Twilio not configured
        if validator is None:
            return f(*args, **kwargs)
        
        # Skip validation in development if BASE_URL is localhost
        if 'localhost' in BASE_URL or '127.0.0.1' in BASE_URL:
            return f(*args, **kwargs)
        
        signature = request.headers.get('X-Twilio-Signature', '')
        url = request.url
        post_vars = request.form.to_dict()
        
        if validator.validate(url, post_vars, signature):
            return f(*args, **kwargs)
        else:
            logger.error(f"Invalid Twilio signature for {url}")
            return "Forbidden", 403
    
    return decorated_function


# ============================================================================
# SARVAM AI: Speech-to-Text
# ============================================================================

def sarvam_stt(audio_url: str) -> Optional[str]:
    """
    Convert speech to text using Sarvam AI
    
    Args:
        audio_url: URL of the audio file (Twilio recording URL)
    
    Returns:
        Transcribed text or None if failed
    """
    try:
        logger.info(f"Downloading audio from: {audio_url}")
        
        # Download audio file from Twilio
        audio_response = requests.get(audio_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        audio_response.raise_for_status()
        audio_data = audio_response.content
        
        logger.info(f"Audio downloaded: {len(audio_data)} bytes")
        
        # Prepare multipart form data for Sarvam AI
        files = {
            'file': ('audio.wav', audio_data, 'audio/wav')
        }
        
        headers = {
            'api-subscription-key': SARVAM_API_KEY
        }
        
        data = {
            'language_code': LANGUAGE_CODE,
            'model': 'saaras:v1'
        }
        
        logger.info(f"Sending to Sarvam STT API with language: {LANGUAGE_CODE}")
        
        # Call Sarvam AI STT API
        response = requests.post(
            SARVAM_STT_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Extract transcript
        transcript = result.get('transcript', '')
        logger.info(f"STT Success: {transcript}")
        
        return transcript
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Sarvam STT API error: {e}")
        return None
    except Exception as e:
        logger.error(f"STT processing error: {e}")
        return None


# ============================================================================
# GOOGLE GEMINI: Conversation Intelligence (Primary LLM)
# ============================================================================

def call_gemini_llm(messages: List[Dict[str, str]], detected_language: str = 'en') -> Optional[str]:
    """
    Get response from Google Gemini API
    
    Args:
        messages: Conversation history in OpenAI format
        detected_language: Detected language code ('hi' or 'en')
    
    Returns:
        LLM response text or None if failed
    """
    try:
        if not GEMINI_API_KEY:
            logger.warning("Gemini API key not set, falling back to local LLM")
            return call_local_llm(messages, detected_language)
        
        # Language-specific system prompts
        if detected_language == 'hi':
            system_instruction = (
                "You are a helpful AI assistant for a voice call system in India. "
                "The user is speaking in Hindi. You MUST respond in Hindi (Devanagari script). "
                "Keep responses concise (2-3 sentences max) and natural for speech. "
                "Be friendly, helpful, and conversational. "
                "Always reply in Hindi when the user speaks Hindi."
            )
        else:
            system_instruction = (
                "You are a helpful AI assistant for a voice call system. "
                "The user is speaking in English. Respond in clear, simple English. "
                "Keep responses concise (2-3 sentences max) and natural for speech. "
                "Be friendly, helpful, and conversational."
            )
        
        # Build conversation text for Gemini
        conversation_parts = []
        
        # Add system instruction as first user message
        conversation_parts.append({
            "text": f"System: {system_instruction}"
        })
        
        # Add conversation history
        for msg in messages:
            if msg.get('role') == 'user':
                conversation_parts.append({
                    "text": f"User: {msg.get('content', '')}"
                })
            elif msg.get('role') == 'assistant':
                conversation_parts.append({
                    "text": f"Assistant: {msg.get('content', '')}"
                })
        
        # Add final prompt
        conversation_parts.append({
            "text": "Assistant:"
        })
        
        payload = {
            "contents": [{
                "parts": conversation_parts
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 150,
                "topP": 0.8,
                "topK": 40
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        
        logger.info(f"Calling Gemini API (Language: {detected_language})")
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Extract response text from Gemini format
        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                parts = candidate['content']['parts']
                if len(parts) > 0 and 'text' in parts[0]:
                    gemini_response = parts[0]['text'].strip()
                    
                    # Remove "Assistant:" prefix if present
                    if gemini_response.startswith("Assistant:"):
                        gemini_response = gemini_response[10:].strip()
                    
                    logger.info(f"Gemini Response ({detected_language}): {gemini_response}")
                    return gemini_response
        
        logger.error("No valid response from Gemini API")
        return call_local_llm(messages, detected_language)
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Gemini API error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response text: {e.response.text}")
        return call_local_llm(messages, detected_language)
    except Exception as e:
        logger.error(f"Gemini processing error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return call_local_llm(messages, detected_language)


# ============================================================================
# LOCAL LLM: Conversation Intelligence (Fallback)
# ============================================================================

def call_local_llm(messages: List[Dict[str, str]], detected_language: str = 'en') -> Optional[str]:
    """
    Get response from local Ollama LLM
    
    Args:
        messages: Conversation history in OpenAI format
        detected_language: Detected language code ('hi' or 'en')
    
    Returns:
        LLM response text or None if failed
    """
    try:
        # Language-specific system prompts
        if detected_language == 'hi':
            system_prompt = {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant for a voice call system in India. "
                    "The user is speaking in Hindi. You MUST respond in Hindi (Devanagari script). "
                    "Keep responses concise (2-3 sentences max) and natural for speech. "
                    "Be friendly, helpful, and conversational. "
                    "Always reply in Hindi when the user speaks Hindi."
                )
            }
        else:
            system_prompt = {
                "role": "system",
                "content": (
                    "You are a helpful AI assistant for a voice call system. "
                    "The user is speaking in English. Respond in clear, simple English. "
                    "Keep responses concise (2-3 sentences max) and natural for speech. "
                    "Be friendly, helpful, and conversational."
                )
            }
        
        # Create a fresh message list to avoid mutation issues
        llm_messages = []
        
        # Add system prompt
        llm_messages.append(system_prompt)
        
        # Add conversation history (skip system prompts from history)
        for msg in messages:
            if msg.get('role') != 'system':
                llm_messages.append(msg)
        
        payload = {
            "model": LOCAL_LLM_MODEL,
            "messages": llm_messages,
            "stream": False
        }
        
        logger.info(f"Calling local LLM at {LOCAL_LLM_URL} (Language: {detected_language})")
        
        response = requests.post(
            LOCAL_LLM_URL,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Extract response text
        llm_response = result.get('message', {}).get('content', '')
        logger.info(f"LLM Response ({detected_language}): {llm_response}")
        
        return llm_response
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Local LLM API error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response text: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"LLM processing error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


# ============================================================================
# SARVAM AI: Text-to-Speech
# ============================================================================

def sarvam_tts(text: str, call_sid: str, language_code: str = 'hi-IN') -> Optional[str]:
    """
    Convert text to speech using Sarvam AI
    
    Args:
        text: Text to convert to speech
        call_sid: Call SID for unique filename
        language_code: Language code (hi-IN or en-IN)
    
    Returns:
        URL of generated audio file or None if failed
    """
    try:
        headers = {
            'api-subscription-key': SARVAM_API_KEY,
            'Content-Type': 'application/json'
        }
        
        # Choose speaker based on language
        speaker = 'meera' if language_code == 'hi-IN' else 'arvind'
        
        payload = {
            'inputs': [text],
            'target_language_code': language_code,
            'speaker': speaker,
            'pitch': 0,
            'pace': 1.0,
            'loudness': 1.5,
            'speech_sample_rate': 8000,  # Optimized for telephony
            'enable_preprocessing': True,
            'model': 'bulbul:v1'
        }
        
        logger.info(f"Calling Sarvam TTS API ({language_code}) for text: {text[:50]}...")
        
        response = requests.post(
            SARVAM_TTS_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Extract base64 audio
        audio_base64 = result.get('audios', [None])[0]
        if not audio_base64:
            logger.error("No audio returned from Sarvam TTS")
            return None
        
        # Decode and save audio
        audio_data = base64.b64decode(audio_base64)
        
        # Generate unique filename
        filename = f"{call_sid}_{uuid.uuid4().hex[:8]}.wav"
        filepath = AUDIO_DIR / filename
        
        with open(filepath, 'wb') as f:
            f.write(audio_data)
        
        # Generate public URL
        audio_url = f"{BASE_URL}/static/audio/{filename}"
        logger.info(f"TTS audio saved ({language_code}): {audio_url}")
        
        return audio_url
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Sarvam TTS API error: {e}")
        return None
    except Exception as e:
        logger.error(f"TTS processing error: {e}")
        return None


# ============================================================================
# 11LABS: Text-to-Speech (Primary TTS)
# ============================================================================

def elevenlabs_tts(text: str, call_sid: str, language_code: str = 'hi-IN') -> Optional[str]:
    """
    Convert text to speech using 11Labs AI (multilingual support)
    
    Args:
        text: Text to convert to speech
        call_sid: Call SID for unique filename
        language_code: Language code (hi-IN or en-IN)
    
    Returns:
        URL of generated audio file or None if failed
    """
    try:
        if not ELEVENLABS_API_KEY:
            logger.warning("11Labs API key not set, falling back to Sarvam TTS")
            return sarvam_tts(text, call_sid, language_code)
        
        # Select voice based on language
        lang_code = 'hi' if language_code == 'hi-IN' else 'en'
        voice_id = ELEVENLABS_VOICES.get(lang_code, ELEVENLABS_VOICES['en'])
        
        headers = {
            'xi-api-key': ELEVENLABS_API_KEY,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'text': text,
            'model_id': 'eleven_multilingual_v2',
            'voice_settings': {
                'stability': 0.5,
                'similarity_boost': 0.75,
                'style': 0.5,
                'use_speaker_boost': True
            }
        }
        
        logger.info(f"Calling 11Labs TTS API ({language_code}) for text: {text[:50]}...")
        
        response = requests.post(
            f"{ELEVENLABS_TTS_URL}/{voice_id}",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        audio_data = response.content
        
        if not audio_data:
            logger.error("No audio returned from 11Labs TTS")
            return sarvam_tts(text, call_sid, language_code)
        
        # Generate unique filename
        filename = f"{call_sid}_{uuid.uuid4().hex[:8]}.mp3"
        filepath = AUDIO_DIR / filename
        
        with open(filepath, 'wb') as f:
            f.write(audio_data)
        
        # Generate public URL
        audio_url = f"{BASE_URL}/static/audio/{filename}"
        logger.info(f"11Labs TTS audio saved ({language_code}): {audio_url}")
        
        return audio_url
    
    except requests.exceptions.RequestException as e:
        logger.error(f"11Labs TTS API error: {e}, falling back to Sarvam")
        return sarvam_tts(text, call_sid, language_code)
    except Exception as e:
        logger.error(f"11Labs TTS processing error: {e}, falling back to Sarvam")
        return sarvam_tts(text, call_sid, language_code)


# ============================================================================
# TWILIO WEBHOOKS
# ============================================================================

@app.route('/voice', methods=['POST'])
@validate_twilio_request
def voice_webhook():
    """
    Initial webhook when call is received
    Greets user and starts recording
    """
    call_sid = request.form.get('CallSid')
    from_number = request.form.get('From')
    
    logger.info(f"Incoming call: {call_sid} from {from_number}")
    
    # Initialize conversation history
    conversation_history[call_sid] = []
    
    # Create TwiML response
    response = VoiceResponse()
    
    # Greet the user
    response.say(
        "Namaste! Main aapki AI assistant hoon. Aap mujhse kuch bhi pooch sakte hain.",
        language='hi-IN',
        voice='Polly.Aditi'
    )
    
    # Start recording user's speech
    response.record(
        action=f'/process?CallSid={call_sid}',
        method='POST',
        max_length=30,  # 30 seconds max
        play_beep=True,
        recording_status_callback=f'/recording-status?CallSid={call_sid}',
        recording_status_callback_method='POST'
    )
    
    logger.info(f"Sent greeting TwiML for {call_sid}")
    
    return str(response), 200, {'Content-Type': 'text/xml'}


@app.route('/process', methods=['POST'])
@validate_twilio_request
def process_webhook():
    """
    Process recorded audio:
    1. Download audio from Twilio
    2. STT via Sarvam AI → Get transcript
    3. Detect language from transcript
    4. LLM processing with language context
    5. TTS via Sarvam AI in detected language
    6. Play response back to caller
    """
    call_sid = request.args.get('CallSid') or request.form.get('CallSid')
    recording_url = request.form.get('RecordingUrl')
    
    logger.info(f"Processing recording for call {call_sid}: {recording_url}")
    
    response = VoiceResponse()
    
    # Step 1: Speech-to-Text
    transcript = sarvam_stt(recording_url)
    
    if not transcript:
        logger.error(f"STT failed for {call_sid}")
        response.say(
            "Maaf kijiye, main aapki baat samajh nahi paaya. Kripya dobara boliye.",
            language='hi-IN',
            voice='Polly.Aditi'
        )
        # Continue recording
        response.record(
            action=f'/process?CallSid={call_sid}',
            method='POST',
            max_length=30,
            play_beep=True
        )
        return str(response), 200, {'Content-Type': 'text/xml'}
    
    # Step 1.5: Detect language from transcript
    detected_lang = detect_language(transcript)
    lang_name = get_language_name(detected_lang)
    tts_lang_code = get_tts_language_code(detected_lang)
    
    logger.info(f"Detected language: {lang_name} ({detected_lang}) for text: {transcript}")
    
    # Add user message to history
    if call_sid not in conversation_history:
        conversation_history[call_sid] = []
    
    conversation_history[call_sid].append({
        "role": "user",
        "content": transcript
    })
    
    logger.info(f"User said ({lang_name}): {transcript}")
    
    # Step 2: Get LLM response with language context
    llm_response = call_gemini_llm(conversation_history[call_sid], detected_lang)
    
    if not llm_response:
        logger.error(f"LLM failed for {call_sid}")
        # Error message in detected language
        if detected_lang == 'hi':
            error_msg = "Mujhe sochne mein thodi dikkat ho rahi hai. Kripya dobara koshish karein."
        else:
            error_msg = "I'm having trouble thinking. Please try again."
        
        response.say(
            error_msg,
            language=tts_lang_code,
            voice='Polly.Aditi' if detected_lang == 'hi' else 'Polly.Joanna'
        )
        # Continue recording
        response.record(
            action=f'/process?CallSid={call_sid}',
            method='POST',
            max_length=30,
            play_beep=True
        )
        return str(response), 200, {'Content-Type': 'text/xml'}
    
    # Add assistant response to history
    conversation_history[call_sid].append({
        "role": "assistant",
        "content": llm_response
    })
    
    logger.info(f"Assistant response ({lang_name}): {llm_response}")
    
    # Step 3: Text-to-Speech using 11Labs (with Sarvam fallback)
    audio_url = elevenlabs_tts(llm_response, call_sid, tts_lang_code)
    
    if not audio_url:
        logger.error(f"TTS failed for {call_sid}")
        # Fallback to Twilio's built-in TTS
        response.say(
            llm_response,
            language=tts_lang_code,
            voice='Polly.Aditi' if detected_lang == 'hi' else 'Polly.Joanna'
        )
    else:
        # Play the generated audio
        response.play(audio_url)
    
    # Continue the conversation - record next input
    response.record(
        action=f'/process?CallSid={call_sid}',
        method='POST',
        max_length=30,
        play_beep=True,
        recording_status_callback=f'/recording-status?CallSid={call_sid}',
        recording_status_callback_method='POST'
    )
    
    return str(response), 200, {'Content-Type': 'text/xml'}


@app.route('/call-status', methods=['POST'])
@validate_twilio_request
def call_status_webhook():
    """
    Handle call status updates
    Clean up resources when call ends
    """
    call_sid = request.form.get('CallSid')
    call_status = request.form.get('CallStatus')
    
    logger.info(f"Call status update: {call_sid} - {call_status}")
    
    if call_status in ['completed', 'failed', 'busy', 'no-answer', 'canceled']:
        # Clean up conversation history
        if call_sid in conversation_history:
            logger.info(f"Cleaning up conversation history for {call_sid}")
            del conversation_history[call_sid]
        
        # Clean up audio files for this call
        try:
            for audio_file in AUDIO_DIR.glob(f"{call_sid}_*.wav"):
                audio_file.unlink()
                logger.info(f"Deleted audio file: {audio_file.name}")
        except Exception as e:
            logger.error(f"Error cleaning up audio files: {e}")
    
    return '', 200


@app.route('/recording-status', methods=['POST'])
@validate_twilio_request
def recording_status_webhook():
    """Handle recording status callbacks"""
    call_sid = request.args.get('CallSid') or request.form.get('CallSid')
    recording_status = request.form.get('RecordingStatus')
    
    logger.info(f"Recording status for {call_sid}: {recording_status}")
    
    return '', 200


# ============================================================================
# OUTBOUND CALLS
# ============================================================================

@app.route('/make-call', methods=['POST'])
def make_call():
    """
    Initiate an outbound call
    
    POST body:
    {
        "to_number": "+919876543210"
    }
    """
    try:
        data = request.get_json()
        to_number = data.get('to_number')
        
        if not to_number:
            return jsonify({"error": "to_number is required"}), 400
        
        logger.info(f"Initiating outbound call to {to_number}")
        
        # Create call
        call = twilio_client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=f"{BASE_URL}/voice",
            status_callback=f"{BASE_URL}/call-status",
            status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
            status_callback_method='POST'
        )
        
        logger.info(f"Outbound call created: {call.sid}")
        
        return jsonify({
            "success": True,
            "call_sid": call.sid,
            "to": to_number,
            "status": call.status
        }), 200
    
    except Exception as e:
        logger.error(f"Error making outbound call: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# STATIC FILE SERVING
# ============================================================================

# ============================================================================
# STATIC FILE SERVING
# ============================================================================

@app.route('/static/audio/<filename>')
def serve_audio(filename):
    """Serve generated audio files"""
    return send_from_directory(AUDIO_DIR, filename)
    """
    API endpoint for web testing
    Process audio file and return JSON response with audio
    """
    try:
        # Get audio file from request
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        session_id = request.form.get('session_id', f'web-{uuid.uuid4().hex[:8]}')
        
        # Save audio temporarily
        temp_audio_path = AUDIO_DIR / f"temp_{session_id}.wav"
        audio_file.save(temp_audio_path)
        
        logger.info(f"Web API: Processing audio for session {session_id}")
        
        # Read audio data
        with open(temp_audio_path, 'rb') as f:
            audio_data = f.read()
        
        # Create a temporary URL for STT (simulate Twilio recording URL)
        # For web testing, we'll pass the audio data directly
        
        # Step 1: STT
        # For web testing, we need to upload to a temporary location
        # Let's save it and create a local URL
        recording_url = f"{BASE_URL}/static/audio/temp_{session_id}.wav"
        
        transcript = sarvam_stt(recording_url)
        
        if not transcript:
            return jsonify({
                "success": False,
                "error": "Speech-to-text failed",
                "transcription": None,
                "response_text": "Sorry, I couldn't understand the audio. Please try again."
            }), 200
        
        # Step 1.5: Detect language
        detected_lang = detect_language(transcript)
        lang_name = get_language_name(detected_lang)
        tts_lang_code = get_tts_language_code(detected_lang)
        
        logger.info(f"Web API: Detected language: {lang_name} for text: {transcript}")
        
        # Initialize conversation history if needed
        if session_id not in conversation_history:
            conversation_history[session_id] = []
        
        # Add user message
        conversation_history[session_id].append({
            "role": "user",
            "content": transcript
        })
        
        # Step 2: LLM with language context
        llm_response = call_gemini_llm(conversation_history[session_id], detected_lang)
        
        if not llm_response:
            return jsonify({
                "success": False,
                "error": "LLM processing failed",
                "transcription": transcript,
                "detected_language": lang_name,
                "response_text": "I'm having trouble thinking right now. Please try again."
            }), 200
        
        # Add assistant response
        conversation_history[session_id].append({
            "role": "assistant",
            "content": llm_response
        })
        
        # Step 3: TTS using 11Labs (with Sarvam fallback)
        audio_url = elevenlabs_tts(llm_response, session_id, tts_lang_code)
        
        # Read the generated audio and convert to base64
        audio_base64 = None
        if audio_url:
            audio_filename = audio_url.split('/')[-1]
            audio_path = AUDIO_DIR / audio_filename
            if audio_path.exists():
                with open(audio_path, 'rb') as f:
                    audio_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # Clean up temp file
        if temp_audio_path.exists():
            temp_audio_path.unlink()
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "transcription": transcript,
            "detected_language": lang_name,
            "language_code": detected_lang,
            "response_text": llm_response,
            "audio_response_b64": audio_base64,
            "audio_url": audio_url
        }), 200
    
    except Exception as e:
        logger.error(f"Web API error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# HEALTH CHECK & INFO
# ============================================================================

@app.route('/')
def index():
    """API information"""
    return jsonify({
        "service": "AI Voice Call System",
        "status": "running",
        "endpoints": {
            "voice_webhook": "/voice",
            "process_webhook": "/process",
            "call_status": "/call-status",
            "make_call": "/make-call (POST)",
            "audio_files": "/static/audio/<filename>"
        },
        "configuration": {
            "language": LANGUAGE_CODE,
            "llm_model": LOCAL_LLM_MODEL,
            "base_url": BASE_URL
        },
        "active_calls": len(conversation_history)
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_conversations": len(conversation_history)
    })


# ============================================================================
# ANDROID APP API
# ============================================================================

@app.route('/api/v1/test', methods=['POST'])
def test_endpoint():
    """Test endpoint"""
    logger.info("TEST ENDPOINT CALLED")
    print("TEST ENDPOINT CALLED")
    return jsonify({"status": "ok"}), 200


@app.route('/api/v1/process', methods=['POST'])
def android_process():
    """
    Process text from Android app (speech already converted to text by Android)
    
    POST body:
    {
        "audio": "transcribed text from Android",
        "session_id": "unique session ID"
    }
    
    Returns:
    {
        "success": true,
        "session_id": "session_id",
        "transcription": "user text",
        "detected_language": "Hindi/English",
        "language_code": "hi/en",
        "response_text": "AI response",
        "audio_response_b64": "base64 encoded audio"
    }
    """
    try:
        print("=== Android API Called ===")
        data = request.get_json()
        print(f"Request data: {data}")
        transcript = data.get('audio', '')
        session_id = data.get('session_id', f'android-{uuid.uuid4().hex[:8]}')
        
        print(f"Transcript: {transcript}")
        print(f"Session ID: {session_id}")
        
        if not transcript:
            return jsonify({
                "success": False,
                "error": "No transcript provided"
            }), 400
        
        logger.info(f"Android API: Processing text for session {session_id}: {transcript}")
        
        # Step 1: Detect language
        detected_lang = detect_language(transcript)
        lang_name = get_language_name(detected_lang)
        tts_lang_code = get_tts_language_code(detected_lang)
        
        print(f"Detected language: {lang_name} ({detected_lang})")
        logger.info(f"Android API: Detected language: {lang_name} for text: {transcript}")
        
        # Initialize conversation history if needed
        if session_id not in conversation_history:
            conversation_history[session_id] = []
        
        # Add user message
        conversation_history[session_id].append({
            "role": "user",
            "content": transcript
        })
        
        print(f"Conversation history: {conversation_history[session_id]}")
        
        # Step 2: Get LLM response with language context
        print("Calling LLM...")
        llm_response = call_gemini_llm(conversation_history[session_id], detected_lang)
        print(f"LLM response: {llm_response}")
        
        if not llm_response:
            return jsonify({
                "success": False,
                "error": "LLM processing failed",
                "transcription": transcript,
                "detected_language": lang_name,
                "response_text": "I'm having trouble thinking right now. Please try again."
            }), 200
        
        # Add assistant response
        conversation_history[session_id].append({
            "role": "assistant",
            "content": llm_response
        })
        
        logger.info(f"Android API: LLM response ({lang_name}): {llm_response}")
        
        # Step 3: TTS using 11Labs (with Sarvam fallback)
        audio_url = elevenlabs_tts(llm_response, session_id, tts_lang_code)
        
        # Read the generated audio and convert to base64
        audio_base64 = None
        if audio_url:
            audio_filename = audio_url.split('/')[-1]
            audio_path = AUDIO_DIR / audio_filename
            if audio_path.exists():
                with open(audio_path, 'rb') as f:
                    audio_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "transcription": transcript,
            "detected_language": lang_name,
            "language_code": detected_lang,
            "response_text": llm_response,
            "audio_response_b64": audio_base64,
            "audio_url": audio_url
        }), 200
    
    except Exception as e:
        logger.error(f"Android API error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {e}")
    return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🚀 VyapaarSetu AI System Starting")
    logger.info("=" * 60)
    logger.info(f"📞 Twilio Phone: {TWILIO_PHONE_NUMBER}")
    logger.info(f"🌐 Base URL: {BASE_URL}")
    logger.info(f"🗣️  Language: {LANGUAGE_CODE}")
    logger.info(f"🤖 LLM Model: {LOCAL_LLM_MODEL}")
    logger.info(f"📁 Audio Directory: {AUDIO_DIR}")
    logger.info("=" * 60)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info("📊 Database tables created")
    
    # Register extended routes
    try:
        register_extended_routes(app, socketio, twilio_client)
        logger.info("🔗 Extended routes registered")
    except Exception as e:
        logger.error(f"Failed to register extended routes: {e}")
    
    try:
        register_voice_routes(app, socketio, sarvam_tts, validate_twilio_request)
        logger.info("📞 Voice routes registered")
    except Exception as e:
        logger.error(f"Failed to register voice routes: {e}")
    
    # Run Flask app with Socket.IO
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,  # Enable debug mode to see requests
        log_output=True
    )
